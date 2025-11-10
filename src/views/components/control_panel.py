"""
控制面板组件 - 系统级控制功能
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QGroupBox, QLabel, QPushButton,
                               QComboBox, QSlider, QProgressBar)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class ControlPanel(QWidget):
    """控制面板组件"""

    # 信号定义
    mode_changed = Signal(str)  # 控制模式改变
    emergency_stop = Signal()   # 紧急停止

    def __init__(self, parent=None):
        super().__init__(parent)
        self.control_mode = "自动"  # 默认自动模式

        self._setup_ui()

    def _setup_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # 控制模式组
        mode_group = QGroupBox("控制模式")
        mode_layout = QVBoxLayout(mode_group)

        # 模式选择按钮
        mode_btn_layout = QHBoxLayout()

        self.auto_btn = QPushButton("自动")
        self.auto_btn.setCheckable(True)
        self.auto_btn.setChecked(True)
        self.auto_btn.clicked.connect(lambda: self._set_mode("自动"))

        self.manual_btn = QPushButton("手动")
        self.manual_btn.setCheckable(True)
        self.manual_btn.clicked.connect(lambda: self._set_mode("手动"))

        mode_btn_layout.addWidget(self.auto_btn)
        mode_btn_layout.addWidget(self.manual_btn)
        mode_layout.addLayout(mode_btn_layout)

        # 当前模式显示
        self.mode_label = QLabel("当前模式: 自动")
        self.mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mode_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        self.mode_label.setStyleSheet("color: #27ae60;")
        mode_layout.addWidget(self.mode_label)

        layout.addWidget(mode_group)

        # 系统控制组
        system_group = QGroupBox("系统控制")
        system_layout = QVBoxLayout(system_group)

        # 紧急停止按钮
        self.emergency_btn = QPushButton("紧急停止")
        self.emergency_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        self.emergency_btn.clicked.connect(self._on_emergency_stop)
        system_layout.addWidget(self.emergency_btn)

        # 系统状态指示
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("系统状态:"))

        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #27ae60; font-size: 16px;")
        status_layout.addWidget(self.status_indicator)

        self.status_label = QLabel("运行正常")
        self.status_label.setStyleSheet("color: #27ae60;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        system_layout.addLayout(status_layout)
        layout.addWidget(system_group)

        # 参数设置组
        params_group = QGroupBox("全局参数")
        params_layout = QVBoxLayout(params_group)

        # 总体加药量控制
        dosing_layout = QHBoxLayout()
        dosing_layout.addWidget(QLabel("总体加药量:"))

        self.global_dosing_slider = QSlider(Qt.Orientation.Horizontal)
        self.global_dosing_slider.setRange(0, 100)
        self.global_dosing_slider.setValue(50)
        dosing_layout.addWidget(self.global_dosing_slider)

        self.dosing_value_label = QLabel("50%")
        dosing_layout.addWidget(self.dosing_value_label)
        params_layout.addLayout(dosing_layout)

        # 泡沫质量指示
        foam_layout = QHBoxLayout()
        foam_layout.addWidget(QLabel("泡沫质量:"))

        self.foam_quality_bar = QProgressBar()
        self.foam_quality_bar.setRange(0, 100)
        self.foam_quality_bar.setValue(75)
        self.foam_quality_bar.setFormat("良好")
        foam_layout.addWidget(self.foam_quality_bar)
        params_layout.addLayout(foam_layout)

        layout.addWidget(params_group)

    def _set_mode(self, mode):
        """设置控制模式"""
        self.control_mode = mode
        self.mode_label.setText(f"当前模式: {mode}")

        # 更新按钮状态
        self.auto_btn.setChecked(mode == "自动")
        self.manual_btn.setChecked(mode == "手动")

        # 发射信号
        self.mode_changed.emit(mode)

    def _on_emergency_stop(self):
        """紧急停止按钮点击"""
        self.emergency_stop.emit()
        self.status_indicator.setStyleSheet("color: #e74c3c; font-size: 16px;")
        self.status_label.setText("紧急停止")
        self.status_label.setStyleSheet("color: #e74c3c;")

    def update_system_status(self, status, message):
        """更新系统状态"""
        if status == "normal":
            self.status_indicator.setStyleSheet("color: #27ae60; font-size: 16px;")
            self.status_label.setStyleSheet("color: #27ae60;")
        elif status == "warning":
            self.status_indicator.setStyleSheet("color: #f39c12; font-size: 16px;")
            self.status_label.setStyleSheet("color: #f39c12;")
        else:  # error
            self.status_indicator.setStyleSheet("color: #e74c3c; font-size: 16px;")
            self.status_label.setStyleSheet("color: #e74c3c;")

        self.status_label.setText(message)
