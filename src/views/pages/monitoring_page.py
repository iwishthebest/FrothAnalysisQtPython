from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QGroupBox, QLabel, QTableWidget,
                               QTableWidgetItem, QHeaderView, QFrame)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont
import pyqtgraph as pg
import numpy as np
from datetime import datetime

# 引入 OPC 服务
from src.services.opc_service import get_opc_service


class StatCard(QFrame):
    """
    [新增] 美化的数据展示卡片组件
    包含：标题、数值、单位、状态指示灯
    """

    def __init__(self, title, unit="", color="#3498db", icon="📊"):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)

        # 使用 QSS 设置圆角、背景和边框
        self.setStyleSheet(f"""
            StatCard {{
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }}
            StatCard:hover {{
                border: 1px solid {color};
                background-color: #f8f9fa;
                margin-top: -2px; /* 悬停上浮效果 */
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(5)

        # 1. 头部：标题和图标
        header_layout = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #7f8c8d; font-size: 14px; font-weight: bold;")

        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"color: {color}; font-size: 18px;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(icon_label)
        layout.addLayout(header_layout)

        # 2. 中部：数值
        self.value_label = QLabel("--")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        # 使用对应的主题色显示数值
        self.value_label.setStyleSheet(f"color: #2c3e50; font-size: 28px; font-weight: bold; font-family: Arial;")
        layout.addWidget(self.value_label)

        # 3. 底部：单位
        unit_label = QLabel(unit)
        unit_label.setStyleSheet("color: #95a5a6; font-size: 12px;")
        layout.addWidget(unit_label)

    def set_value(self, value):
        self.value_label.setText(str(value))


class MonitoringPage(QWidget):
    """监测页面 - 显示实时数据和图表 (KPI: 原矿/精矿/回收率)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.opc_service = get_opc_service()

        # 状态记录
        self.last_chart_update = datetime.min
        self.chart_update_interval = 600  # 10分钟

        # 数据缓冲
        self.max_points = 100
        self.feed_grade_data = np.zeros(self.max_points)
        self.conc_grade_data = np.zeros(self.max_points)

        self.setup_ui()
        self.setup_charts()
        self.setup_connections()

    def setup_ui(self):
        # 整体背景色
        self.setStyleSheet("background-color: #f5f6fa;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)

        # 1. 关键指标区域 (Top)
        metrics_widget = self.create_metrics_section()
        layout.addWidget(metrics_widget)

        # 2. 图表区域 (Middle)
        charts_widget = self.create_charts_section()
        layout.addWidget(charts_widget, stretch=1)

        # 3. 数据表格区域 (Bottom)
        table_widget = self.create_table_section()
        layout.addWidget(table_widget, stretch=0)

    def create_metrics_section(self):
        """创建关键指标区域"""
        # 不使用 GroupBox，直接用 Layout 布局卡片，更简洁
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # 创建三个漂亮的卡片
        self.card_feed = StatCard("原矿铅品位 (Feed)", "%", "#3498db", "⛏️")
        self.card_conc = StatCard("高铅精矿品位 (Conc)", "%", "#e74c3c", "💎")
        self.card_rec = StatCard("铅回收率 (Recovery)", "%", "#2ecc71", "📈")

        layout.addWidget(self.card_feed)
        layout.addWidget(self.card_conc)
        layout.addWidget(self.card_rec)

        return container

    def create_charts_section(self):
        """创建图表区域"""
        widget = QGroupBox("实时品位趋势 (每10分钟更新)")
        widget.setStyleSheet("""
            QGroupBox { 
                background-color: white; 
                border: 1px solid #e0e0e0; 
                border-radius: 8px; 
                margin-top: 10px; 
                padding-top: 15px;
                font-weight: bold;
                color: #555;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 5px; }
        """)
        layout = QHBoxLayout(widget)

        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        self.feed_plot = pg.PlotWidget()
        self.feed_plot.setTitle("原矿铅品位趋势", color="#3498db", size="10pt")
        self.feed_plot.showGrid(x=True, y=True, alpha=0.3)
        self.feed_plot.setLabel('left', '品位', units='%')
        self.feed_curve = self.feed_plot.plot(pen=pg.mkPen(color='#3498db', width=2))

        self.conc_plot = pg.PlotWidget()
        self.conc_plot.setTitle("高铅精矿品位趋势", color="#e74c3c", size="10pt")
        self.conc_plot.showGrid(x=True, y=True, alpha=0.3)
        self.conc_plot.setLabel('left', '品位', units='%')
        self.conc_curve = self.conc_plot.plot(pen=pg.mkPen(color='#e74c3c', width=2))

        layout.addWidget(self.feed_plot)
        layout.addWidget(self.conc_plot)

        return widget

    def create_table_section(self):
        """创建数据表格区域"""
        widget = QGroupBox("历史数据 (最新10条)")
        widget.setStyleSheet("""
            QGroupBox { 
                background-color: white; 
                border: 1px solid #e0e0e0; 
                border-radius: 8px; 
                margin-top: 10px; 
                padding-top: 15px;
                font-weight: bold;
                color: #555;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 5px; }
        """)
        layout = QVBoxLayout(widget)

        self.data_table = QTableWidget()
        self.data_table.setColumnCount(4)
        self.data_table.setHorizontalHeaderLabels(["时间", "原矿品位(%)", "精矿品位(%)", "回收率(%)"])

        # 美化表格
        self.data_table.setStyleSheet("""
            QTableWidget { border: none; gridline-color: #f0f0f0; }
            QHeaderView::section { background-color: #f8f9fa; border: none; border-bottom: 1px solid #e0e0e0; padding: 5px; font-weight: bold; }
        """)

        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.data_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout.addWidget(self.data_table)
        return widget

    def setup_charts(self):
        pass

    def setup_connections(self):
        worker = self.opc_service.get_worker()
        if worker:
            worker.data_updated.connect(self.handle_data_updated)

    @Slot(dict)
    def handle_data_updated(self, data: dict):
        """处理 OPC 数据更新信号"""

        def get_val(tag, default=0.0):
            if tag in data and data[tag].get('value') is not None:
                return float(data[tag]['value'])
            return default

        val_feed = get_val("KYFX.kyfx_yk_grade_Pb", 0.0)
        val_conc = get_val("KYFX.kyfx_gqxk_grade_Pb", 0.0)
        val_tail = get_val("KYFX.kyfx_qw_grade_Pb", 0.0)

        # 计算回收率
        val_rec = 0.0
        try:
            if val_feed > val_tail and val_conc > val_tail and val_feed > 0 and (val_conc - val_tail) != 0:
                numerator = val_conc * (val_feed - val_tail)
                denominator = val_feed * (val_conc - val_tail)
                val_rec = (numerator / denominator) * 100
                val_rec = max(0.0, min(100.0, val_rec))
        except Exception:
            val_rec = 0.0

        # [修改] 使用 Card 的 set_value 方法更新
        self.card_feed.set_value(f"{val_feed:.2f}")
        self.card_conc.set_value(f"{val_conc:.2f}")
        self.card_rec.set_value(f"{val_rec:.2f}")

        # 图表和表格更新逻辑 (每10分钟)
        now = datetime.now()
        if (now - self.last_chart_update).total_seconds() >= self.chart_update_interval:
            self.last_chart_update = now
            timestamp_str = now.strftime("%H:%M:%S")

            self.feed_grade_data = np.roll(self.feed_grade_data, -1)
            self.feed_grade_data[-1] = val_feed

            self.conc_grade_data = np.roll(self.conc_grade_data, -1)
            self.conc_grade_data[-1] = val_conc

            self.feed_curve.setData(self.feed_grade_data)
            self.conc_curve.setData(self.conc_grade_data)

            self.data_table.insertRow(0)
            self.data_table.setItem(0, 0, QTableWidgetItem(timestamp_str))
            self.data_table.setItem(0, 1, QTableWidgetItem(f"{val_feed:.2f}"))
            self.data_table.setItem(0, 2, QTableWidgetItem(f"{val_conc:.2f}"))
            self.data_table.setItem(0, 3, QTableWidgetItem(f"{val_rec:.2f}"))

            if self.data_table.rowCount() > 50:
                self.data_table.removeRow(50)

    def update_data(self):
        pass