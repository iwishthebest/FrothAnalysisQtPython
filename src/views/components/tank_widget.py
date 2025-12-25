import math
import random
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QDoubleSpinBox, QComboBox, QLineEdit,
                               QFrame, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, Signal, QRectF, QTimer, QPointF
from PySide6.QtGui import (QPainter, QColor, QPen, QBrush, QFont,
                           QPainterPath, QLinearGradient, QPolygonF)


class TankVisualizationWidget(QWidget):
    """
    浮选槽可视化组件 - 工业HMI风格
    包含：动态搅拌动画、气泡粒子效果、实体管道连接、实时药剂流量监测
    """

    # 信号定义
    level_changed = Signal(int, float)

    # 药剂配置映射 (Tank ID -> List of (Database Key, Display Name))
    # 严格对应 HistoryPage 中的配置
    TANK_REAGENTS_CONFIG = {
        0: [  # 铅快粗槽 (6种药剂)
            ('qkc_dinghuangyao1', '丁黄药1'), ('qkc_dinghuangyao2', '丁黄药2'),
            ('qkc_yiliudan1', '乙硫氮1'), ('qkc_yiliudan2', '乙硫氮2'),
            ('qkc_shihui', '石灰'), ('qkc_5_you', '2#油')
        ],
        1: [  # 铅精一槽 (3种药剂)
            ('qkj1_dinghuangyao', '丁黄药'), ('qkj1_yiliudan', '乙硫氮'),
            ('qkj1_shihui', '石灰')
        ],
        2: [  # 铅精二槽 (3种药剂)
            ('qkj2_yiliudan', '乙硫氮'), ('qkj2_shihui', '石灰'),
            ('qkj2_dinghuangyao', '丁黄药')
        ],
        3: [  # 铅精三槽 (5种药剂)
            ('qkj3_dinghuangyao', '丁黄药'), ('qkj3_yiliudan', '乙硫氮'),
            ('qkj3_ds1', 'DS1'), ('qkj3_ds2', 'DS2'),
            ('qkj3_shihui', '石灰')
        ]
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tank_widgets = []
        self.setup_ui()

    def setup_ui(self):
        """初始化全局布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # 1. 顶部标题
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("浮选槽串联控制 (正浮选流程)")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50; letter-spacing: 1px;")

        # 流程说明图例
        legend_layout = QHBoxLayout()
        self._add_legend(legend_layout, "#f39c12", "泡沫/精矿流向")
        legend_layout.addSpacing(15)
        self._add_legend(legend_layout, "#7f8c8d", "中矿/尾矿流向")

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addLayout(legend_layout)

        layout.addWidget(title_container)

        # 2. 核心可视化区域
        scroll_area_content = self.create_tanks_visualization()
        layout.addWidget(scroll_area_content, 1)  # 伸缩因子1，占据主要空间

    def _add_legend(self, layout, color, text):
        indicator = QFrame()
        indicator.setFixedSize(16, 4)
        indicator.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(indicator)
        layout.addWidget(lbl)

    def create_tanks_visualization(self):
        """创建槽体和管道的水平布局"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(0)  # 管道紧贴槽体
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 定义槽体配置
        tank_configs = [
            {"id": 0, "name": "铅快粗槽", "type": "粗选作业", "color": "#3498db"},
            {"id": 1, "name": "铅精一槽", "type": "精选一", "color": "#2ecc71"},
            {"id": 2, "name": "铅精二槽", "type": "精选二", "color": "#e74c3c"},
            {"id": 3, "name": "铅精三槽", "type": "精选三", "color": "#9b59b6"}
        ]

        for i, config in enumerate(tank_configs):
            # 获取该槽对应的药剂配置
            reagents = self.TANK_REAGENTS_CONFIG.get(config["id"], [])

            # 1. 添加槽体
            tank = SingleTankWidget(config, reagents)
            self.tank_widgets.append(tank)
            layout.addWidget(tank)

            # 2. 添加连接管道 (除了最后一个)
            if i < len(tank_configs) - 1:
                pipe = PipeConnectionWidget()
                layout.addWidget(pipe)

        return widget

    def update_tank_data(self, tank_data):
        """外部数据更新接口"""
        for tank_id, data in tank_data.items():
            # 确保 tank_id 是整数索引
            try:
                idx = int(tank_id) if isinstance(tank_id, (int, str)) else -1
                if 0 <= idx < len(self.tank_widgets):
                    self.tank_widgets[idx].update_data(data)
            except ValueError:
                pass


class PipeConnectionWidget(QWidget):
    """
    工业风格管道连接组件
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(50)  # 管道长度
        self.setSizePolicy(self.sizePolicy().Policy.Fixed, self.sizePolicy().Policy.Preferred)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        froth_y = h * 0.35  # 泡沫流高度 (对齐槽体上方)
        pulp_y = h * 0.55  # 矿浆流高度 (对齐槽体下方)

        # 1. 绘制泡沫流 (向右 ->)
        froth_pen = QPen(QColor("#f39c12"), 3)
        froth_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(froth_pen)
        painter.drawLine(0, int(froth_y), w, int(froth_y))
        self._draw_arrow(painter, w - 5, froth_y, direction="right", color="#f39c12")

        # 2. 绘制中矿/尾矿流 (向左 <-)
        pulp_pen = QPen(QColor("#95a5a6"), 3)  # 灰色管道
        pulp_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pulp_pen)
        painter.drawLine(0, int(pulp_y), w, int(pulp_y))
        self._draw_arrow(painter, 5, pulp_y, direction="left", color="#95a5a6")

    def _draw_arrow(self, painter, x, y, direction="right", color="#000"):
        painter.setBrush(QBrush(QColor(color)))
        painter.setPen(Qt.PenStyle.NoPen)
        arrow_size = 5
        points = []
        if direction == "right":
            points = [QPointF(x, y), QPointF(x - arrow_size, y - arrow_size), QPointF(x - arrow_size, y + arrow_size)]
        else:
            points = [QPointF(x, y), QPointF(x + arrow_size, y - arrow_size), QPointF(x + arrow_size, y + arrow_size)]
        painter.drawPolygon(points)


class TankGraphicWidget(QWidget):
    """
    高保真浮选槽图形 (带搅拌动画)
    """

    def __init__(self, base_color_hex, parent=None):
        super().__init__(parent)
        self.base_color = QColor(base_color_hex)
        self.water_level = 0.6
        self.setMinimumSize(100, 120)

        self.angle = 0
        self.bubbles = []
        for _ in range(12): self._spawn_bubble()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_animation)
        self.timer.start(50)

    def _spawn_bubble(self):
        self.bubbles.append(
            [random.uniform(0.2, 0.8), random.uniform(0.5, 0.9), random.uniform(0.005, 0.015), random.uniform(2, 4)])

    def _update_animation(self):
        self.angle = (self.angle + 15) % 360
        for b in self.bubbles:
            b[1] -= b[2]
            b[0] += math.sin(b[1] * 10) * 0.002
            if b[1] < (1.0 - self.water_level):
                b[1] = random.uniform(0.8, 1.0)
                b[0] = random.uniform(0.2, 0.8)
        self.update()

    def set_water_level(self, level):
        self.water_level = max(0.2, min(0.9, level))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        tank_rect = QRectF(10, 10, w - 20, h - 20)
        fill_height = tank_rect.height() * self.water_level
        liquid_y = tank_rect.bottom() - fill_height

        # 1. 槽体
        path = QPainterPath()
        path.moveTo(tank_rect.left(), tank_rect.top())
        path.lineTo(tank_rect.left(), tank_rect.bottom() - 10)
        path.quadTo(tank_rect.left(), tank_rect.bottom(), tank_rect.left() + 10, tank_rect.bottom())
        path.lineTo(tank_rect.right() - 10, tank_rect.bottom())
        path.quadTo(tank_rect.right(), tank_rect.bottom(), tank_rect.right(), tank_rect.bottom() - 10)
        path.lineTo(tank_rect.right(), tank_rect.top())

        painter.fillPath(path, QBrush(QColor("#f4f6f7")))
        painter.setPen(QPen(QColor("#bdc3c7"), 2))
        painter.drawPath(path)

        # 2. 液体
        liquid_rect = QRectF(tank_rect.left() + 2, liquid_y, tank_rect.width() - 4, fill_height - 2)
        painter.save()
        painter.setClipPath(path)
        grad = QLinearGradient(liquid_rect.topLeft(), liquid_rect.bottomRight())
        grad.setColorAt(0, self.base_color.lighter(130))
        grad.setColorAt(1, self.base_color)
        painter.fillRect(liquid_rect, grad)

        # 气泡
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 120))
        for b in self.bubbles:
            painter.drawEllipse(
                QPointF(tank_rect.left() + b[0] * tank_rect.width(), tank_rect.top() + b[1] * tank_rect.height()), b[3],
                b[3])
        painter.restore()

        # 3. 搅拌器
        shaft_x = w / 2
        painter.setPen(QPen(QColor("#555"), 3))
        painter.drawLine(int(shaft_x), int(tank_rect.top() - 5), int(shaft_x), int(tank_rect.bottom() - 20))

        painter.save()
        painter.translate(shaft_x, tank_rect.bottom() - 20)
        painter.scale(1.0, 0.3)
        painter.rotate(self.angle)
        painter.setPen(QPen(QColor("#333"), 1))
        painter.setBrush(QColor("#7f8c8d"))
        painter.drawRect(-20, -3, 40, 6)
        painter.drawRect(-3, -20, 6, 40)
        painter.restore()


class SingleTankWidget(QFrame):
    """
    单个槽体卡片
    包含：TankGraphicWidget + 动态生成的只读药剂仪表盘
    """

    def __init__(self, config, reagents, parent=None):
        super().__init__(parent)
        self.config = config
        self.reagents = reagents  # 药剂配置列表 [(key, name), ...]
        self.reagent_widgets = {}  # 存储控件引用 {key: QLineEdit}

        self.current_level = 1.2
        self.setup_ui()

    def setup_ui(self):
        self.setObjectName("TankCard")
        self.setStyleSheet("""
            #TankCard {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #dcdfe6;
            }
            #TankCard:hover {
                border: 1px solid #3498db;
                background-color: #fcfcfc;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        self.setFixedWidth(240)  # 固定宽度

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 15)
        layout.setSpacing(8)

        # 1. 头部信息
        header = QHBoxLayout()
        name_lbl = QLabel(self.config["name"])
        name_lbl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {self.config['color']};")
        type_lbl = QLabel(self.config["type"])
        type_lbl.setStyleSheet("font-size: 10px; color: #909399;")

        header_v = QVBoxLayout()
        header_v.setSpacing(0)
        header_v.addWidget(name_lbl)
        header_v.addWidget(type_lbl)

        # 运行状态指示灯
        self.status_led = QLabel()
        self.status_led.setFixedSize(10, 10)
        self.status_led.setStyleSheet("background-color: #2ecc71; border-radius: 5px; border: 1px solid #fff;")

        header.addLayout(header_v)
        header.addStretch()
        header.addWidget(self.status_led)
        layout.addLayout(header)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #f0f0f0;")
        layout.addWidget(line)

        # 2. 槽体图形 (占比小一点)
        graphic_layout = QHBoxLayout()
        self.tank_graphic = TankGraphicWidget(self.config["color"])
        graphic_layout.addWidget(self.tank_graphic)
        layout.addLayout(graphic_layout)

        # 3. 控制与显示区域
        ctrl_widget = self.create_control_widget()
        layout.addWidget(ctrl_widget)

        # 底部填充，保证对齐
        layout.addStretch()

    def create_control_widget(self):
        """创建控制参数区域"""
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setContentsMargins(0, 5, 0, 0)
        layout.setVerticalSpacing(6)
        layout.setHorizontalSpacing(8)

        # 统一样式
        lbl_style = "color: #606266; font-size: 11px;"

        # --- 1. 液位设定 (保留可控) ---
        layout.addWidget(QLabel("液位设定:", styleSheet="font-weight:bold; font-size:11px;"), 0, 0, 1, 2)

        self.spin_level = QDoubleSpinBox()
        self.spin_level.setRange(0.0, 3.0)
        self.spin_level.setValue(1.2)
        self.spin_level.setSuffix(" m")
        self.spin_level.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
        self.spin_level.setStyleSheet("""
            QDoubleSpinBox { border: 1px solid #dcdfe6; border-radius: 3px; padding: 2px; }
            QDoubleSpinBox:hover { border-color: #409eff; }
        """)
        self.spin_level.valueChanged.connect(self._on_level_changed)
        layout.addWidget(self.spin_level, 0, 2)

        # --- 2. 药剂流量监测 (只读仪表) ---
        layout.addWidget(QLabel("药剂流量实时监测:", styleSheet="font-weight:bold; font-size:11px; margin-top:5px;"), 1,
                         0, 1, 3)

        # 动态生成药剂显示行
        row_idx = 2
        for key, name in self.reagents:
            # 药剂名称
            name_lbl = QLabel(name)
            name_lbl.setStyleSheet(lbl_style)
            name_lbl.setToolTip(f"数据库标签: {key}")

            # 流量数值显示 (模拟数码管)
            value_display = QLineEdit("0.0")
            value_display.setReadOnly(True)
            value_display.setAlignment(Qt.AlignmentFlag.AlignRight)
            value_display.setFixedWidth(70)
            value_display.setStyleSheet("""
                QLineEdit {
                    background-color: #2c3e50; /* 深色背景 */
                    color: #00ff00;            /* 绿色荧光字 */
                    border: 1px solid #555;
                    border-radius: 3px;
                    font-family: 'Consolas', monospace;
                    font-weight: bold;
                    padding-right: 4px;
                    font-size: 12px;
                }
            """)

            # 单位
            unit_lbl = QLabel("ml/min")
            unit_lbl.setStyleSheet("color: #909399; font-size: 10px;")

            layout.addWidget(name_lbl, row_idx, 0)
            layout.addWidget(value_display, row_idx, 1)
            layout.addWidget(unit_lbl, row_idx, 2)

            # 存储控件引用以便更新
            self.reagent_widgets[key] = value_display
            row_idx += 1

        return widget

    def _on_level_changed(self, val):
        self.tank_graphic.set_water_level(val / 2.5)

    def update_data(self, data):
        """
        更新数据
        data: 字典，包含液位和药剂数据
        """
        # 更新液位 (如果有)
        if 'level' in data:
            self.spin_level.setValue(float(data['level']))

        # 更新药剂流量 (根据 key 匹配)
        for key, widget in self.reagent_widgets.items():
            # 尝试从数据中获取该药剂的值
            # 数据源可能是扁平化的，直接用 key 获取
            if key in data:
                val = data[key]
                # 格式化显示
                try:
                    widget.setText(f"{float(val):.1f}")
                except (ValueError, TypeError):
                    widget.setText("--")