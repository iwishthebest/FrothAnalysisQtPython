from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QGroupBox, QLabel, QDoubleSpinBox,
                               QComboBox, QPushButton)
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
import numpy as np


class TankVisualizationWidget(QWidget):
    """浮选槽可视化组件"""

    # 信号定义
    level_changed = Signal(int, float)  # 槽ID, 新液位
    dosing_changed = Signal(int, float)  # 槽ID, 新加药量
    reagent_changed = Signal(int, str)  # 槽ID, 新药剂类型

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tank_widgets = []
        self.setup_ui()

    def setup_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("浮选槽串联控制")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 浮选槽可视化区域
        tanks_widget = self.create_tanks_visualization()
        layout.addWidget(tanks_widget)

    def create_tanks_visualization(self):
        """创建浮选槽可视化区域"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(0)
        layout.setContentsMargins(20, 10, 20, 10)

        # 四个浮选槽配置
        tank_configs = [
            {"id": 0, "name": "铅快粗槽", "type": "粗选", "color": "#3498db"},
            {"id": 1, "name": "铅精一槽", "type": "精选一", "color": "#2ecc71"},
            {"id": 2, "name": "铅精二槽", "type": "精选二", "color": "#e74c3c"},
            {"id": 3, "name": "铅精三槽", "type": "精选三", "color": "#9b59b6"}
        ]

        # 创建浮选槽组件
        for i, config in enumerate(tank_configs):
            tank_widget = SingleTankWidget(config)
            self.tank_widgets.append(tank_widget)
            layout.addWidget(tank_widget)

            # 添加箭头（除了最后一个）
            if i < len(tank_configs) - 1:
                arrow_widget = self.create_flow_arrow()
                layout.addWidget(arrow_widget)

        return widget

    def create_flow_arrow(self):
        """创建流向箭头"""
        widget = QWidget()
        widget.setFixedWidth(40)

        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        arrow_label = QLabel("➡➡")
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow_label.setFont(QFont("Arial", 20))
        arrow_label.setStyleSheet("color: #95a5a6;")
        layout.addWidget(arrow_label)

        return widget

    def update_tank_data(self, tank_data):
        """更新浮选槽数据"""
        for tank_id, data in tank_data.items():
            if tank_id < len(self.tank_widgets):
                self.tank_widgets[tank_id].update_data(data)


class SingleTankWidget(QWidget):
    """单个浮选槽组件"""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.current_level = 1.2
        self.current_dosing = 50.0
        self.reagent_type = "捕收剂"
        self.setup_ui()

    def setup_ui(self):
        """初始化用户界面"""
        self.setMinimumWidth(180)
        self.setMaximumWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)

        # 槽名称和类型
        name_label = QLabel(self.config["name"])
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {self.config['color']};")
        layout.addWidget(name_label)

        type_label = QLabel(self.config["type"])
        type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        type_label.setFont(QFont("Microsoft YaHei", 10))
        type_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(type_label)

        # 浮选槽图形
        self.tank_graphic = TankGraphicWidget(self.config["color"])
        layout.addWidget(self.tank_graphic)

        # 控制参数区域
        control_widget = self.create_control_widget()
        layout.addWidget(control_widget)

    def create_control_widget(self):
        """创建控制参数区域"""
        widget = QGroupBox("控制参数")
        widget.setMaximumHeight(120)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 12, 8, 8)

        # 液位控制
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("液位:"))

        self.level_spinbox = QDoubleSpinBox()
        self.level_spinbox.setRange(0.5, 2.5)
        self.level_spinbox.setValue(1.2)
        self.level_spinbox.setSingleStep(0.1)
        self.level_spinbox.valueChanged.connect(self.on_level_changed)
        level_layout.addWidget(self.level_spinbox)
        level_layout.addWidget(QLabel("m"))
        level_layout.addStretch()

        # 加药量控制
        dosing_layout = QHBoxLayout()
        dosing_layout.addWidget(QLabel("加药:"))

        self.dosing_spinbox = QDoubleSpinBox()
        self.dosing_spinbox.setRange(0, 200)
        self.dosing_spinbox.setValue(50)
        self.dosing_spinbox.setSingleStep(5)
        self.dosing_spinbox.valueChanged.connect(self.on_dosing_changed)
        dosing_layout.addWidget(self.dosing_spinbox)
        dosing_layout.addWidget(QLabel("ml/min"))
        dosing_layout.addStretch()

        # 药剂类型
        reagent_layout = QHBoxLayout()
        reagent_layout.addWidget(QLabel("药剂:"))

        self.reagent_combo = QComboBox()
        self.reagent_combo.addItems(["捕收剂", "起泡剂", "抑制剂"])
        self.reagent_combo.currentTextChanged.connect(self.on_reagent_changed)
        reagent_layout.addWidget(self.reagent_combo)
        reagent_layout.addStretch()

        layout.addLayout(level_layout)
        layout.addLayout(dosing_layout)
        layout.addLayout(reagent_layout)

        return widget

    def on_level_changed(self, value):
        """液位值改变"""
        self.current_level = value
        self.tank_graphic.set_water_level(value / 2.5)  # 归一化到0-1

    def on_dosing_changed(self, value):
        """加药量改变"""
        self.current_dosing = value

    def on_reagent_changed(self, text):
        """药剂类型改变"""
        self.reagent_type = text

    def update_data(self, data):
        """更新数据"""
        if 'level' in data:
            self.level_spinbox.setValue(data['level'])
        if 'dosing' in data:
            self.dosing_spinbox.setValue(data['dosing'])
        if 'reagent' in data:
            self.reagent_combo.setCurrentText(data['reagent'])


class TankGraphicWidget(QWidget):
    """浮选槽图形显示组件"""

    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.color = color
        self.water_level = 0.5  # 0-1之间的值
        self.setMinimumSize(120, 150)

    def set_water_level(self, level):
        """设置水位（0-1）"""
        self.water_level = max(0.0, min(1.0, level))
        self.update()

    def paintEvent(self, event):
        """绘制浮选槽"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        # 绘制槽体外框
        tank_rect = self.rect().adjusted(10, 10, -10, -10)
        painter.setPen(QPen(QColor(self.color), 3))
        painter.setBrush(QBrush(QColor(240, 240, 240)))
        painter.drawRoundedRect(tank_rect, 10, 10)

        # 绘制水位
        water_height = int(tank_rect.height() * self.water_level)
        water_rect = QRect(tank_rect.left(), tank_rect.bottom() - water_height,
                           tank_rect.width(), water_height)

        water_color = QColor(self.color)
        water_color.setAlpha(128)
        painter.setBrush(QBrush(water_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(water_rect, 8, 8)

        # 绘制泡沫层
        foam_height = max(10, water_height // 5)
        foam_rect = QRect(tank_rect.left(), water_rect.top() - foam_height,
                          tank_rect.width(), foam_height)

        foam_color = QColor(255, 255, 255, 180)
        painter.setBrush(QBrush(foam_color))
        painter.drawRoundedRect(foam_rect, 5, 5)

        painter.end()
