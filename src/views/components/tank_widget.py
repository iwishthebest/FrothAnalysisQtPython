from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QGroupBox, QLabel, QDoubleSpinBox,
                               QComboBox, QFrame, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
import numpy as np


class TankVisualizationWidget(QWidget):
    """浮选槽可视化组件 - 包含卡片化设计与双向流向逻辑"""

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
        # 增加外边距，避免卡片阴影被截断
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        # 1. 顶部标题 (美化版)
        title_label = QLabel("浮选槽串联控制 (正浮选流程)")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; letter-spacing: 2px;")
        layout.addWidget(title_label)

        # 2. 上方弹簧 (垂直居中)
        layout.addStretch(1)

        # 3. 浮选槽可视化区域
        tanks_widget = self.create_tanks_visualization()
        layout.addWidget(tanks_widget)

        # 4. 下方弹簧 (垂直居中)
        layout.addStretch(1)

    def create_tanks_visualization(self):
        """创建浮选槽可视化区域"""
        widget = QWidget()
        # 使用水平布局排列槽和流向指示器
        layout = QHBoxLayout(widget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 整体居中

        # 四个浮选槽配置
        tank_configs = [
            {"id": 0, "name": "铅快粗槽", "type": "粗选作业", "color": "#3498db"},
            {"id": 1, "name": "铅精一槽", "type": "精选一作业", "color": "#2ecc71"},
            {"id": 2, "name": "铅精二槽", "type": "精选二作业", "color": "#e74c3c"},
            {"id": 3, "name": "铅精三槽", "type": "精选三作业", "color": "#9b59b6"}
        ]

        # 创建浮选槽组件
        for i, config in enumerate(tank_configs):
            # 添加槽体卡片
            tank_widget = SingleTankWidget(config)
            self.tank_widgets.append(tank_widget)
            layout.addWidget(tank_widget)

            # 添加流向指示器（除了最后一个）
            if i < len(tank_configs) - 1:
                # 泡沫向右（去下一级），矿浆向左（返回上一级）
                flow_widget = FlowIndicator()
                layout.addWidget(flow_widget)

        return widget

    def update_tank_data(self, tank_data):
        """更新浮选槽数据"""
        for tank_id, data in tank_data.items():
            if tank_id < len(self.tank_widgets):
                self.tank_widgets[tank_id].update_data(data)


class FlowIndicator(QWidget):
    """
    流向指示器组件
    显示泡沫流向（向右）和矿浆流向（向左）
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(80)  # 增加宽度以容纳箭头
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(40)  # 上下箭头之间的间距

        # 1. 上层：泡沫流 (向右)
        froth_container = QWidget()
        froth_layout = QVBoxLayout(froth_container)
        froth_layout.setContentsMargins(0, 0, 0, 0)
        froth_layout.setSpacing(2)

        froth_arrow = QLabel("➡")
        froth_arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        froth_arrow.setStyleSheet("color: #f39c12; font-size: 24px; font-weight: bold;")  # 金色代表泡沫

        froth_label = QLabel("泡沫")
        froth_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        froth_label.setStyleSheet("color: #f39c12; font-size: 10px;")

        froth_layout.addWidget(froth_label)
        froth_layout.addWidget(froth_arrow)

        # 2. 下层：矿浆/中矿流 (向左)
        pulp_container = QWidget()
        pulp_layout = QVBoxLayout(pulp_container)
        pulp_layout.setContentsMargins(0, 0, 0, 0)
        pulp_layout.setSpacing(2)

        pulp_arrow = QLabel("⬅")
        pulp_arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pulp_arrow.setStyleSheet("color: #7f8c8d; font-size: 24px; font-weight: bold;")  # 灰色代表中矿

        pulp_label = QLabel("中矿返回")
        pulp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pulp_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")

        pulp_layout.addWidget(pulp_arrow)
        pulp_layout.addWidget(pulp_label)

        # 添加到主布局
        # 通过 addStretch 调整垂直位置，使其大致对齐槽体的上方泡沫层和下方矿浆层
        layout.addStretch(1)
        layout.addWidget(froth_container)
        layout.addStretch(1)  # 中间间距
        layout.addWidget(pulp_container)
        layout.addStretch(1)


class SingleTankWidget(QFrame):  # 改为继承 QFrame 以支持边框阴影
    """单个浮选槽组件 - 卡片式设计"""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.current_level = 1.2
        self.current_dosing = 50.0
        self.reagent_type = "捕收剂"
        self.setup_ui()

    def setup_ui(self):
        """初始化用户界面"""
        # 设置卡片外观
        self.setObjectName("TankCard")
        self.setStyleSheet("""
            #TankCard {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)

        # 添加阴影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        self.setMinimumWidth(200)
        self.setMaximumWidth(240)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(10)

        # 1. 标题区域
        name_label = QLabel(self.config["name"])
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {self.config['color']}; border: none;")
        layout.addWidget(name_label)

        type_label = QLabel(self.config["type"])
        type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        type_label.setFont(QFont("Microsoft YaHei", 10))
        type_label.setStyleSheet("color: #95a5a6; border: none; margin-bottom: 5px;")
        layout.addWidget(type_label)

        # 2. 浮选槽图形 (居中显示)
        graphic_container = QHBoxLayout()
        graphic_container.addStretch()
        self.tank_graphic = TankGraphicWidget(self.config["color"])
        graphic_container.addWidget(self.tank_graphic)
        graphic_container.addStretch()
        layout.addLayout(graphic_container)

        # 3. 控制参数区域
        # 移除之前的 GroupBox 边框，直接嵌入卡片
        control_widget = self.create_control_widget()
        layout.addWidget(control_widget)

    def create_control_widget(self):
        """创建控制参数区域 (无边框样式)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(8)

        # 统一样式
        label_style = "color: #555; font-size: 11px; font-weight: bold;"
        spin_style = """
            QDoubleSpinBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 2px;
                background: #f8f9fa;
            }
            QDoubleSpinBox:hover { border: 1px solid #409eff; }
        """
        combo_style = """
            QComboBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 2px;
                background: #f8f9fa;
            }
            QComboBox::drop-down { border: none; }
        """

        # 液位控制
        level_row = QHBoxLayout()
        lvl_lbl = QLabel("液位:")
        lvl_lbl.setStyleSheet(label_style)

        self.level_spinbox = QDoubleSpinBox()
        self.level_spinbox.setRange(0.5, 2.5)
        self.level_spinbox.setValue(1.2)
        self.level_spinbox.setSingleStep(0.1)
        self.level_spinbox.setStyleSheet(spin_style)
        self.level_spinbox.valueChanged.connect(self.on_level_changed)

        level_row.addWidget(lvl_lbl)
        level_row.addWidget(self.level_spinbox)
        level_row.addWidget(QLabel("m"))
        layout.addLayout(level_row)

        # 加药量控制
        dosing_row = QHBoxLayout()
        dos_lbl = QLabel("加药:")
        dos_lbl.setStyleSheet(label_style)

        self.dosing_spinbox = QDoubleSpinBox()
        self.dosing_spinbox.setRange(0, 200)
        self.dosing_spinbox.setValue(50)
        self.dosing_spinbox.setSingleStep(5)
        self.dosing_spinbox.setStyleSheet(spin_style)
        self.dosing_spinbox.valueChanged.connect(self.on_dosing_changed)

        dosing_row.addWidget(dos_lbl)
        dosing_row.addWidget(self.dosing_spinbox)
        dosing_row.addWidget(QLabel("ml"))  # 简化单位显示
        layout.addLayout(dosing_row)

        # 药剂类型
        reagent_row = QHBoxLayout()
        rag_lbl = QLabel("药剂:")
        rag_lbl.setStyleSheet(label_style)

        self.reagent_combo = QComboBox()
        self.reagent_combo.addItems(["捕收剂", "起泡剂", "抑制剂"])
        self.reagent_combo.setStyleSheet(combo_style)
        self.reagent_combo.currentTextChanged.connect(self.on_reagent_changed)

        reagent_row.addWidget(rag_lbl)
        reagent_row.addWidget(self.reagent_combo)
        layout.addLayout(reagent_row)

        return widget

    def on_level_changed(self, value):
        self.current_level = value
        self.tank_graphic.set_water_level(value / 2.5)

    def on_dosing_changed(self, value):
        self.current_dosing = value

    def on_reagent_changed(self, text):
        self.reagent_type = text

    def update_data(self, data):
        if 'level' in data:
            self.level_spinbox.setValue(data['level'])
        if 'dosing' in data:
            self.dosing_spinbox.setValue(data['dosing'])
        if 'reagent' in data:
            self.reagent_combo.setCurrentText(data['reagent'])


class TankGraphicWidget(QWidget):
    """浮选槽图形显示组件 (优化版)"""

    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.color = color
        self.water_level = 0.5
        self.setMinimumSize(100, 120)  # 稍微调小一点适配卡片

    def set_water_level(self, level):
        self.water_level = max(0.0, min(1.0, level))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        # 1. 绘制槽体 (U型结构)
        tank_rect = self.rect().adjusted(10, 10, -10, -10)

        # 槽壁颜色
        wall_color = QColor(self.color).darker(120)
        painter.setPen(QPen(wall_color, 4))
        painter.setBrush(QBrush(QColor("#f4f6f7")))  # 浅灰背景

        # 绘制类似U型的烧杯形状，使用圆角矩形代替之前的路径，避免 Attribute Error
        painter.drawRoundedRect(tank_rect, 15, 15)

        # 2. 绘制矿浆 (Liquid)
        # 计算液面高度
        fill_height = int(tank_rect.height() * self.water_level * 0.8)  # 留出顶部空间给泡沫
        liquid_rect = QRect(
            tank_rect.left() + 2,
            tank_rect.bottom() - fill_height - 2,
            tank_rect.width() - 4,
            fill_height
        )

        liquid_color = QColor(self.color)
        liquid_color.setAlpha(180)  # 半透明
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(liquid_color))
        # 下部直角，上部平直
        painter.drawRect(liquid_rect)

        # 3. 绘制泡沫层 (Froth)
        foam_height = max(15, int(fill_height * 0.25))
        foam_rect = QRect(
            liquid_rect.left(),
            liquid_rect.top() - foam_height + 5,  # 稍微重叠一点
            liquid_rect.width(),
            foam_height
        )

        # 泡沫颜色 (带一点槽体颜色的灰白色)
        foam_color = QColor(self.color).lighter(180)
        foam_color.setAlpha(220)
        painter.setBrush(QBrush(foam_color))
        painter.drawRoundedRect(foam_rect, 10, 10)

        # 4. 绘制搅拌器示意 (可选，增加细节)
        shaft_x = width // 2
        painter.setPen(QPen(QColor("#7f8c8d"), 2))
        painter.drawLine(shaft_x, tank_rect.top() - 5, shaft_x, liquid_rect.bottom() - 10)

        painter.end()