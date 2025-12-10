from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QGroupBox, QLabel, QTableWidget,
                               QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont
import pyqtgraph as pg
import numpy as np
from datetime import datetime

# 引入 OPC 服务
from src.services.opc_service import get_opc_service


class MonitoringPage(QWidget):
    """监测页面 - 显示实时数据和图表 (KPI: 原矿/精矿/回收率)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.opc_service = get_opc_service()

        # 初始化数据缓冲区 (用于图表)
        self.max_points = 100
        self.time_data = np.arange(self.max_points)
        # 曲线1: 原矿品位
        self.feed_grade_data = np.zeros(self.max_points)
        # 曲线2: 精矿品位
        self.conc_grade_data = np.zeros(self.max_points)

        self.setup_ui()
        self.setup_charts()
        self.setup_connections()

    def setup_ui(self):
        """初始化用户界面布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

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
        widget = QGroupBox("生产关键指标 (Key Performance Indicators)")
        layout = QHBoxLayout(widget)

        # 创建并保存 Label 引用
        self.lbl_feed_grade = self.create_metric_label()
        self.lbl_conc_grade = self.create_metric_label()
        self.lbl_recovery = self.create_metric_label()

        # [修改] 使用新的指标名称
        layout.addWidget(self.create_metric_item("原矿铅品位 (Feed)", self.lbl_feed_grade, "%"))
        layout.addWidget(self.create_metric_item("高铅精矿品位 (Conc)", self.lbl_conc_grade, "%"))
        layout.addWidget(self.create_metric_item("铅回收率 (Recovery)", self.lbl_recovery, "%"))

        return widget

    def create_metric_label(self):
        label = QLabel("--")
        label.setStyleSheet("color: #2980b9; font-size: 24px; font-weight: bold;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    def create_metric_item(self, title, value_label, unit):
        v_layout = QVBoxLayout()
        v_layout.setContentsMargins(10, 10, 10, 10)

        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("color: #7f8c8d; font-size: 14px;")

        unit_lbl = QLabel(unit)
        unit_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        unit_lbl.setStyleSheet("color: #95a5a6; font-size: 12px;")

        v_layout.addWidget(title_lbl)
        v_layout.addWidget(value_label)
        v_layout.addWidget(unit_lbl)

        container = QWidget()
        container.setLayout(v_layout)
        container.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #bdc3c7;")
        return container

    def create_charts_section(self):
        """创建图表区域"""
        widget = QGroupBox("实时品位趋势")
        layout = QHBoxLayout(widget)

        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        # 1. 原矿品位趋势
        self.feed_plot = pg.PlotWidget(title="原矿铅品位趋势 (Feed)")
        self.feed_plot.showGrid(x=True, y=True)
        self.feed_plot.setLabel('left', '品位', units='%')
        self.feed_curve = self.feed_plot.plot(pen=pg.mkPen(color='#3498db', width=2))
        layout.addWidget(self.feed_plot)

        # 2. 精矿品位趋势
        self.conc_plot = pg.PlotWidget(title="高铅精矿品位趋势 (Conc)")
        self.conc_plot.showGrid(x=True, y=True)
        self.conc_plot.setLabel('left', '品位', units='%')
        self.conc_curve = self.conc_plot.plot(pen=pg.mkPen(color='#e74c3c', width=2))
        layout.addWidget(self.conc_plot)

        return widget

    def create_table_section(self):
        """创建数据表格区域"""
        widget = QGroupBox("历史数据 (最新10条)")
        layout = QVBoxLayout(widget)

        self.data_table = QTableWidget()
        self.data_table.setColumnCount(4)
        # [修改] 表头更新
        self.data_table.setHorizontalHeaderLabels(["时间", "原矿品位(%)", "精矿品位(%)", "回收率(%)"])

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

        # === [核心修改] 获取指定的三个指标 ===
        # 1. 原矿铅品位 (Run of Mine)
        val_feed = get_val("KYFX.kyfx_yk_grade_Pb", 0.0)

        # 2. 高铅精矿铅品位 (High Lead Concentrate)
        val_conc = get_val("KYFX.kyfx_gqxk_grade_Pb", 0.0)

        # 3. 尾矿铅品位 (Tailings - 用于计算回收率)
        val_tail = get_val("KYFX.kyfx_qw_grade_Pb", 0.0)

        # === [核心修改] 计算回收率 ===
        # 公式: R = [c * (f - t)] / [f * (c - t)] * 100
        val_rec = 0.0
        try:
            if val_feed > val_tail and val_conc > val_tail and val_feed > 0 and (val_conc - val_tail) != 0:
                numerator = val_conc * (val_feed - val_tail)
                denominator = val_feed * (val_conc - val_tail)
                val_rec = (numerator / denominator) * 100
                # 限制在 0-100 之间
                val_rec = max(0.0, min(100.0, val_rec))
        except Exception:
            val_rec = 0.0

        timestamp = datetime.now().strftime("%H:%M:%S")

        # 2. 更新 KPI 数值显示
        self.lbl_feed_grade.setText(f"{val_feed:.2f}")
        self.lbl_conc_grade.setText(f"{val_conc:.2f}")
        self.lbl_recovery.setText(f"{val_rec:.2f}")

        # 3. 更新图表
        self.feed_grade_data = np.roll(self.feed_grade_data, -1)
        self.feed_grade_data[-1] = val_feed

        self.conc_grade_data = np.roll(self.conc_grade_data, -1)
        self.conc_grade_data[-1] = val_conc

        self.feed_curve.setData(self.feed_grade_data)
        self.conc_curve.setData(self.conc_grade_data)

        # 4. 更新表格
        self.data_table.insertRow(0)
        self.data_table.setItem(0, 0, QTableWidgetItem(timestamp))
        self.data_table.setItem(0, 1, QTableWidgetItem(f"{val_feed:.2f}"))
        self.data_table.setItem(0, 2, QTableWidgetItem(f"{val_conc:.2f}"))
        self.data_table.setItem(0, 3, QTableWidgetItem(f"{val_rec:.2f}"))

        if self.data_table.rowCount() > 50:
            self.data_table.removeRow(50)

    def update_data(self):
        pass