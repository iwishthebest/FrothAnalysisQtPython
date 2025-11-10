"""
浮选槽组件 - 显示和控制浮选槽状态
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QGroupBox, QSlider, QDoubleSpinBox,
                               QProgressBar, QComboBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
import numpy as np


class TankGraphicWidget(QWidget):
    """浮选槽图形显示组件"""

    def __init__(self, tank_name, parent=None):
        super().__init__(parent)
        self.tank_name = tank_name
        self.water_level = 0.6  # 默认水位
        self.foam_height = 0.1  # 默认泡沫高度
        self.setMinimumSize(120, 150)

    def paintEvent(self, event):
        """绘制浮选槽"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        # 绘制槽体外框
        tank_rect = self.rect().adjusted(10, 10, -10, -10)
        painter.setPen(QPen(QColor("#34495e"), 3))
        painter.setBrush(QBrush(QColor("#ecf0f1")))
        painter.drawRoundedRect(tank_rect, 10, 10)

        # 绘制水位
        water_height = int(tank_rect.height() * self.water_level)
        water_rect = tank_rect.adjusted(0, tank_rect.height() - water_height, 0, 0)

        water_color = QColor("#3498db")
        water_color.setAlpha(180)
        painter.setBrush(QBrush(water_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(water_rect, 8, 8)

        # 绘制泡沫层
        foam_height = int(tank_rect.height() * self.foam_height)
        foam_rect = water_rect.adjusted(0, -foam_height, 0, 0)

        foam_color = QColor("#ffffff")
        foam_color.setAlpha(200)
        painter.setBrush(QBrush(foam_color))
        painter.drawRoundedRect(foam_rect, 5, 5)

        # 绘制刻度
        painter.setPen(QPen(QColor("#7f8c8d"), 2))
        for i in range(0, 101, 25):
            y_pos = tank_rect.bottom() - int(tank_rect.height() * i / 100)
            painter.drawLine(tank_rect.left() - 5, y_pos, tank_rect.left(), y_pos)

        # 绘制槽体名称
        painter.setPen(QPen(QColor("#2c3e50")))
        painter.drawText(tank_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                        self.tank_name)

    def update_levels(self, water_level, foam_height):
        """更新水位和泡沫高度"""
        self.water_level = max(0.0, min(1.0, water_level))
        self.foam_height = max(0.0, min(0.3, foam_height))
        self.update()


class TankWidget(QWidget):
    """浮选槽控制组件"""

    # 信号定义
    level_changed = Signal(str, float)  # 槽名称, 新液位
    dosing_changed = Signal(str, float)  # 槽名称, 新加药量

    def __init__(self, tank_name, initial_level, initial_dosing, parent=None):
        super().__init__(parent)
        self.tank_name = tank_name
        self.current_level = initial_level
        self.current_dosing = initial_dosing

        self._setup_ui()

    def _setup_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)

        # 图形显示
        self.graphic_widget = TankGraphicWidget(self.tank_name)
        layout.addWidget(self.graphic_widget)

        # 参数显示组
        params_group = QGroupBox("实时参数")
        params_layout = QVBoxLayout(params_group)

        # 液位显示
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("液位:"))
        self.level_label = QLabel(f"{self.current_level:.2f} m")
        level_layout.addWidget(self.level_label)
        level_layout.addStretch()
        params_layout.addLayout(level_layout)

        # 加药量显示
        dosing_layout = QHBoxLayout()
        dosing_layout.addWidget(QLabel("加药:"))
        self.dosing_label = QLabel(f"{self.current_dosing:.1f} ml/min")
        dosing_layout.addWidget(self.dosing_label)
        dosing_layout.addStretch()
        params_layout.addLayout(dosing_layout)

        layout.addWidget(params_group)

        # 控制组
        control_group = QGroupBox("控制参数")
        control_layout = QVBoxLayout(control_group)

        # 液位控制
        level_control_layout = QHBoxLayout()
        level_control_layout.addWidget(QLabel("液位设定:"))

        self.level_spinbox = QDoubleSpinBox()
        self.level_spinbox.setRange(0.5, 2.5)
        self.level_spinbox.setValue(self.current_level)
        self.level_spinbox.setSingleStep(0.1)
        self.level_spinbox.valueChanged.connect(self._on_level_changed)
        level_control_layout.addWidget(self.level_spinbox)
        level_control_layout.addStretch()
        control_layout.addLayout(level_control_layout)

        # 加药量控制
        dosing_control_layout = QHBoxLayout()
        dosing_control_layout.addWidget(QLabel("加药设定:"))

        self.dosing_spinbox = QDoubleSpinBox()
        self.dosing_spinbox.setRange(0, 200)
        self.dosing_spinbox.setValue(self.current_dosing)
        self.dosing_spinbox.setSingleStep(5)
        self.dosing_spinbox.valueChanged.connect(self._on_dosing_changed)
        dosing_control_layout.addWidget(self.dosing_spinbox)
        dosing_control_layout.addStretch()
        control_layout.addLayout(dosing_control_layout)

        layout.addWidget(control_group)

    def _on_level_changed(self, value):
        """液位设定值改变"""
        self.level_changed.emit(self.tank_name, value)
        self.update_display(value, self.current_dosing)

    def _on_dosing_changed(self, value):
        """加药量设定值改变"""
        self.dosing_changed.emit(self.tank_name, value)
        self.current_dosing = value
        self.dosing_label.setText(f"{value:.1f} ml/min")

    def update_display(self, level, dosing):
        """更新显示"""
        self.current_level = level
        self.current_dosing = dosing

        self.level_label.setText(f"{level:.2f} m")
        self.dosing_label.setText(f"{dosing:.1f} ml/min")

        # 更新图形显示（水位归一化到0-1范围）
        normalized_level = (level - 0.5) / 2.0  # 从0.5-2.5映射到0-1
        foam_height = 0.1 + (dosing / 200) * 0.2  # 根据加药量计算泡沫高度
        self.graphic_widget.update_levels(normalized_level, foam_height)
