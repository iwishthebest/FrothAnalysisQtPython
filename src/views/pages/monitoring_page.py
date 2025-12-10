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
    """监测页面 - 显示实时数据和图表 (OPC 信号驱动版)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.opc_service = get_opc_service()

        # 初始化数据缓冲区 (用于图表)
        self.max_points = 100
        self.time_data = np.arange(self.max_points)
        self.grade_data = np.zeros(self.max_points)
        self.recovery_data = np.zeros(self.max_points)

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
        layout.addWidget(charts_widget, stretch=1)  # 图表占据主要空间

        # 3. 数据表格区域 (Bottom)
        table_widget = self.create_table_section()
        layout.addWidget(table_widget, stretch=0)  # 表格高度自适应

    def create_metrics_section(self):
        """创建关键指标区域"""
        widget = QGroupBox("关键指标 (KPI)")
        layout = QHBoxLayout(widget)

        # 创建并保存 Label 引用，以便后续更新数值
        self.lbl_pb_grade = self.create_metric_label()
        self.lbl_zn_grade = self.create_metric_label()
        self.lbl_recovery = self.create_metric_label()

        # [修改点 1] 使用 addWidget 而不是 addLayout，因为 create_metric_item 现在返回的是 Widget
        layout.addWidget(self.create_metric_item("铅品位 (Pb)", self.lbl_pb_grade, "%"))
        layout.addWidget(self.create_metric_item("锌品位 (Zn)", self.lbl_zn_grade, "%"))
        layout.addWidget(self.create_metric_item("回收率", self.lbl_recovery, "%"))

        return widget

    def create_metric_label(self):
        """创建显示数值的 Label"""
        label = QLabel("--")
        label.setStyleSheet("color: #2980b9; font-size: 24px; font-weight: bold;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    def create_metric_item(self, title, value_label, unit):
        """创建单个指标组件布局"""
        v_layout = QVBoxLayout()
        v_layout.setContentsMargins(10, 10, 10, 10)  # 稍微加点内边距

        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("color: #7f8c8d; font-size: 14px;")

        unit_lbl = QLabel(unit)
        unit_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        unit_lbl.setStyleSheet("color: #95a5a6; font-size: 12px;")

        v_layout.addWidget(title_lbl)
        v_layout.addWidget(value_label)
        v_layout.addWidget(unit_lbl)

        # 给个背景框看起来更像个卡片
        container = QWidget()
        container.setLayout(v_layout)
        container.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #bdc3c7;")

        # [修改点 2] 返回 container (Widget) 而不是 v_layout
        # 这样 container 就会被父级引用，不会被垃圾回收，layout 也自然安全了
        return container

    def create_charts_section(self):
        """创建图表区域"""
        widget = QGroupBox("实时趋势")
        layout = QHBoxLayout(widget)

        # 设置 pyqtgraph 样式
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        # 1. 品位趋势图
        self.grade_plot = pg.PlotWidget(title="铅品位趋势")
        self.grade_plot.showGrid(x=True, y=True)
        self.grade_plot.setLabel('left', '品位', units='%')
        self.grade_curve = self.grade_plot.plot(pen=pg.mkPen(color='#3498db', width=2))
        layout.addWidget(self.grade_plot)

        # 2. 回收率趋势图
        self.recovery_plot = pg.PlotWidget(title="回收率趋势")
        self.recovery_plot.showGrid(x=True, y=True)
        self.recovery_plot.setLabel('left', '回收率', units='%')
        self.recovery_curve = self.recovery_plot.plot(pen=pg.mkPen(color='#2ecc71', width=2))
        layout.addWidget(self.recovery_plot)

        return widget

    def create_table_section(self):
        """创建数据表格区域"""
        widget = QGroupBox("历史数据 (最新10条)")
        layout = QVBoxLayout(widget)

        self.data_table = QTableWidget()
        self.data_table.setColumnCount(4)
        self.data_table.setHorizontalHeaderLabels(["时间", "铅品位 (%)", "锌品位 (%)", "回收率 (%)"])

        # 表格样式
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # 禁止编辑
        self.data_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout.addWidget(self.data_table)
        return widget

    def setup_charts(self):
        """初始化图表数据 (已在__init__中完成数组初始化)"""
        pass

    def setup_connections(self):
        """连接 OPC 服务的信号"""
        worker = self.opc_service.get_worker()
        if worker:
            # 连接数据更新信号 -> handle_data_updated
            worker.data_updated.connect(self.handle_data_updated)
            # 连接状态信号 (可选)
            # worker.status_changed.connect(self.handle_status_changed)

    @Slot(dict)
    def handle_data_updated(self, data: dict):
        """处理 OPC 数据更新信号"""

        # 1. 解析数据 (使用安全获取方法)
        def get_val(tag, default=0.0):
            if tag in data and data[tag].get('value') is not None:
                return float(data[tag]['value'])
            return default

        # 根据你的 tagList.csv 或实际标签名修改这里
        val_pb = get_val("KYFX.grade_Pb", 0.0)
        val_zn = get_val("KYFX.grade_Zn", 0.0)
        val_rec = get_val("KYFX.recovery_rate", 0.0)
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 2. 更新 KPI 数值显示
        self.lbl_pb_grade.setText(f"{val_pb:.2f}")
        self.lbl_zn_grade.setText(f"{val_zn:.2f}")
        self.lbl_recovery.setText(f"{val_rec:.2f}")

        # 3. 更新图表 (滚动数组)
        # 移除第一个，追加最新的
        self.grade_data = np.roll(self.grade_data, -1)
        self.grade_data[-1] = val_pb

        self.recovery_data = np.roll(self.recovery_data, -1)
        self.recovery_data[-1] = val_rec

        # 刷新曲线
        self.grade_curve.setData(self.grade_data)
        self.recovery_curve.setData(self.recovery_data)

        # 4. 更新表格 (插入新行到顶部)
        self.data_table.insertRow(0)
        self.data_table.setItem(0, 0, QTableWidgetItem(timestamp))
        self.data_table.setItem(0, 1, QTableWidgetItem(f"{val_pb:.2f}"))
        self.data_table.setItem(0, 2, QTableWidgetItem(f"{val_zn:.2f}"))
        self.data_table.setItem(0, 3, QTableWidgetItem(f"{val_rec:.2f}"))

        # 限制表格行数 (例如只保留最新 50 条)
        if self.data_table.rowCount() > 50:
            self.data_table.removeRow(50)

    # 兼容旧代码接口
    def update_data(self):
        pass