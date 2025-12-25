import math
import random
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QDoubleSpinBox, QComboBox, QLineEdit,
                               QFrame, QGraphicsDropShadowEffect, QScrollArea,
                               QSizePolicy)
from PySide6.QtCore import Qt, Signal, QRectF, QTimer, QPointF, Slot
from PySide6.QtGui import (QPainter, QColor, QPen, QBrush, QFont,
                           QPainterPath, QLinearGradient, QPolygonF)

from src.services.opc_service import get_opc_service
from src.services.data_service import get_data_service


class TankVisualizationWidget(QWidget):
    """
    浮选槽可视化组件 - 工业HMI风格 (精致图标版)
    特性：动态搅拌、气泡粒子、自适应管道、带图标的现代化仪表盘
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
        self.setup_data_connection()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 1. 顶部标题
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(10, 0, 10, 0)

        title_label = QLabel("浮选槽串联监控 (正浮选流程)")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
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

        # 外层垂直布局：负责垂直居中
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        # 内容容器：负责水平排列
        tanks_container = QWidget()
        self.tanks_layout = QHBoxLayout(tanks_container)
        self.tanks_layout.setContentsMargins(10, 0, 10, 0)
        self.tanks_layout.setSpacing(0)
        self.tanks_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        scroll_layout.addWidget(tanks_container)

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
        lbl.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(indicator)
        layout.addWidget(lbl)

    def setup_data_connection(self):
        try:
            opc_service = get_opc_service()
            worker = opc_service.get_worker()
            if worker:
                worker.data_updated.connect(self.update_tank_data)
        except Exception as e:
            print(f"TankWidget connection error: {e}")

    @Slot(dict)
    def update_tank_data(self, data):
        for tank in self.tank_widgets:
            tank.update_data(data)


class PipeConnectionWidget(QWidget):
    """连接管道 - 自适应"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(15)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(300)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # [调整] 对齐坐标优化，对齐槽体图形
        froth_y = 90  # 泡沫流
        pulp_y = 205  # 矿浆流

        # 泡沫流 (右)
        painter.setPen(QPen(QColor("#f39c12"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(0, froth_y, w, froth_y)
        self._draw_arrow(painter, w / 2, froth_y, "right", "#f39c12")

        # 矿浆流 (左)
        painter.setPen(QPen(QColor("#95a5a6"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(0, pulp_y, w, pulp_y)
        self._draw_arrow(painter, w / 2, pulp_y, "left", "#95a5a6")

    def _draw_arrow(self, painter, x, y, direction, color):
        painter.setBrush(QBrush(QColor(color)))
        painter.setPen(Qt.PenStyle.NoPen)
        s = 6
        pts = [QPointF(x, y), QPointF(x - s, y - s), QPointF(x - s, y + s)] if direction == "right" else \
            [QPointF(x, y), QPointF(x + s, y - s), QPointF(x + s, y + s)]
        painter.drawPolygon(pts)


class TankGraphicWidget(QWidget):
    """槽体图形"""

    def __init__(self, base_color_hex, parent=None):
        super().__init__(parent)
        self.base_color = QColor(base_color_hex)
        self.water_level = 0.6
        self.setMinimumSize(150, 200)

        self.angle = 0
        self.bubbles = []
        for _ in range(15): self._spawn_bubble()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_animation)
        self.timer.start(50)

    def _spawn_bubble(self):
        self.bubbles.append(
            [random.uniform(0.2, 0.8), random.uniform(0.5, 0.9), random.uniform(0.005, 0.015), random.uniform(3, 6)])

    def _update_animation(self):
        self.angle = (self.angle + 12) % 360
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

        tank_rect = QRectF(10, 10, w - 20, h - 20)
        fill_height = tank_rect.height() * self.water_level
        liquid_y = tank_rect.bottom() - fill_height

        # 1. 槽体
        path = QPainterPath()
        path.moveTo(tank_rect.left(), tank_rect.top())
        path.lineTo(tank_rect.left(), tank_rect.bottom() - 15)
        path.quadTo(tank_rect.left(), tank_rect.bottom(), tank_rect.left() + 15, tank_rect.bottom())
        path.lineTo(tank_rect.right() - 15, tank_rect.bottom())
        path.quadTo(tank_rect.right(), tank_rect.bottom(), tank_rect.right(), tank_rect.bottom() - 15)
        path.lineTo(tank_rect.right(), tank_rect.top())

        painter.fillPath(path, QBrush(QColor("#f4f6f7")))
        painter.setPen(QPen(QColor("#bdc3c7"), 3))
        painter.drawPath(path)

        # 2. 液体
        liquid_rect = QRectF(tank_rect.left() + 3, liquid_y, tank_rect.width() - 6, fill_height - 3)
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

        # 3. 泡沫层
        froth_h = 14
        froth_y_pos = liquid_y - froth_h + 3
        froth_rect = QRectF(tank_rect.left() + 2, froth_y_pos, tank_rect.width() - 4, froth_h)
        froth_grad = QLinearGradient(froth_rect.topLeft(), froth_rect.bottomLeft())
        froth_grad.setColorAt(0, QColor(255, 255, 255, 230))
        froth_grad.setColorAt(1, self.base_color.lighter(160))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(froth_grad)
        painter.drawRoundedRect(froth_rect, 4, 4)

        # 4. 搅拌器
        shaft_x = w / 2
        painter.setPen(QPen(QColor("#555"), 4))
        painter.drawLine(int(shaft_x), int(tank_rect.top() - 10), int(shaft_x), int(tank_rect.bottom() - 30))

        painter.save()
        painter.translate(shaft_x, tank_rect.bottom() - 30)
        painter.scale(1.0, 0.3)
        painter.rotate(self.angle)
        painter.setPen(QPen(QColor("#333"), 1))
        painter.setBrush(QColor("#7f8c8d"))
        painter.drawRect(-30, -4, 60, 8)
        painter.drawRect(-4, -30, 8, 60)
        painter.restore()


class SingleTankWidget(QFrame):
    """
    单个槽体卡片 - 紧凑型
    """

    MAX_REAGENT_COUNT = 6

    def __init__(self, config, reagents, parent=None):
        super().__init__(parent)
        self.config = config
        self.reagents = reagents
        self.reagent_widgets = {}
        self.data_mapping = get_data_service().reagent_mapping
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

        self.setFixedWidth(245)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 10, 6, 8)
        main_layout.setSpacing(6)

        # 1. 头部
        header = QHBoxLayout()
        name_lbl = QLabel(self.config["name"])
        name_lbl.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {self.config['color']};")

        self.status_led = QLabel()
        self.status_led.setFixedSize(8, 8)
        self.status_led.setStyleSheet("background-color: #2ecc71; border-radius: 4px;")
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

        # --- 块1: 药剂流量 ---
        reagent_panel = self._create_reagent_block()
        monitor_layout.addWidget(reagent_panel)

        # --- 块2: 液位监测 ---
        level_panel = self._create_level_block()
        monitor_layout.addWidget(level_panel)

        # --- 块3: 充气量 ---
        # 浅青色背景
        air_panel = self._create_data_block("充气量 (m³/min)", "air", "0.00", "#16a085", "#e8f8f5", "💨")
        monitor_layout.addWidget(air_panel)

        # --- 块4: 冲水量 ---
        # 浅蓝色背景
        water_panel = self._create_data_block("冲水量 (L/min)", "water", "0.0", "#3498db", "#eef7fd", "💧")
        monitor_layout.addWidget(water_panel)

        main_layout.addLayout(monitor_layout)

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
        """块1: 药剂流量列表 (美化版)"""
        frame = self._create_panel_frame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)

        # [图标] 药剂流量
        title = QLabel("  🧪 药剂流量 (ml/min)")
        title.setStyleSheet("font-weight: bold; font-size: 12px; color: #444; border:none;")
        layout.addWidget(title)

        items_layout = QGridLayout()
        # [调整] 增加垂直间距，更宽松
        items_layout.setVerticalSpacing(12)
        items_layout.setHorizontalSpacing(5)
        items_layout.setColumnStretch(0, 1)

        for i in range(self.MAX_REAGENT_COUNT):
            if i < len(self.reagents):
                key, name = self.reagents[i]

                # 名称
                lbl = QLabel(name)
                lbl.setStyleSheet("font-size: 12px; color: #555; font-weight: 500; border:none;")
                full_tag = self.data_mapping.get(key, key)
                lbl.setToolTip(full_tag)

                # 数值显示 (胶囊风格)
                val_display = QLabel("0.0")
                val_display.setFixedWidth(55)  # 固定宽度
                val_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
                val_display.setStyleSheet("""
                    background-color: #f0f2f5; 
                    color: #2c3e50; 
                    border: 1px solid #dcdfe6;
                    border-radius: 3px;
                    font-family: 'Consolas'; 
                    font-size: 12px; 
                    font-weight: bold;
                    padding: 1px 0px;
                """)
                self.reagent_widgets[key] = val_display

                items_layout.addWidget(lbl, i, 0)
                items_layout.addWidget(val_display, i, 1)
            else:
                lbl = QLabel(" ")
                lbl.setStyleSheet("font-size: 12px; border:none;")
                val = QLabel(" ")
                val.setStyleSheet("font-size: 12px; border:none; padding: 1px 0px;")

                items_layout.addWidget(lbl, i, 0)
                items_layout.addWidget(val, i, 1)

        layout.addLayout(items_layout)
        return frame

    def _create_level_block(self):
        """块2: 液位监测"""
        frame = self._create_panel_frame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)

        # [图标] 液位
        title = QLabel("  📏 液位")
        title.setStyleSheet("font-weight: bold; font-size: 12px; color: #444; border:none;")

        self.lbl_level_real = QLabel("1.20")
        self.lbl_level_real.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_level_real.setStyleSheet("""
            background-color: #e8f5e9; 
            color: #2ecc71; 
            border: 1px solid #c8e6c9;
            border-radius: 4px;
            font-family: 'Consolas'; 
            font-size: 16px; 
            font-weight: bold; 
            padding: 2px 8px;
            min-width: 60px;
        """)

        unit = QLabel("m")
        unit.setStyleSheet("color: #888; font-size: 11px; border:none;")

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.lbl_level_real)
        layout.addWidget(unit)
        return frame

    def _create_data_block(self, title_text, obj_name, default_val, text_color, bg_color, icon=""):
        """通用数据块"""
        frame = self._create_panel_frame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)

        # [图标] 动态
        title = QLabel(f"  {icon} {title_text.split('(')[0]}")
        title.setStyleSheet("font-weight: bold; font-size: 12px; color: #444; border:none;")

        val_lbl = QLabel(default_val)
        val_lbl.setObjectName(f"val_{obj_name}")
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val_lbl.setStyleSheet(f"""
            background-color: {bg_color}; 
            color: {text_color}; 
            border: 1px solid {text_color}40;
            border-radius: 4px;
            font-family: 'Consolas'; 
            font-size: 16px; 
            font-weight: bold; 
            padding: 2px 8px;
            min-width: 60px;
        """)

        unit_text = title_text.split("(")[1].replace(")", "") if "(" in title_text else ""
        unit = QLabel(unit_text)
        unit.setStyleSheet("color: #888; font-size: 11px; border:none;")

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(val_lbl)
        layout.addWidget(unit)

        return frame

    def update_data(self, data):
        # 液位更新 (兼容逻辑)
        if 'level' in data:
            try:
                val = float(data['level'])
                self.lbl_level_real.setText(f"{val:.2f}")
                self.tank_graphic.set_water_level(val / 2.5)
            except:
                pass

        # 药剂更新
        for short_key, widget in self.reagent_widgets.items():
            full_tag = self.data_mapping.get(short_key)

            if full_tag and full_tag in data:
                tag_data = data[full_tag]
                val = tag_data.get('value') if isinstance(tag_data, dict) else tag_data

                try:
                    if val is not None:
                        widget.setText(f"{float(val):.1f}")
                    else:
                        widget.setText("--")
                except (ValueError, TypeError):
                    widget.setText("ERR")