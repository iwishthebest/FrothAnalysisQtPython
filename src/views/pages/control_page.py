from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                               QLabel, QDoubleSpinBox, QComboBox, QPushButton,
                               QGridLayout, QProgressBar)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import numpy as np


class ControlPage(QWidget):
    """控制参数页面 - 包含液位控制、加药量控制等"""
    
    # 信号定义
    level_setpoint_changed = Signal(int, float)  # 槽ID, 设定值
    dosing_setpoint_changed = Signal(int, float)  # 槽ID, 设定值
    reagent_type_changed = Signal(int, str)  # 槽ID, 药剂类型
    control_mode_changed = Signal(str)  # 控制模式: "auto" 或 "manual"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.control_mode = "auto"  # 默认自动模式
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)
        
        # 标题
        title_label = QLabel("浮选过程智能控制")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin: 10px;")
        layout.addWidget(title_label)
        
        # 控制模式选择
        mode_widget = self.create_control_mode_section()
        layout.addWidget(mode_widget)
        
        # 液位控制区域
        level_widget = self.create_level_control_section()
        layout.addWidget(level_widget)
        
        # 加药量控制区域
        dosing_widget = self.create_dosing_control_section()
        layout.addWidget(dosing_widget)
        
        # 状态指示区域
        status_widget = self.create_status_section()
        layout.addWidget(status_widget)
        
        layout.addStretch()
        
    def create_control_mode_section(self):
        """创建控制模式选择区域"""
        widget = QGroupBox("控制模式")
        widget.setMaximumHeight(100)
        layout = QVBoxLayout(widget)
        
        # 模式选择按钮
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.auto_mode_btn = QPushButton("自动模式")
        self.manual_mode_btn = QPushButton("手动模式")
        
        # 设置按钮样式
        for btn in [self.auto_mode_btn, self.manual_mode_btn]:
            btn.setCheckable(True)
            btn.setFixedSize(120, 40)
            btn.setFont(QFont("Microsoft YaHei", 11))
            
        # 默认选择自动模式
        self.auto_mode_btn.setChecked(True)
        self.update_mode_buttons_style()
        
        button_layout.addWidget(self.auto_mode_btn)
        button_layout.addWidget(self.manual_mode_btn)
        
        # 状态指示
        mode_status_layout = QHBoxLayout()
        mode_status_layout.addWidget(QLabel("当前模式:"))
        self.mode_status_label = QLabel("自动控制")
        self.mode_status_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self.mode_status_label.setStyleSheet("color: #27ae60;")
        mode_status_layout.addWidget(self.mode_status_label)
        mode_status_layout.addStretch()
        
        layout.addLayout(button_layout)
        layout.addLayout(mode_status_layout)
        
        return widget
        
    def create_level_control_section(self):
        """创建液位控制区域"""
        widget = QGroupBox("液位智能控制")
        layout = QGridLayout(widget)
        
        # 标题行
        layout.addWidget(QLabel("浮选槽"), 0, 0)
        layout.addWidget(QLabel("设定值(m)"), 0, 1)
        layout.addWidget(QLabel("当前值(m)"), 0, 2)
        layout.addWidget(QLabel("PID参数"), 0, 3)
        
        # 四个浮选槽的控制参数
        self.level_controls = []
        for i in range(4):
            row = i + 1
            
            # 槽名称
            tank_names = ["铅快粗槽", "铅精一槽", "铅精二槽", "铅精三槽"]
            tank_label = QLabel(tank_names[i])
            tank_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
            layout.addWidget(tank_label, row, 0)
            
            # 设定值
            level_spin = QDoubleSpinBox()
            level_spin.setRange(0.5, 2.5)
            level_spin.setValue(1.2 + i * 0.1)
            level_spin.setDecimals(2)
            level_spin.setSingleStep(0.1)
            level_spin.valueChanged.connect(
                lambda value, idx=i: self.on_level_setpoint_changed(idx, value)
            )
            layout.addWidget(level_spin, row, 1)
            
            # 当前值显示
            current_level_label = QLabel("--")
            current_level_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            current_level_label.setStyleSheet("font-weight: bold; color: #3498db;")
            layout.addWidget(current_level_label, row, 2)
            
            # PID参数显示
            pid_label = QLabel("Kp=1.0, Ki=0.1, Kd=0.01")
            pid_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
            layout.addWidget(pid_label, row, 3)
            
            self.level_controls.append({
                'setpoint': level_spin,
                'current': current_level_label,
                'pid': pid_label
            })
            
        return widget
        
    def create_dosing_control_section(self):
        """创建加药量控制区域"""
        widget = QGroupBox("加药量自动控制")
        layout = QGridLayout(widget)
        
        # 标题行
        layout.addWidget(QLabel("浮选槽"), 0, 0)
        layout.addWidget(QLabel("药剂类型"), 0, 1)
        layout.addWidget(QLabel("设定值(ml/min)"), 0, 2)
        layout.addWidget(QLabel("当前值(ml/min)"), 0, 3)
        layout.addWidget(QLabel("状态"), 0, 4)
        
        # 四个浮选槽的加药控制
        self.dosing_controls = []
        for i in range(4):
            row = i + 1
            
            # 槽名称
            tank_names = ["铅快粗槽", "铅精一槽", "铅精二槽", "铅精三槽"]
            tank_label = QLabel(tank_names[i])
            tank_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
            layout.addWidget(tank_label, row, 0)
            
            # 药剂类型选择
            reagent_combo = QComboBox()
            reagent_combo.addItems(["捕收剂", "起泡剂", "抑制剂"])
            reagent_combo.currentTextChanged.connect(
                lambda text, idx=i: self.on_reagent_type_changed(idx, text)
            )
            layout.addWidget(reagent_combo, row, 1)
            
            # 加药量设定
            dosing_spin = QDoubleSpinBox()
            dosing_spin.setRange(0, 200)
            dosing_spin.setValue(50 + i * 10)
            dosing_spin.setSingleStep(5)
            dosing_spin.valueChanged.connect(
                lambda value, idx=i: self.on_dosing_setpoint_changed(idx, value)
            )
            layout.addWidget(dosing_spin, row, 2)
            
            # 当前值显示
            current_dosing_label = QLabel("--")
            current_dosing_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            current_dosing_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
            layout.addWidget(current_dosing_label, row, 3)
            
            # 状态指示
            status_indicator = QLabel("●")
            status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_indicator.setStyleSheet("color: green; font-weight: bold; font-size: 16px;")
            layout.addWidget(status_indicator, row, 4)
            
            self.dosing_controls.append({
                'reagent': reagent_combo,
                'setpoint': dosing_spin,
                'current': current_dosing_label,
                'status': status_indicator
            })
            
        return widget
        
    def create_status_section(self):
        """创建状态指示区域"""
        widget = QGroupBox("控制状态监控")
        layout = QHBoxLayout(widget)
        
        # 总体控制效果
        effect_layout = QVBoxLayout()
        effect_layout.addWidget(QLabel("控制效果"))
        self.control_effect_bar = QProgressBar()
        self.control_effect_bar.setRange(0, 100)
        self.control_effect_bar.setValue(85)
        self.control_effect_bar.setFormat("优化程度: %p%")
        effect_layout.addWidget(self.control_effect_bar)
        
        # 系统稳定性
        stability_layout = QVBoxLayout()
        stability_layout.addWidget(QLabel("系统稳定性"))
        self.stability_bar = QProgressBar()
        self.stability_bar.setRange(0, 100)
        self.stability_bar.setValue(92)
        self.stability_bar.setFormat("稳定度: %p%")
        stability_layout.addWidget(self.stability_bar)
        
        # 能耗指标
        energy_layout = QVBoxLayout()
        energy_layout.addWidget(QLabel("能耗指标"))
        self.energy_bar = QProgressBar()
        self.energy_bar.setRange(0, 100)
        self.energy_bar.setValue(78)
        self.energy_bar.setFormat("效率: %p%")
        energy_layout.addWidget(self.energy_bar)
        
        layout.addLayout(effect_layout)
        layout.addLayout(stability_layout)
        layout.addLayout(energy_layout)
        
        return widget
        
    def setup_connections(self):
        """设置信号连接"""
        # 控制模式按钮连接
        self.auto_mode_btn.clicked.connect(self.on_auto_mode_selected)
        self.manual_mode_btn.clicked.connect(self.on_manual_mode_selected)
        
    def on_auto_mode_selected(self):
        """选择自动模式"""
        if self.auto_mode_btn.isChecked():
            self.manual_mode_btn.setChecked(False)
            self.control_mode = "auto"
            self.mode_status_label.setText("自动控制")
            self.mode_status_label.setStyleSheet("color: #27ae60;")
            self.control_mode_changed.emit("auto")
            
    def on_manual_mode_selected(self):
        """选择手动模式"""
        if self.manual_mode_btn.isChecked():
            self.auto_mode_btn.setChecked(False)
            self.control_mode = "manual"
            self.mode_status_label.setText("手动控制")
            self.mode_status_label.setStyleSheet("color: #e67e22;")
            self.control_mode_changed.emit("manual")
            
    def update_mode_buttons_style(self):
        """更新模式按钮样式"""
        if self.control_mode == "auto":
            self.auto_mode_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:checked {
                    background-color: #2ecc71;
                }
            """)
            self.manual_mode_btn.setStyleSheet("""
                QPushButton {
                    background-color: #bdc3c7;
                    color: #7f8c8d;
                    border: none;
                    border-radius: 5px;
                }
            """)
        else:
            self.manual_mode_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e67e22;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:checked {
                    background-color: #f39c12;
                }
            """)
            self.auto_mode_btn.setStyleSheet("""
                QPushButton {
                    background-color: #bdc3c7;
                    color: #7f8c8d;
                    border: none;
                    border-radius: 5px;
                }
            """)
            
    def on_level_setpoint_changed(self, tank_id, value):
        """液位设定值改变"""
        self.level_setpoint_changed.emit(tank_id, value)
        
    def on_dosing_setpoint_changed(self, tank_id, value):
        """加药量设定值改变"""
        self.dosing_setpoint_changed.emit(tank_id, value)
        
    def on_reagent_type_changed(self, tank_id, reagent_type):
        """药剂类型改变"""
        self.reagent_type_changed.emit(tank_id, reagent_type)
        
    def update_control_data(self, control_data):
        """更新控制数据"""
        try:
            # 更新液位当前值
            for i, control in enumerate(self.level_controls):
                if f'level_current_{i}' in control_data:
                    current_value = control_data[f'level_current_{i}']
                    control['current'].setText(f"{current_value:.2f}")
                    
            # 更新加药量当前值
            for i, control in enumerate(self.dosing_controls):
                if f'dosing_current_{i}' in control_data:
                    current_value = control_data[f'dosing_current_{i}']
                    control['current'].setText(f"{current_value:.1f}")
                    
                # 更新状态指示
                if f'dosing_status_{i}' in control_data:
                    status = control_data[f'dosing_status_{i}']
                    color = "green" if status == "normal" else "red"
                    control['status'].setStyleSheet(f"color: {color}; font-weight: bold; font-size: 16px;")
                    
            # 更新控制效果指标
            if 'control_effect' in control_data:
                self.control_effect_bar.setValue(int(control_data['control_effect']))
                
            if 'stability' in control_data:
                self.stability_bar.setValue(int(control_data['stability']))
                
            if 'energy_efficiency' in control_data:
                self.energy_bar.setValue(int(control_data['energy_efficiency']))
                
        except Exception as e:
            print(f"更新控制数据时出错: {e}")