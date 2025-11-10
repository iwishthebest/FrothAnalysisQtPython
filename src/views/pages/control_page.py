"""
控制页面 - 参数设置和过程控制
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QGroupBox, QLabel, QSlider, QDoubleSpinBox,
                               QPushButton, QComboBox, QCheckBox, QTextEdit)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPalette, QColor
import random


class ControlPage(QWidget):
    """控制页面 - 参数设置和过程控制"""

    # 信号定义
    parameter_changed = Signal(str, object)  # 参数名称, 新值
    control_mode_changed = Signal(str)       # 控制模式
    emergency_stop_signal = Signal()          # 紧急停止

    def __init__(self, parent=None):
        super().__init__(parent)
        self.control_mode = "自动"  # 自动/手动
        self._setup_ui()

    def _setup_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("过程控制面板")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 控制模式选择
        layout.addWidget(self._create_mode_selector())

        # 参数控制区域
        control_layout = QHBoxLayout()
        control_layout.addWidget(self._create_level_control())
        control_layout.addWidget(self._create_dosing_control())
        layout.addLayout(control_layout)

        # PID参数设置
        layout.addWidget(self._create_pid_control())

        # 高级控制
        layout.addWidget(self._create_advanced_control())

    def _create_mode_selector(self):
        """创建模式选择器"""
        group = QGroupBox("控制模式")
        layout = QHBoxLayout(group)

        # 自动模式按钮
        self.auto_btn = QPushButton("自动模式")
        self.auto_btn.setCheckable(True)
        self.auto_btn.setChecked(True)
        self.auto_btn.clicked.connect(self._on_auto_mode)
        self.auto_btn.setStyleSheet("""
            QPushButton:checked {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
            }
        """)

        # 手动模式按钮
        self.manual_btn = QPushButton("手动模式")
        self.manual_btn.setCheckable(True)
        self.manual_btn.clicked.connect(self._on_manual_mode)
        self.manual_btn.setStyleSheet("""
            QPushButton:checked {
                background-color: #e67e22;
                color: white;
                font-weight: bold;
            }
        """)

        layout.addWidget(self.auto_btn)
        layout.addWidget(self.manual_btn)
        layout.addStretch()

        # 模式状态显示
        self.mode_status = QLabel("自动模式 - 系统自动调节参数")
        self.mode_status.setStyleSheet("color: #27ae60; font-weight: bold;")
        layout.addWidget(self.mode_status)

        return group

    def _create_level_control(self):
        """创建液位控制组件"""
        group = QGroupBox("液位控制")
        layout = QVBoxLayout(group)

        # 总体液位控制
        overall_layout = QHBoxLayout()
        overall_layout.addWidget(QLabel("总体液位:"))

        self.level_slider = QSlider(Qt.Orientation.Horizontal)
        self.level_slider.setRange(50, 150)  # 0.5m - 1.5m 的百分比
        self.level_slider.setValue(100)      # 1.0m
        self.level_slider.valueChanged.connect(self._on_level_changed)
        overall_layout.addWidget(self.level_slider)

        self.level_value = QLabel("1.00 m")
        overall_layout.addWidget(self.level_value)
        layout.addLayout(overall_layout)

        # 单个槽位控制
        tanks_layout = QVBoxLayout()
        tanks = ["铅快粗槽", "铅精一槽", "铅精二槽", "铅精三槽"]

        for tank in tanks:
            tank_layout = QHBoxLayout()
            tank_layout.addWidget(QLabel(f"{tank}:"))

            spinbox = QDoubleSpinBox()
            spinbox.setRange(0.5, 2.5)
            spinbox.setValue(1.2 + random.uniform(-0.1, 0.1))
            spinbox.setSingleStep(0.05)
            spinbox.valueChanged.connect(
                lambda value, t=tank: self._on_tank_level_changed(t, value)
            )
            tank_layout.addWidget(spinbox)
            tank_layout.addWidget(QLabel("m"))
            tank_layout.addStretch()

            tanks_layout.addLayout(tank_layout)

        layout.addLayout(tanks_layout)

        return group

    def _create_dosing_control(self):
        """创建加药量控制组件"""
        group = QGroupBox("加药量控制")
        layout = QVBoxLayout(group)

        # 药剂类型选择
        reagent_layout = QHBoxLayout()
        reagent_layout.addWidget(QLabel("药剂类型:"))

        self.reagent_combo = QComboBox()
        self.reagent_combo.addItems(["捕收剂", "起泡剂", "抑制剂", "调整剂"])
        self.reagent_combo.currentTextChanged.connect(self._on_reagent_changed)
        reagent_layout.addWidget(self.reagent_combo)
        reagent_layout.addStretch()
        layout.addLayout(reagent_layout)

        # 总体加药量控制
        overall_dosing_layout = QHBoxLayout()
        overall_dosing_layout.addWidget(QLabel("总体加药量:"))

        self.dosing_slider = QSlider(Qt.Orientation.Horizontal)
        self.dosing_slider.setRange(0, 200)
        self.dosing_slider.setValue(100)
        self.dosing_slider.valueChanged.connect(self._on_dosing_changed)
        overall_dosing_layout.addWidget(self.dosing_slider)

        self.dosing_value = QLabel("100 ml/min")
        overall_dosing_layout.addWidget(self.dosing_value)
        layout.addLayout(overall_dosing_layout)

        # 单个槽位加药控制
        dosing_tanks_layout = QVBoxLayout()
        tanks = ["铅快粗槽", "铅精一槽", "铅精二槽", "铅精三槽"]

        for tank in tanks:
            tank_dosing_layout = QHBoxLayout()
            tank_dosing_layout.addWidget(QLabel(f"{tank}:"))

            spinbox = QDoubleSpinBox()
            spinbox.setRange(0, 200)
            spinbox.setValue(50 + random.uniform(-10, 10))
            spinbox.setSingleStep(5)
            spinbox.valueChanged.connect(
                lambda value, t=tank: self._on_tank_dosing_changed(t, value)
            )
            tank_dosing_layout.addWidget(spinbox)
            tank_dosing_layout.addWidget(QLabel("ml/min"))
            tank_dosing_layout.addStretch()

            dosing_tanks_layout.addLayout(tank_dosing_layout)

        layout.addLayout(dosing_tanks_layout)

        return group

    def _create_pid_control(self):
        """创建PID参数控制"""
        group = QGroupBox("PID参数设置")
        layout = QHBoxLayout(group)

        # P参数
        p_layout = QVBoxLayout()
        p_layout.addWidget(QLabel("比例系数 Kp"))
        self.kp_spinbox = QDoubleSpinBox()
        self.kp_spinbox.setRange(0.1, 10.0)
        self.kp_spinbox.setValue(1.2)
        self.kp_spinbox.setSingleStep(0.1)
        p_layout.addWidget(self.kp_spinbox)

        # I参数
        i_layout = QVBoxLayout()
        i_layout.addWidget(QLabel("积分时间 Ti"))
        self.ti_spinbox = QDoubleSpinBox()
        self.ti_spinbox.setRange(0.01, 1.0)
        self.ti_spinbox.setValue(0.1)
        self.ti_spinbox.setSingleStep(0.01)
        i_layout.addWidget(self.ti_spinbox)

        # D参数
        d_layout = QVBoxLayout()
        d_layout.addWidget(QLabel("微分时间 Td"))
        self.td_spinbox = QDoubleSpinBox()
        self.td_spinbox.setRange(0.001, 0.1)
        self.td_spinbox.setValue(0.01)
        self.td_spinbox.setSingleStep(0.001)
        d_layout.addWidget(self.td_spinbox)

        layout.addLayout(p_layout)
        layout.addLayout(i_layout)
        layout.addLayout(d_layout)

        # 应用按钮
        apply_btn = QPushButton("应用PID参数")
        apply_btn.clicked.connect(self._apply_pid_parameters)
        layout.addWidget(apply_btn)

        return group

    def _create_advanced_control(self):
        """创建高级控制组件"""
        group = QGroupBox("高级控制")
        layout = QHBoxLayout(group)

        # 左侧：优化算法选择
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("优化算法:"))

        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems([
            "传统PID控制",
            "模糊PID控制",
            "神经网络优化",
            "模型预测控制"
        ])
        left_layout.addWidget(self.algorithm_combo)

        # 优化目标
        left_layout.addWidget(QLabel("优化目标:"))
        self.optimization_checkboxes = []
        targets = ["最大化回收率", "稳定泡沫层", "节能优化", "质量优先"]

        for target in targets:
            checkbox = QCheckBox(target)
            self.optimization_checkboxes.append(checkbox)
            left_layout.addWidget(checkbox)

        layout.addLayout(left_layout)

        # 右侧：控制日志
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("控制日志:"))

        self.control_log = QTextEdit()
        self.control_log.setMaximumHeight(150)
        self.control_log.setReadOnly(True)
        right_layout.addWidget(self.control_log)

        # 紧急停止按钮
        emergency_btn = QPushButton("紧急停止")
        emergency_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        emergency_btn.clicked.connect(self._on_emergency_stop)
        right_layout.addWidget(emergency_btn)

        layout.addLayout(right_layout)

        return group

    def _on_auto_mode(self):
        """自动模式选择"""
        self.control_mode = "自动"
        self.manual_btn.setChecked(False)
        self.mode_status.setText("自动模式 - 系统自动调节参数")
        self.mode_status.setStyleSheet("color: #27ae60; font-weight: bold;")
        self.control_mode_changed.emit("自动")
        self._log_control_action("切换到自动模式")

    def _on_manual_mode(self):
        """手动模式选择"""
        self.control_mode = "手动"
        self.auto_btn.setChecked(False)
        self.mode_status.setText("手动模式 - 手动调节参数")
        self.mode_status.setStyleSheet("color: #e67e22; font-weight: bold;")
        self.control_mode_changed.emit("手动")
        self._log_control_action("切换到手动模式")

    def _on_level_changed(self, value):
        """液位设定值改变"""
        level = value / 100.0  # 转换为米
        self.level_value.setText(f"{level:.2f} m")
        self.parameter_changed.emit("总体液位", level)
        self._log_control_action(f"设定总体液位: {level:.2f}m")

    def _on_dosing_changed(self, value):
        """加药量设定值改变"""
        self.dosing_value.setText(f"{value} ml/min")
        self.parameter_changed.emit("总体加药量", value)
        self._log_control_action(f"设定总体加药量: {value}ml/min")

    def _on_reagent_changed(self, reagent):
        """药剂类型改变"""
        self.parameter_changed.emit("药剂类型", reagent)
        self._log_control_action(f"切换药剂类型: {reagent}")

    def _on_tank_level_changed(self, tank_name, level):
        """单个槽位液位改变"""
        self.parameter_changed.emit(f"{tank_name}_液位", level)
        self._log_control_action(f"设定{tank_name}液位: {level:.2f}m")

    def _on_tank_dosing_changed(self, tank_name, dosing):
        """单个槽位加药量改变"""
        self.parameter_changed.emit(f"{tank_name}_加药量", dosing)
        self._log_control_action(f"设定{tank_name}加药量: {dosing}ml/min")

    def _apply_pid_parameters(self):
        """应用PID参数"""
        kp = self.kp_spinbox.value()
        ti = self.ti_spinbox.value()
        td = self.td_spinbox.value()

        self.parameter_changed.emit("PID参数", {"Kp": kp, "Ti": ti, "Td": td})
        self._log_control_action(f"应用PID参数: Kp={kp:.2f}, Ti={ti:.2f}, Td={td:.3f}")

    def _on_emergency_stop(self):
        """紧急停止"""
        self.emergency_stop_signal.emit()
        self._log_control_action("紧急停止触发", is_error=True)

    def _log_control_action(self, message, is_error=False):
        """记录控制动作日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")

        if is_error:
            log_entry = f"[{timestamp}] ❌ {message}"
            self.control_log.setTextColor(QColor("#e74c3c"))
        else:
            log_entry = f"[{timestamp}] ✅ {message}"
            self.control_log.setTextColor(QColor("#27ae60"))

        self.control_log.append(log_entry)
        # 保持日志长度
        if self.control_log.document().lineCount() > 100:
            cursor = self.control_log.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.select(cursor.SelectionType.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()  # 删除换行符
