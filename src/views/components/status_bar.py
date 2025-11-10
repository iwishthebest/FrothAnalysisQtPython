"""
状态栏组件 - 显示系统状态和信息
"""

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLabel,
                               QProgressBar, QSizePolicy)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QFont


class StatusBar(QWidget):
    """状态栏组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumHeight(30)

        self._setup_ui()
        self._setup_timers()

    def _setup_ui(self):
        """初始化用户界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 2, 10, 2)
        layout.setSpacing(15)

        # 时间显示
        self.time_label = QLabel()
        self.time_label.setFont(QFont("Microsoft YaHei", 9))
        layout.addWidget(self.time_label)

        # 系统状态指示
        self.status_label = QLabel("系统运行中")
        self.status_label.setFont(QFont("Microsoft YaHei", 9))
        self.status_label.setStyleSheet("color: #27ae60;")
        layout.addWidget(self.status_label)

        # 内存使用率
        memory_layout = QHBoxLayout()
        memory_layout.setSpacing(5)

        memory_label = QLabel("内存:")
        memory_label.setFont(QFont("Microsoft YaHei", 9))
        memory_layout.addWidget(memory_label)

        self.memory_bar = QProgressBar()
        self.memory_bar.setMaximumWidth(100)
        self.memory_bar.setRange(0, 100)
        self.memory_bar.setValue(45)
        self.memory_bar.setTextVisible(False)
        self.memory_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3498db;
            }
        """)
        memory_layout.addWidget(self.memory_bar)

        self.memory_label = QLabel("45%")
        self.memory_label.setFont(QFont("Microsoft YaHei", 9))
        memory_layout.addWidget(self.memory_label)

        layout.addLayout(memory_layout)

        # CPU使用率
        cpu_layout = QHBoxLayout()
        cpu_layout.setSpacing(5)

        cpu_label = QLabel("CPU:")
        cpu_label.setFont(QFont("Microsoft YaHei", 9))
        cpu_layout.addWidget(cpu_label)

        self.cpu_bar = QProgressBar()
        self.cpu_bar.setMaximumWidth(100)
        self.cpu_bar.setRange(0, 100)
        self.cpu_bar.setValue(30)
        self.cpu_bar.setTextVisible(False)
        self.cpu_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
            }
        """)
        cpu_layout.addWidget(self.cpu_bar)

        self.cpu_label = QLabel("30%")
        self.cpu_label.setFont(QFont("Microsoft YaHei", 9))
        cpu_layout.addWidget(self.cpu_label)

        layout.addLayout(cpu_layout)

        # 连接状态
        self.connection_label = QLabel("已连接")
        self.connection_label.setFont(QFont("Microsoft YaHei", 9))
        self.connection_label.setStyleSheet("color: #27ae60;")
        layout.addWidget(self.connection_label)

        layout.addStretch()

    def _setup_timers(self):
        """设置定时器"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_status)
        self.update_timer.start(1000)  # 1秒更新一次

    def _update_status(self):
        """更新状态信息"""
        # 更新时间
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        self.time_label.setText(current_time)

        # 模拟系统状态变化
        self._simulate_system_status()

    def _simulate_system_status(self):
        """模拟系统状态变化"""
        import random

        # 模拟内存使用率
        memory_usage = random.randint(40, 60)
        self.memory_bar.setValue(memory_usage)
        self.memory_label.setText(f"{memory_usage}%")

        # 模拟CPU使用率
        cpu_usage = random.randint(25, 40)
        self.cpu_bar.setValue(cpu_usage)
        self.cpu_label.setText(f"{cpu_usage}%")

        # 随机状态变化（小概率事件）
        if random.random() < 0.05:  # 5%概率
            self.status_label.setText("系统警告")
            self.status_label.setStyleSheet("color: #f39c12;")
        elif random.random() < 0.02:  # 2%概率
            self.connection_label.setText("连接中断")
            self.connection_label.setStyleSheet("color: #e74c3c;")
        else:
            self.status_label.setText("系统运行中")
            self.status_label.setStyleSheet("color: #27ae60;")
            self.connection_label.setText("已连接")
            self.connection_label.setStyleSheet("color: #27ae60;")

    def update_connection_status(self, connected):
        """更新连接状态"""
        if connected:
            self.connection_label.setText("已连接")
            self.connection_label.setStyleSheet("color: #27ae60;")
        else:
            self.connection_label.setText("连接中断")
            self.connection_label.setStyleSheet("color: #e74c3c;")

    def update_system_metrics(self, memory_usage, cpu_usage):
        """更新系统指标"""
        self.memory_bar.setValue(memory_usage)
        self.memory_label.setText(f"{memory_usage}%")

        self.cpu_bar.setValue(cpu_usage)
        self.cpu_label.setText(f"{cpu_usage}%")
