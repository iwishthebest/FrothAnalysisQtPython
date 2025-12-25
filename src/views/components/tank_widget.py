import math
import random
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QDoubleSpinBox, QComboBox, QLineEdit,
                               QFrame, QGraphicsDropShadowEffect, QScrollArea)
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
        0: [  # 铅快粗槽
            ('qkc_dinghuangyao1', '丁黄药1'), ('qkc_dinghuangyao2', '丁黄药2'),
            ('qkc_yiliudan1', '乙硫氮1'), ('qkc_yiliudan2', '乙硫氮2'),
            ('qkc_shihui', '石灰'), ('qkc_5_you', '2#油')
        ],
        1: [  # 铅精一槽
            ('qkj1_dinghuangyao', '丁黄药'), ('qkj1_yiliudan', '乙硫氮'),
            ('qkj1_shihui', '石灰')
        ],
        2: [  # 铅精二槽
            ('qkj2_yiliudan', '乙硫氮'), ('qkj2_shihui', '石灰'),
            ('qkj2_dinghuangyao', '丁黄药')
        ],
        3: [  # 铅精三槽
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

        # 2. 核心可视化区域 (添加滚动区域以适应垂直高度增加)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("background: transparent;")

        scroll_content = QWidget()
        self.tanks_layout = QHBoxLayout(scroll_content)
        self.tanks_layout.setSpacing(0)
        self.tanks_layout.setContentsMargins(10, 10, 10, 10)
        # 顶部对齐，避免因卡片高度不一致导致的错位
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
        self.setFixedWidth(40)
        self.setSizePolicy(self.sizePolicy().Policy.Fixed, self.sizePolicy().Policy.Preferred)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # 调整高度以匹配槽体视觉重心
        # 这里的绝对坐标可能需要根据 SingleTankWidget 的头部高度微调
        # 假设头部约40px，槽体约120px，管道大概在 40 + 30 (泡沫) 和 40 + 90 (矿浆)
        froth_y = 70
        pulp_y = 130

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
        s = 5
        pts = [QPointF(x, y), QPointF(x - s, y - s), QPointF(x - s, y + s)] if direction == "right" else \
            [QPointF(x, y), QPointF(x + s, y - s), QPointF(x + s, y + s)]
        painter.drawPolygon(pts)


class TankGraphicWidget(QWidget):
    """槽体图形"""

    def __init__(self, base_color_hex, parent=None):
        super().__init__(parent)
        self.base_color = QColor(base_color_hex)
        self.water_level = 0.6
        self.setMinimumSize(120, 140)

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
        painter.drawLine(int(shaft_x), int(tank_rect.top() - 5), int(shaft_x), int(tank_rect.bottom() - 25))

        painter.save()
        painter.translate(shaft_x, tank_rect.bottom() - 25)
        painter.scale(1.0, 0.3)
        painter.rotate(self.angle)
        painter.setPen(QPen(QColor("#333"), 1))
        painter.setBrush(QColor("#7f8c8d"))
        painter.drawRect(-25, -3, 50, 6)
        painter.drawRect(-3, -25, 6, 50)
        painter.restore()


class SingleTankWidget(QFrame):
    """
    单个槽体卡片 - 垂直布局，四块监测区域
    """

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
                border: 1px solid #e0e0e0;
            }
            #TankCard:hover {
                border: 1px solid #3498db;
                background-color: #fbfbfb;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)

        self.setFixedWidth(300)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 12, 10, 15)
        main_layout.setSpacing(8)

        # 1. 头部
        header = QHBoxLayout()
        name_lbl = QLabel(self.config["name"])
        name_lbl.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {self.config['color']};")

        self.status_led = QLabel()
        self.status_led.setFixedSize(10, 10)
        self.status_led.setStyleSheet("background-color: #2ecc71; border-radius: 5px;")
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
        monitor_layout.setSpacing(8)
        monitor_layout.setContentsMargins(0, 5, 0, 5)

        # --- 块1: 药剂流量 (列表) ---
        reagent_panel = self._create_reagent_block()
        monitor_layout.addWidget(reagent_panel)

        # --- 块2: 液位监测 (无设定，只读) ---
        level_panel = self._create_level_block()
        monitor_layout.addWidget(level_panel)

        # --- 块3: 充气量 (预留) ---
        air_panel = self._create_data_block("充气量 (m³/min)", "air", "0.00", "#16a085")
        monitor_layout.addWidget(air_panel)

        # --- 块4: 冲水量 (预留) ---
        water_panel = self._create_data_block("冲水量 (L/min)", "water", "0.0", "#2980b9")
        monitor_layout.addWidget(water_panel)

        main_layout.addLayout(monitor_layout)
        main_layout.addStretch()

    def _create_panel_frame(self):
        """通用面板背景样式"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #f9f9fa;
                border-radius: 4px;
                border: 1px solid #eef0f2;
            }
        """)
        return frame

    def _create_reagent_block(self):
        """块1: 药剂流量列表"""
        frame = self._create_panel_frame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        title = QLabel("药剂流量 (ml/min)")
        title.setStyleSheet("font-weight: bold; font-size: 11px; color: #555; border:none;")
        layout.addWidget(title)

        # 药剂列表容器 (Grid布局对齐名称和数值)
        items_layout = QGridLayout()
        items_layout.setVerticalSpacing(4)
        items_layout.setHorizontalSpacing(10)
        items_layout.setColumnStretch(1, 1)  # 数值列拉伸

        for i, (key, name) in enumerate(self.reagents):
            lbl = QLabel(name)
            lbl.setStyleSheet("font-size: 11px; color: #666; border:none;")
            lbl.setToolTip(key)

            val_display = QLabel("0.0")
            val_display.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            val_display.setStyleSheet("""
                background: #34495e; color: #f1c40f; 
                border-radius: 2px;
                font-family: 'Consolas'; font-size: 11px; font-weight: bold;
                padding: 2px 4px;
            """)
            self.reagent_widgets[key] = val_display

            items_layout.addWidget(lbl, i, 0)
            items_layout.addWidget(val_display, i, 1)

        layout.addLayout(items_layout)
        return frame

    def _create_level_block(self):
        """块2: 液位监测 (纯显示)"""
        frame = self._create_panel_frame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)

        title = QLabel("液位")
        title.setStyleSheet("font-weight: bold; font-size: 11px; color: #555; border:none;")

        # 实时值
        self.lbl_level_real = QLabel("1.20")
        self.lbl_level_real.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_level_real.setStyleSheet("""
            background: #34495e; color: #2ecc71; 
            border-radius: 3px; font-family: 'Consolas'; 
            font-size: 14px; font-weight: bold; padding: 2px 6px;
            border:none;
        """)

        unit = QLabel("m")
        unit.setStyleSheet("color: #888; font-size: 10px; border:none;")

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.lbl_level_real)
        layout.addWidget(unit)
        return frame

    def _create_data_block(self, title_text, obj_name, default_val, value_color):
        """通用数据块 (空气/水)"""
        frame = self._create_panel_frame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)

        title = QLabel(title_text.split("(")[0])  # 只取标题
        title.setStyleSheet("font-weight: bold; font-size: 11px; color: #555; border:none;")

        val_lbl = QLabel(default_val)
        val_lbl.setObjectName(f"val_{obj_name}")
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        val_lbl.setStyleSheet(f"""
            background: #34495e; color: {value_color};
            border-radius: 3px; font-family: 'Consolas'; 
            font-size: 14px; font-weight: bold; padding: 2px 6px;
            border:none;
        """)

        # 提取单位
        unit_text = title_text.split("(")[1].replace(")", "") if "(" in title_text else ""
        unit = QLabel(unit_text)
        unit.setStyleSheet("color: #888; font-size: 10px; border:none;")

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(val_lbl)
        layout.addWidget(unit)

        return frame

    def update_data(self, data):
        # 液位更新
        if 'level' in data:
            try:
                val = float(data['level'])
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