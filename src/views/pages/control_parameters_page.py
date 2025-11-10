"""控制参数页面 - 包含浮选槽可视化和控制参数面板"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QGroupBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from ..components.tank_graphic import TankGraphicWidget
from ..components.tank_parameters import TankParametersWidget


class ControlParametersPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tank_widgets = []  # 存储浮选槽组件
        self._setup_ui()

    def _setup_ui(self):
        """初始化控制参数界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        title_label = QLabel("浮选过程控制参数")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        layout.addWidget(title_label)
        layout.addStretch()

        # 浮选槽可视化
        tanks_widget = self._create_flotation_tanks_visualization()
        layout.addWidget(tanks_widget)
        layout.addStretch()

        # 控制参数面板（可进一步拆分到独立组件）
        control_params = self._create_control_parameters_panel()
        layout.addWidget(control_params)
        layout.addStretch()

    def _create_flotation_tanks_visualization(self):
        """创建浮选槽串联可视化"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(5)

        # 浮选槽配置
        tank_configs = [
            {"name": "铅快粗槽", "type": "粗选", "color": "#3498db"},
            {"name": "铅精一槽", "type": "精选一", "color": "#2ecc71"},
            {"name": "铅精二槽", "type": "精选二", "color": "#e74c3c"},
            {"name": "铅精三槽", "type": "精选三", "color": "#9b59b6"}
        ]

        for i, config in enumerate(tank_configs):
            tank_widget = self._create_single_tank_widget(config, i)
            self.tank_widgets.append(tank_widget)
            layout.addWidget(tank_widget)

            # 添加流向箭头（最后一个槽不添加）
            if i < len(tank_configs) - 1:
                layout.addWidget(self._create_flow_arrow())

        return widget

    def _create_single_tank_widget(self, config, tank_id):
        """创建单个浮选槽组件"""
        widget = QWidget()
        widget.setMinimumWidth(180)
        widget.setMaximumWidth(220)
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        # 槽名称
        name_label = QLabel(config["name"])
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {config['color']};")

        # 槽类型
        type_label = QLabel(config["type"])
        type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        type_label.setFont(QFont("Microsoft YaHei", 10))
        type_label.setStyleSheet("color: #7f8c8d;")

        # 槽图形
        tank_graphic = TankGraphicWidget(config["color"], tank_id)

        # 参数显示
        params_widget = TankParametersWidget(tank_id)

        # 组装布局
        layout.addWidget(name_label)
        layout.addWidget(type_label)
        layout.addWidget(tank_graphic)
        layout.addWidget(params_widget)

        return widget

    def _create_flow_arrow(self):
        """创建槽间流向箭头"""
        arrow_label = QLabel("→")
        arrow_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow_label.setStyleSheet("color: #7f8c8d;")
        return arrow_label

    def _create_control_parameters_panel(self):
        """创建控制参数面板（可根据需要扩展）"""
        panel = QGroupBox("全局控制参数")
        layout = QVBoxLayout(panel)

        # 此处可添加全局控制参数组件
        placeholder = QLabel("控制参数面板内容")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(placeholder)

        return panel