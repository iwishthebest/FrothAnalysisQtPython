"""
历史数据页面 - 数据查询和趋势分析
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QGroupBox, QLabel, QTableWidget,
                               QTableWidgetItem, QHeaderView, QComboBox,
                               QDateEdit, QPushButton, QSplitter)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor
from PySide6.QtCharts import (QChart, QChartView, QLineSeries,
                              QValueAxis, QDateTimeAxis)
import random
from datetime import datetime, timedelta


class HistoryPage(QWidget):
    """历史数据页面 - 数据查询和趋势分析"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_sample_data()

    def _setup_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("历史数据分析")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 查询条件区域
        layout.addWidget(self._create_query_panel())

        # 分割器：图表和表格
        splitter = QSplitter(Qt.Orientation.Vertical)

        # 图表区域
        chart_widget = self._create_chart_widget()
        splitter.addWidget(chart_widget)

        # 数据表格区域
        table_widget = self._create_data_table()
        splitter.addWidget(table_widget)

        # 设置分割比例
        splitter.setSizes([400, 200])
        layout.addWidget(splitter)

    def _create_query_panel(self):
        """创建查询条件面板"""
        group = QGroupBox("数据查询条件")
        layout = QHBoxLayout(group)

        # 数据类型选择
        layout.addWidget(QLabel("数据类型:"))
        self.data_type_combo = QComboBox()
        self.data_type_combo.addItems([
            "铅品位数据", "回收率数据", "加药量数据",
            "液位数据", "泡沫厚度数据", "所有数据"
        ])
        self.data_type_combo.currentTextChanged.connect(self._on_data_type_changed)
        layout.addWidget(self.data_type_combo)

        # 时间范围选择
        layout.addWidget(QLabel("时间范围:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.start_date.setCalendarPopup(True)
        layout.addWidget(self.start_date)

        layout.addWidget(QLabel("至"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        layout.addWidget(self.end_date)

        # 查询按钮
        query_btn = QPushButton("查询数据")
        query_btn.clicked.connect(self._on_query_data)
        layout.addWidget(query_btn)

        # 导出按钮
        export_btn = QPushButton("导出数据")
        export_btn.clicked.connect(self._on_export_data)
        layout.addWidget(export_btn)

        layout.addStretch()

        return group

    def _create_chart_widget(self):
        """创建图表显示组件"""
        group = QGroupBox("趋势图表")
        layout = QVBoxLayout(group)

        # 创建图表
        self.chart = QChart()
        self.chart.setTitle("历史数据趋势")
        self.chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        # 创建坐标轴
        self.axis_x = QDateTimeAxis()
        self.axis_x.setFormat("MM-dd hh:mm")
        self.axis_x.setTitleText("时间")
        self.chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)

        self.axis_y = QValueAxis()
        self.axis_y.setTitleText("数值")
        self.chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)

        # 图表视图
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        layout.addWidget(self.chart_view)

        return group

    def _create_data_table(self):
        """创建数据表格"""
        group = QGroupBox("详细数据")
        layout = QVBoxLayout(group)

        self.data_table = QTableWidget()
        self.data_table.setColumnCount(5)
        self.data_table.setHorizontalHeaderLabels([
            "时间", "铅品位(%)", "回收率(%)", "液位(m)", "加药量(ml/min)"
        ])

        # 设置表格属性
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.data_table)

        return group

    def _load_sample_data(self):
        """加载示例数据"""
        self.history_data = []
        base_time = datetime.now() - timedelta(days=7)

        # 生成7天的示例数据（每小时一个点）
        for i in range(24 * 7):
            timestamp = base_time + timedelta(hours=i)

            # 模拟数据波动
            grade = 85 + random.uniform(-3, 3)  # 铅品位 82-88%
            recovery = 92 + random.uniform(-2, 2)  # 回收率 90-94%
            level = 1.2 + random.uniform(-0.1, 0.1)  # 液位 1.1-1.3m
            dosing = 50 + random.uniform(-5, 5)  # 加药量 45-55ml/min

            self.history_data.append({
                'timestamp': timestamp,
                'grade': grade,
                'recovery': recovery,
                'level': level,
                'dosing': dosing
            })

        self._update_chart()
        self._update_data_table()

    def _update_chart(self):
        """更新图表显示"""
        # 清空现有系列
        self.chart.removeAllSeries()

        # 创建数据系列
        grade_series = QLineSeries()
        grade_series.setName("铅品位")

        recovery_series = QLineSeries()
        recovery_series.setName("回收率")

        # 添加数据点
        for data in self.history_data:
            timestamp = data['timestamp']
            grade_series.append(timestamp.toMSecsSinceEpoch(), data['grade'])
            recovery_series.append(timestamp.toMSecsSinceEpoch(), data['recovery'])

        # 添加到图表
        self.chart.addSeries(grade_series)
        self.chart.addSeries(recovery_series)

        # 绑定坐标轴
        grade_series.attachAxis(self.axis_x)
        grade_series.attachAxis(self.axis_y)
        recovery_series.attachAxis(self.axis_x)
        recovery_series.attachAxis(self.axis_y)

        # 调整Y轴范围
        min_value = min([data['grade'] for data in self.history_data] +
                        [data['recovery'] for data in self.history_data]) - 2
        max_value = max([data['grade'] for data in self.history_data] +
                        [data['recovery'] for data in self.history_data]) + 2
        self.axis_y.setRange(min_value, max_value)

        # 调整X轴范围
        if self.history_data:
            start_time = self.history_data[0]['timestamp']
            end_time = self.history_data[-1]['timestamp']
            self.axis_x.setRange(start_time, end_time)

    def _update_data_table(self):
        """更新数据表格"""
        # 显示最近24小时的数据
        recent_data = self.history_data[-24:]
        self.data_table.setRowCount(len(recent_data))

        for row, data in enumerate(recent_data):
            self.data_table.setItem(row, 0,
                                    QTableWidgetItem(data['timestamp'].strftime("%m-%d %H:%M")))
            self.data_table.setItem(row, 1,
                                    QTableWidgetItem(f"{data['grade']:.2f}"))
            self.data_table.setItem(row, 2,
                                    QTableWidgetItem(f"{data['recovery']:.2f}"))
            self.data_table.setItem(row, 3,
                                    QTableWidgetItem(f"{data['level']:.2f}"))
            self.data_table.setItem(row, 4,
                                    QTableWidgetItem(f"{data['dosing']:.1f}"))

    def _on_data_type_changed(self, data_type):
        """数据类型改变事件"""
        self._update_chart()

    def _on_query_data(self):
        """查询数据事件"""
        # 这里可以实现实际的数据查询逻辑
        self._update_chart()
        self._update_data_table()

    def _on_export_data(self):
        """导出数据事件"""
        # 这里可以实现数据导出逻辑
        print("数据导出功能待实现")

    def refresh_data(self):
        """刷新数据"""
        self._load_sample_data()
