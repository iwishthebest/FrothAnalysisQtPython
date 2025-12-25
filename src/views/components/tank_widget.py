import math
import random
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QDoubleSpinBox, QComboBox, QLineEdit,
                               QFrame, QGraphicsDropShadowEffect, QScrollArea,
                               QSizePolicy)
from PySide6.QtCore import Qt, Signal, QRectF, QTimer, QPointF
from PySide6.QtGui import (QPainter, QColor, QPen, QBrush, QFont,
                           QPainterPath, QLinearGradient, QPolygonF)


class TankVisualizationWidget(QWidget):
    """
    浮选槽可视化组件 - 工业HMI风格
    包含：动态搅拌动画、气泡粒子效果、实体管道连接、垂直堆叠仪表盘
    """

    # 信号定义
    level_changed = Signal(int, float)

    # 药剂配置映射 (Tank ID -> List of (Database Key, Display Name))
    TANK_REAGENTS_CONFIG = {
        0: [  # 铅快粗槽 (6种)
            ('qkc_dinghuangyao1', '丁黄药1'), ('qkc_dinghuangyao2', '丁黄药2'),
            ('qkc_yiliudan1', '乙硫氮1'), ('qkc_yiliudan2', '乙硫氮2'),
            ('qkc_shihui', '石灰'), ('qkc_5_you', '2#油')
        ],
        1: [  # 铅精一槽 (3种)
            ('qkj1_dinghuangyao', '丁黄药'), ('qkj1_yiliudan', '乙硫氮'),
            ('qkj1_shihui', '石灰')
        ],
        2: [  # 铅精二槽 (3种)
            ('qkj2_yiliudan', '乙硫氮'), ('qkj2_shihui', '石灰'),
            ('qkj2_dinghuangyao', '丁黄药')
        ],
        3: [  # 铅精三槽 (5种)
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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 1. 顶部标题
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(10, 0, 10, 0)

        title_label = QLabel("浮选槽串联监控 (正浮选流程)")
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
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("background: transparent;")

        scroll_content = QWidget()
        self.tanks_layout = QHBoxLayout(scroll_content)
        self.tanks_layout.setSpacing(0)
        self.tanks_layout.setContentsMargins(5, 5, 5, 5)
        self.tanks_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self._init_tanks()

        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area, 1)

    def _init_tanks(self):
        tank_configs = [
            {"id": 0, "name": "铅快粗槽", "type": "粗选作业", "color": "#3498db"},
            {"id": 1, "name": "铅精一槽", "type": "精选一", "color": "#2ecc71"},
            {"id": 2, "name": "铅精二槽", "type": "精选二", "color": "#e74c3c"},
            {"id": 3, "name": "铅精三槽", "type": "精选三", "color": "#9b59b6"}
        ]

        for i, config in enumerate(tank_configs):
            reagents = self.TANK_REAGENTS_CONFIG.get(config["id"], [])

            # 添加槽体
            tank = SingleTankWidget(config, reagents)
            self.tank_widgets.append(tank)
            self.tanks_layout.addWidget(tank)

            # 添加管道
            if i < len(tank_configs) - 1:
                pipe = PipeConnectionWidget()
                self.tanks_layout.addWidget(pipe)

    def _add_legend(self, layout, color, text):
        indicator = QFrame()
        indicator.setFixedSize(16, 4)
        indicator.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(indicator)
        layout.addWidget(lbl)

    def update_tank_data(self, tank_data):
        for tank_id, data in tank_data.items():
            try:
                idx = int(tank_id) if isinstance(tank_id, (int, str)) else -1
                if 0 <= idx < len(self.tank_widgets):
                    self.tank_widgets[idx].update_data(data)
            except ValueError:
                pass


class PipeConnectionWidget(QWidget):
    """连接管道"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(30)
        self.setSizePolicy(self.sizePolicy().Policy.Fixed, self.sizePolicy().Policy.Preferred)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # 根据 SingleTankWidget 的布局估算连接点高度
        # Header(40) + Graphic(120/2) = ~100px (泡沫)
        # Header(40) + Graphic(120) + Some padding = ~160px (矿浆)
        froth_y = 90
        pulp_y = 150

        # 泡沫流 (右)
        painter.setPen(QPen(QColor("#f39c12"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(0, froth_y, w, froth_y)
        self._draw_arrow(painter, w / 2, froth_y, "right", "#f39c12")

        # 矿浆流 (左)
        painter.setPen(QPen(QColor("#95a5a6"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(0, pulp_y, w, pulp_y)
        self._draw_arrow(painter, w / 2, pulp_y, "left", "#95a5a6")

    def _draw_arrow(self, painter, x, y, direction, color):
        painter.setBrush(QBrush(QColor(color)))
        painter.setPen(Qt.PenStyle.NoPen)
        s = 4
        pts = [QPointF(x, y), QPointF(x - s, y - s), QPointF(x - s, y + s)] if direction == "right" else \
            [QPointF(x, y), QPointF(x + s, y - s), QPointF(x + s, y + s)]
        painter.drawPolygon(pts)


class TankGraphicWidget(QWidget):
    """槽体图形"""

    def __init__(self, base_color_hex, parent=None):
        super().__init__(parent)
        self.base_color = QColor(base_color_hex)
        self.water_level = 0.6
        self.setMinimumSize(100, 120)  # 进一步减小最小高度

        self.angle = 0
        self.bubbles = []
        for _ in range(10): self._spawn_bubble()

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
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        tank_rect = QRectF(15, 10, w - 30, h - 20)
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
        painter.drawLine(int(shaft_x), int(tank_rect.top() - 10), int(shaft_x), int(tank_rect.bottom() - 25))

        painter.save()
        painter.translate(shaft_x, tank_rect.bottom() - 25)
        painter.scale(1.0, 0.3)
        painter.rotate(self.angle)
        painter.setPen(QPen(QColor("#333"), 1))
        painter.setBrush(QColor("#7f8c8d"))
        painter.drawRect(-20, -3, 40, 6)
        painter.drawRect(-3, -20, 6, 40)
        painter.restore()


class SingleTankWidget(QFrame):
    """
    单个槽体卡片 - 垂直布局，四块监测区域
    """

    # 定义最大药剂显示行数，用于占位对齐
    MAX_REAGENT_COUNT = 6

    def __init__(self, config, reagents, parent=None):
        super().__init__(parent)
        self.config = config
        self.reagents = reagents
        self.reagent_widgets = {}
        self.setup_ui()

    def setup_ui(self):
        self.setObjectName("TankCard")
        self.setStyleSheet("""
            #TankCard {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #dcdfe6;
            }
            #TankCard:hover {
                border: 1px solid #3498db;
                background-color: #fbfbfb;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)

        self.setFixedWidth(260)  # 宽度适中

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 8, 6, 10)
        main_layout.setSpacing(6)

        # 1. 头部
        header = QHBoxLayout()
        header.setContentsMargins(4, 0, 4, 0)
        name_lbl = QLabel(self.config["name"])
        name_lbl.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {self.config['color']};")

        self.status_led = QLabel()
        self.status_led.setFixedSize(10, 10)
        self.status_led.setStyleSheet("background-color: #2ecc71; border-radius: 5px; border: 1px solid #fff;")
        self.status_led.setToolTip("运行正常")

        header.addWidget(name_lbl)
        header.addStretch()
        header.addWidget(self.status_led)
        main_layout.addLayout(header)

        # 2. 图形区 (居中)
        graphic_container = QHBoxLayout()
        self.tank_graphic = TankGraphicWidget(self.config["color"])
        graphic_container.addWidget(self.tank_graphic)
        main_layout.addLayout(graphic_container)

        # 3. 监测数据区 (垂直布局)
        monitor_layout = QVBoxLayout()
        monitor_layout.setSpacing(6)
        monitor_layout.setContentsMargins(0, 2, 0, 2)

        # --- 块1: 药剂流量 (列表) ---
        reagent_panel = self._create_reagent_block()
        monitor_layout.addWidget(reagent_panel)

        # --- 块2: 液位监测 (无设定，只读) ---
        level_panel = self._create_data_block("液位监测 (m)", "level", "1.20", "#2ecc71", icon="📏")
        self.lbl_level_real = level_panel.findChild(QLabel, "val_level")  # 保存引用
        monitor_layout.addWidget(level_panel)

        # --- 块3: 充气量 (预留) ---
        air_panel = self._create_data_block("充气量 (m³/min)", "air", "0.00", "#1abc9c", icon="💨")
        monitor_layout.addWidget(air_panel)

        # --- 块4: 冲水量 (预留) ---
        water_panel = self._create_data_block("冲水量 (L/min)", "water", "0.0", "#3498db", icon="💧")
        monitor_layout.addWidget(water_panel)

        main_layout.addLayout(monitor_layout)
        main_layout.addStretch()

    def _create_frame_style(self):
        return """
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e1e4e8;
                border-radius: 4px;
            }
        """

    def _create_reagent_block(self):
        """块1: 药剂流量列表 (列表式仪表)"""
        frame = QFrame()
        frame.setStyleSheet(self._create_frame_style())
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题栏
        title_bar = QLabel("  药剂流量 (ml/min)")
        title_bar.setFixedHeight(24)
        title_bar.setStyleSheet("""
            background-color: #e9ecef; 
            color: #495057; font-weight: bold; font-size: 11px;
            border-top-left-radius: 4px; border-top-right-radius: 4px;
            border-bottom: 1px solid #e1e4e8;
        """)
        layout.addWidget(title_bar)

        # 内容区
        content_widget = QWidget()
        grid = QGridLayout(content_widget)
        grid.setContentsMargins(8, 6, 8, 6)
        grid.setVerticalSpacing(4)
        grid.setHorizontalSpacing(10)
        grid.setColumnStretch(1, 1)

        for i in range(self.MAX_REAGENT_COUNT):
            if i < len(self.reagents):
                key, name = self.reagents[i]

                # 名称
                lbl = QLabel(name)
                lbl.setStyleSheet("font-size: 11px; color: #606266;")
                lbl.setToolTip(key)

                # 数值 (LCD风格)
                val_display = QLabel("0.0")
                val_display.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                val_display.setStyleSheet("""
                    background: #343a40; color: #f1c40f; 
                    border-radius: 2px; font-family: 'Consolas'; 
                    font-size: 11px; font-weight: bold; padding: 1px 4px;
                """)
                self.reagent_widgets[key] = val_display

                grid.addWidget(lbl, i, 0)
                grid.addWidget(val_display, i, 1)
            else:
                # 占位符
                lbl = QLabel(" ")
                lbl.setStyleSheet("font-size: 11px;")
                val = QLabel(" ")
                val.setStyleSheet("font-size: 11px; padding: 1px 4px;")
                grid.addWidget(lbl, i, 0)
                grid.addWidget(val, i, 1)

        layout.addWidget(content_widget)
        return frame

    def _create_data_block(self, title_text, obj_name, default_val, value_color, icon=""):
        """通用单值数据块"""
        frame = QFrame()
        frame.setStyleSheet(self._create_frame_style())
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题栏
        title_bar = QLabel(f"  {icon} {title_text}")
        title_bar.setFixedHeight(24)
        title_bar.setStyleSheet("""
            background-color: #e9ecef; 
            color: #495057; font-weight: bold; font-size: 11px;
            border-top-left-radius: 4px; border-top-right-radius: 4px;
            border-bottom: 1px solid #e1e4e8;
        """)
        layout.addWidget(title_bar)

        # 内容区
        content = QWidget()
        h_layout = QHBoxLayout(content)
        h_layout.setContentsMargins(10, 8, 10, 8)

        # 数值显示
        val_lbl = QLabel(default_val)
        val_lbl.setObjectName(f"val_{obj_name}")
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val_lbl.setStyleSheet(f"""
            background: #343a40; color: {value_color};
            border-radius: 3px; font-family: 'Consolas'; letter-spacing: 1px;
            font-size: 16px; font-weight: bold; padding: 4px 10px;
            min-width: 80px;
        """)

        h_layout.addStretch()
        h_layout.addWidget(val_lbl)
        h_layout.addStretch()

        layout.addWidget(content)
        return frame

    def update_data(self, data):
        # 液位更新
        if 'level' in data:
            try:
                val = float(data['level'])
                if self.lbl_level_real:
                    self.lbl_level_real.setText(f"{val:.2f}")
                self.tank_graphic.set_water_level(val / 2.5)  # 假设2.5m为满量程
            except:
                pass

        # 药剂更新
        for key, widget in self.reagent_widgets.items():
            if key in data:
                try:
                    val = float(data[key])
                    widget.setText(f"{val:.1f}")
                except:
                    widget.setText("--")