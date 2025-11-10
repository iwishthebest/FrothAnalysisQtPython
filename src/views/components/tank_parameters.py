"""浮选槽参数显示组件"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtGui import QFont


class TankParametersWidget(QWidget):
    def __init__(self, tank_id, parent=None):
        super().__init__(parent)
        self.tank_id = tank_id
        self._setup_ui()

    def _setup_ui(self):
        """初始化参数显示布局"""
        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        # 液位显示
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("液位:"))
        self.level_label = QLabel("-- m")
        self.level_label.setObjectName(f"tank_{self.tank_id}_level")
        self.level_label.setStyleSheet("font-weight: bold;")
        level_layout.addWidget(self.level_label)
        level_layout.addStretch()

        # 加药量显示
        dosing_layout = QHBoxLayout()
        dosing_layout.addWidget(QLabel("加药:"))
        self.dosing_label = QLabel("-- ml/min")
        self.dosing_label.setObjectName(f"tank_{self.tank_id}_dosing")
        self.dosing_label.setStyleSheet("font-weight: bold;")
        dosing_layout.addWidget(self.dosing_label)
        dosing_layout.addStretch()

        layout.addLayout(level_layout)
        layout.addLayout(dosing_layout)

    def update_parameters(self, level, dosing):
        """更新参数显示"""
        self.level_label.setText(f"{level:.2f} m")
        self.dosing_label.setText(f"{dosing:.1f} ml/min")