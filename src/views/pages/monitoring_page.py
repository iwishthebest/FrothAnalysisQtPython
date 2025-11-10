"""
监测页面 - 实时数据显示和监控
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QGroupBox, QLabel, QTableWidget,
                               QTableWidgetItem, QHeaderView, QProgressBar)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
from datetime import datetime
import random


class MonitoringPage(QWidget):
    """监测页面 - 显示实时数据和系统状态"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_timer = QTimer()
        self._setup_ui()
        self._setup_data_simulation()

    def _setup_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("实时监测面板")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 第一行：关键指标
        key_metrics_layout = QHBoxLayout()
        key_metrics_layout.addWidget(self._create_metric_widget("铅品位", "85.2%", "#e74c3c", "当前铅精矿品位"))
        key_metrics_layout.addWidget(self._create_metric_widget("回收率", "92.1%", "#2ecc71", "铅回收率"))
        key_metrics_layout.addWidget(self._create_metric_widget("处理量", "150 t/h", "#3498db", "矿石处理量"))
        key_metrics_layout.addWidget(self._create_metric_widget("泡沫厚度", "25 cm", "#9b59b6", "平均泡沫层厚度"))
        layout.addLayout(key_metrics_layout)

        # 第二行：浮选槽状态表格
        layout.addWidget(self._create_tank_status_table())

        # 第三行：趋势指示器
        layout.addWidget(self._create_trend_indicators())

    def _create_metric_widget(self, title, value, color, description):
        """创建指标显示组件"""
        group = QGroupBox(title)
        group.setStyleSheet(f"QGroupBox {{ border: 2px solid {color}; border-radius: 8px; }}")
        layout = QVBoxLayout(group)

        # 数值显示
        value_label = QLabel(value)
        value_label.setFont(QFont("Microsoft YaHei", 24, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)

        # 描述
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        layout.addWidget(desc_label)

        return group

    def _create_tank_status_table(self):
        """创建浮选槽状态表格"""
        group = QGroupBox("浮选槽实时状态")
        layout = QVBoxLayout(group)

        self.status_table = QTableWidget()
        self.status_table.setColumnCount(6)
        self.status_table.setHorizontalHeaderLabels([
            "槽位", "液位(m)", "加药量(ml/min)", "泡沫质量", "状态", "更新时间"
        ])

        # 设置表格属性
        self.status_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.status_table.setAlternatingRowColors(True)
        self.status_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # 初始化数据
        self._update_status_table()
        layout.addWidget(self.status_table)

        return group

    def _create_trend_indicators(self):
        """创建趋势指示器"""
        group = QGroupBox("关键参数趋势")
        layout = QHBoxLayout(group)

        # 品位趋势
        grade_widget = self._create_trend_item("铅品位趋势", 85.2, 80, 90, "#e74c3c")
        layout.addWidget(grade_widget)

        # 回收率趋势
        recovery_widget = self._create_trend_item("回收率趋势", 92.1, 85, 95, "#2ecc71")
        layout.addWidget(recovery_widget)

        # 泡沫稳定性
        foam_widget = self._create_trend_item("泡沫稳定性", 88.5, 80, 95, "#3498db")
        layout.addWidget(foam_widget)

        return group

    def _create_trend_item(self, title, current, min_val, max_val, color):
        """创建趋势显示项"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 标题
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        layout.addWidget(title_label)

        # 进度条
        progress_bar = QProgressBar()
        progress_bar.setRange(min_val, max_val)
        progress_bar.setValue(int(current))
        progress_bar.setFormat(f"{current:.1f}%")
        progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {color};
                border-radius: 5px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {color};
            }}
        """)
        layout.addWidget(progress_bar)

        # 趋势指示
        trend = random.choice([-1, 0, 1])
        trend_text = "↗ 上升" if trend > 0 else "↘ 下降" if trend < 0 else "→ 平稳"
        trend_label = QLabel(trend_text)
        trend_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        trend_color = "#2ecc71" if trend > 0 else "#e74c3c" if trend < 0 else "#f39c12"
        trend_label.setStyleSheet(f"color: {trend_color}; font-weight: bold;")
        layout.addWidget(trend_label)

        return widget

    def _setup_data_simulation(self):
        """设置数据模拟"""
        self.data_timer.timeout.connect(self._update_real_time_data)
        self.data_timer.start(2000)  # 2秒更新一次

    def _update_real_time_data(self):
        """更新实时数据"""
        self._update_status_table()

    def _update_status_table(self):
        """更新状态表格数据"""
        tank_data = [
            ("铅快粗槽", 1.25, 52.3, "良好", "运行正常"),
            ("铅精一槽", 1.35, 48.7, "优良", "运行正常"),
            ("铅精二槽", 1.42, 45.1, "良好", "运行正常"),
            ("铅精三槽", 1.51, 38.9, "一般", "运行正常")
        ]

        self.status_table.setRowCount(len(tank_data))

        for row, (name, level, dosing, quality, status) in enumerate(tank_data):
            # 添加少量随机波动
            level += random.uniform(-0.05, 0.05)
            dosing += random.uniform(-2.0, 2.0)

            self.status_table.setItem(row, 0, QTableWidgetItem(name))
            self.status_table.setItem(row, 1, QTableWidgetItem(f"{level:.2f}"))
            self.status_table.setItem(row, 2, QTableWidgetItem(f"{dosing:.1f}"))
            self.status_table.setItem(row, 3, QTableWidgetItem(quality))

            status_item = QTableWidgetItem(status)
            if status == "运行正常":
                status_item.setBackground(QColor("#d5f5e3"))
            else:
                status_item.setBackground(QColor("#fadbd8"))
            self.status_table.setItem(row, 4, status_item)

            # 更新时间
            time_str = datetime.now().strftime("%H:%M:%S")
            self.status_table.setItem(row, 5, QTableWidgetItem(time_str))

    def start_monitoring(self):
        """开始监测"""
        self.data_timer.start()

    def stop_monitoring(self):
        """停止监测"""
        self.data_timer.stop()
