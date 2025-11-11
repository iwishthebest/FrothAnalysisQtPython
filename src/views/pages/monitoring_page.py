from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QGroupBox, QLabel, QTableWidget,
                               QTableWidgetItem)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import pyqtgraph as pg
import numpy as np


class MonitoringPage(QWidget):
    """监测页面 - 显示实时数据和图表"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_charts()

    def setup_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 关键指标区域
        metrics_widget = self.create_metrics_section()
        layout.addWidget(metrics_widget)

        # 图表区域
        charts_widget = self.create_charts_section()
        layout.addWidget(charts_widget)

        # 数据表格区域
        table_widget = self.create_table_section()
        layout.addWidget(table_widget)

    def create_metrics_section(self):
        """创建关键指标区域"""
        widget = QGroupBox("关键指标")
        layout = QHBoxLayout(widget)

        # 铅品位
        grade_widget = self.create_metric_item("铅品位", "85.2%", "#e74c3c")
        layout.addWidget(grade_widget)

        # 回收率
        recovery_widget = self.create_metric_item("回收率", "92.1%", "#2ecc71")
        layout.addWidget(recovery_widget)

        # 处理量
        throughput_widget = self.create_metric_item("处理量", "150 t/h", "#3498db")
        layout.addWidget(throughput_widget)

        # 泡沫厚度
        foam_widget = self.create_metric_item("泡沫厚度", "25 cm", "#9b59b6")
        layout.addWidget(foam_widget)

        return widget

    @staticmethod
    def create_metric_item(self, title, value, color):
        """创建单个指标项"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 标题
        title_label = QLabel(title)
        title_label.setFont(QFont("Microsoft YaHei", 10))
        title_label.setStyleSheet(f"color: {color};")

        # 数值
        value_label = QLabel(value)
        value_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {color};")

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        return widget

    def create_charts_section(self):
        """创建图表区域"""
        widget = QGroupBox("实时趋势")
        layout = QVBoxLayout(widget)

        # 创建图表控件
        self.graphics_widget = pg.GraphicsLayoutWidget()

        # 品位趋势图
        self.grade_plot = self.graphics_widget.ci.addPlot(title="铅品位趋势")
        self.grade_curve = self.grade_plot.plot(pen='r')

        # 回收率趋势图
        self.recovery_plot = self.graphics_widget.ci.addPlot(title="回收率趋势")
        self.recovery_curve = self.recovery_plot.plot(pen='g')

        layout.addWidget(self.graphics_widget)

        return widget

    def create_table_section(self):
        """创建数据表格区域"""
        widget = QGroupBox("实时数据")
        layout = QVBoxLayout(widget)

        self.data_table = QTableWidget(6, 3)
        self.data_table.setHorizontalHeaderLabels(["参数", "数值", "单位"])
        self.data_table.setVerticalHeaderLabels([
            "泡沫厚度", "气泡尺寸", "流速", "纹理", "稳定性", "浓度"
        ])

        # 设置表格属性
        self.data_table.setAlternatingRowColors(True)
        self.data_table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(self.data_table)
        return widget

    def setup_charts(self):
        """设置图表数据"""
        # 初始化数据
        self.time_data = np.arange(100)
        self.grade_data = np.random.normal(85, 2, 100)
        self.recovery_data = np.random.normal(92, 1, 100)

    def update_data(self):
        """更新数据"""
        # 模拟数据更新
        new_grade = np.random.normal(85, 2)
        new_recovery = np.random.normal(92, 1)

        # 更新图表数据
        self.grade_data = np.roll(self.grade_data, -1)
        self.grade_data[-1] = new_grade
        self.grade_curve.setData(self.time_data, self.grade_data)

        self.recovery_data = np.roll(self.recovery_data, -1)
        self.recovery_data[-1] = new_recovery
        self.recovery_curve.setData(self.time_data, self.recovery_data)

        # 更新表格数据
        self.update_table_data()

    def update_table_data(self):
        """更新表格数据"""
        data = [
            np.random.uniform(20, 30),  # 泡沫厚度
            np.random.uniform(5, 15),  # 气泡尺寸
            np.random.uniform(10, 20),  # 流速
            np.random.uniform(0, 1),  # 纹理
            np.random.uniform(80, 95),  # 稳定性
            np.random.uniform(50, 150)  # 浓度
        ]

        for row, value in enumerate(data):
            self.data_table.setItem(row, 1, QTableWidgetItem(f"{value:.2f}"))
