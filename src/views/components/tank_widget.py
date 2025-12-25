import math
import random
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QDoubleSpinBox, QComboBox,
                               QFrame, QGraphicsDropShadowEffect, QGridLayout)
from PySide6.QtCore import Qt, Signal, QRectF, QTimer, QPointF, QSize
from PySide6.QtGui import (QPainter, QColor, QPen, QBrush, QFont,
                           QPainterPath, QLinearGradient, QRadialGradient, QPolygonF)


class TankVisualizationWidget(QWidget):
    """
    浮选槽可视化组件 - 工业HMI风格
    包含：动态搅拌动画、气泡粒子效果、实体管道连接、仪表盘式读数
    """

    # 信号定义 (保持原有接口兼容)
    level_changed = Signal(int, float)
    dosing_changed = Signal(int, float)
    reagent_changed = Signal(int, str)

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

        title_label = QLabel("浮选机组串联监控 (Flotation Circuit)")
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
            {"id": 0, "name": "铅快粗槽", "type": "粗选作业 (Rougher)", "color": "#3498db"},
            {"id": 1, "name": "铅精一槽", "type": "精选一 (Cleaner 1)", "color": "#2ecc71"},
            {"id": 2, "name": "铅精二槽", "type": "精选二 (Cleaner 2)", "color": "#e74c3c"},
            {"id": 3, "name": "铅精三槽", "type": "精选三 (Cleaner 3)", "color": "#9b59b6"}
        ]

        for i, config in enumerate(tank_configs):
            # 1. 添加槽体
            tank = SingleTankWidget(config)
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
    绘制精矿(上)和尾矿(下)的流向
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(60)  # 管道长度
        self.setSizePolicy(self.sizePolicy().Policy.Fixed, self.sizePolicy().Policy.Preferred)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # 相对高度定位 (需要与 SingleTankWidget 的液体/泡沫高度大致对齐)
        # 假设槽体图形在卡片中间，我们需要目测或计算对齐位置
        # 这里采用相对比例估算

        froth_y = h * 0.45  # 泡沫流高度
        pulp_y = h * 0.65  # 矿浆流高度

        # 1. 绘制泡沫流 (向右 ->)
        froth_pen = QPen(QColor("#f39c12"), 3)
        froth_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(froth_pen)
        painter.drawLine(0, int(froth_y), w, int(froth_y))

        # 箭头
        self._draw_arrow(painter, w - 5, froth_y, direction="right", color="#f39c12")

        # 2. 绘制中矿/尾矿流 (向左 <-)
        pulp_pen = QPen(QColor("#95a5a6"), 3)  # 灰色管道
        pulp_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pulp_pen)
        painter.drawLine(0, int(pulp_y), w, int(pulp_y))

        # 箭头
        self._draw_arrow(painter, 5, pulp_y, direction="left", color="#95a5a6")

    def _draw_arrow(self, painter, x, y, direction="right", color="#000"):
        painter.setBrush(QBrush(QColor(color)))
        painter.setPen(Qt.PenStyle.NoPen)

        arrow_size = 6
        points = []
        if direction == "right":
            points = [
                QPointF(x, y),
                QPointF(x - arrow_size, y - arrow_size),
                QPointF(x - arrow_size, y + arrow_size)
            ]
        else:
            points = [
                QPointF(x, y),
                QPointF(x + arrow_size, y - arrow_size),
                QPointF(x + arrow_size, y + arrow_size)
            ]
        painter.drawPolygon(points)


class TankGraphicWidget(QWidget):
    """
    高保真浮选槽图形
    特性：
    1. 搅拌动画
    2. 气泡粒子系统
    3. 渐变色液体
    """

    def __init__(self, base_color_hex, parent=None):
        super().__init__(parent)
        self.base_color = QColor(base_color_hex)
        self.water_level = 0.6
        self.setMinimumSize(100, 140)

        # 动画相关
        self.angle = 0
        self.bubbles = []  # list of [x, y, speed, size]

        # 初始化气泡
        for _ in range(15):
            self._spawn_bubble()

        # 定时器刷新动画
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_animation)
        self.timer.start(50)  # 20 FPS

    def _spawn_bubble(self):
        """生成一个随机气泡"""
        # x: 0.1~0.9 (相对宽度), y: 0.8~1.0 (相对液体底部), speed: 0.005~0.02, size: 2~5
        self.bubbles.append([
            random.uniform(0.2, 0.8),  # x
            random.uniform(0.5, 0.9),  # y
            random.uniform(0.005, 0.015),  # speed
            random.uniform(2, 5)  # size
        ])

    def _update_animation(self):
        self.angle = (self.angle + 10) % 360

        # 更新气泡
        for b in self.bubbles:
            b[1] -= b[2]  # y 向上移动
            # 简单的左右摆动
            b[0] += math.sin(b[1] * 10) * 0.002

            # 如果到达液面(假设液面在 0.3 左右)，重置到底部
            liquid_top_ratio = 1.0 - self.water_level
            if b[1] < liquid_top_ratio:
                b[1] = random.uniform(0.8, 1.0)
                b[0] = random.uniform(0.2, 0.8)

        self.update()

    def set_water_level(self, level):
        # 限制在 0.2 ~ 0.9 之间，防止图形崩坏
        self.water_level = max(0.2, min(0.9, level))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # 绘制参数
        tank_rect = QRectF(10, 10, w - 20, h - 20)
        fill_height = tank_rect.height() * self.water_level
        liquid_y = tank_rect.bottom() - fill_height

        # 1. 绘制槽体外壳 (金属质感)
        path = QPainterPath()
        # U型底
        path.moveTo(tank_rect.left(), tank_rect.top())
        path.lineTo(tank_rect.left(), tank_rect.bottom() - 15)
        path.quadTo(tank_rect.left(), tank_rect.bottom(), tank_rect.left() + 15, tank_rect.bottom())
        path.lineTo(tank_rect.right() - 15, tank_rect.bottom())
        path.quadTo(tank_rect.right(), tank_rect.bottom(), tank_rect.right(), tank_rect.bottom() - 15)
        path.lineTo(tank_rect.right(), tank_rect.top())

        # 槽体背景(深灰)
        painter.fillPath(path, QBrush(QColor("#ecf0f1")))
        # 槽体边框
        painter.setPen(QPen(QColor("#7f8c8d"), 3))
        painter.drawPath(path)

        # 2. 绘制矿浆 (使用渐变色)
        liquid_rect = QRectF(tank_rect.left() + 3, liquid_y, tank_rect.width() - 6, fill_height - 3)

        # 裁剪区域，防止液体画出圆角槽体外
        painter.save()
        painter.setClipPath(path)

        # 液体渐变
        grad = QLinearGradient(liquid_rect.topLeft(), liquid_rect.bottomRight())
        grad.setColorAt(0, self.base_color.lighter(130))
        grad.setColorAt(1, self.base_color)
        painter.fillRect(liquid_rect, grad)

        # 3. 绘制气泡
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 150))
        for b in self.bubbles:
            bx = tank_rect.left() + b[0] * tank_rect.width()
            by = tank_rect.top() + b[1] * tank_rect.height()
            painter.drawEllipse(QPointF(bx, by), b[3], b[3])

        painter.restore()  # 恢复裁剪

        # 4. 绘制泡沫层 (Froth)
        froth_h = 15
        froth_rect = QRectF(tank_rect.left(), liquid_y - froth_h + 3, tank_rect.width(), froth_h * 1.5)
        froth_grad = QLinearGradient(froth_rect.topLeft(), froth_rect.bottomLeft())
        froth_grad.setColorAt(0, QColor("#ffffff"))
        froth_grad.setColorAt(1, self.base_color.lighter(150))

        # 泡沫波浪效果 (简单的圆角矩形代替)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(froth_grad)
        painter.drawRoundedRect(froth_rect, 5, 5)

        # 5. 绘制搅拌器 (Agitator)
        shaft_x = w / 2
        # 轴
        painter.setPen(QPen(QColor("#555"), 4))
        painter.drawLine(int(shaft_x), int(tank_rect.top() - 5), int(shaft_x), int(tank_rect.bottom() - 25))

        # 叶轮 (旋转动画)
        painter.save()
        painter.translate(shaft_x, tank_rect.bottom() - 25)
        # 透视效果，压扁y轴
        painter.scale(1.0, 0.4)
        painter.rotate(self.angle)

        painter.setPen(QPen(QColor("#333"), 2))
        painter.setBrush(QColor("#7f8c8d"))
        painter.drawRect(-25, -4, 50, 8)
        painter.drawRect(-4, -25, 8, 50)

        painter.restore()


class SingleTankWidget(QFrame):
    """
    单个槽体卡片
    包含：TankGraphicWidget, 仪表盘控制, 状态指示灯
    """

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._init_data()
        self.setup_ui()

    def _init_data(self):
        self.current_level = 1.2
        self.current_dosing = 50.0
        self.is_running = True

    def setup_ui(self):
        self.setObjectName("TankCard")
        # 现代卡片样式
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

        # 阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)

        self.setFixedWidth(240)
        # self.setFixedHeight(340)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 1. 头部：名称 + 状态灯
        header_layout = QHBoxLayout()

        name_vbox = QVBoxLayout()
        name_vbox.setSpacing(2)
        name_lbl = QLabel(self.config["name"])
        name_lbl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {self.config['color']};")
        type_lbl = QLabel(self.config["type"])
        type_lbl.setStyleSheet("font-size: 10px; color: #909399;")
        name_vbox.addWidget(name_lbl)
        name_vbox.addWidget(type_lbl)

        # 状态灯
        self.status_led = QLabel()
        self.status_led.setFixedSize(12, 12)
        self.update_status_led(True)  # 默认运行

        header_layout.addLayout(name_vbox)
        header_layout.addStretch()
        header_layout.addWidget(self.status_led)

        layout.addLayout(header_layout)

        # 2. 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #f0f0f0;")
        layout.addWidget(line)

        # 3. 槽体图形
        graphic_layout = QHBoxLayout()
        self.tank_graphic = TankGraphicWidget(self.config["color"])
        graphic_layout.addWidget(self.tank_graphic)
        layout.addLayout(graphic_layout)

        # 4. 控制面板 (Grid Layout)
        # 仿照工业仪表盘样式
        ctrl_layout = QGridLayout()
        ctrl_layout.setVerticalSpacing(8)

        # 液位
        lbl_lvl = QLabel("液位(m)")
        lbl_lvl.setStyleSheet("font-size: 11px; color: #606266;")
        self.spin_level = self._create_digital_spinbox(0.0, 3.0, 1.2, " m")
        self.spin_level.valueChanged.connect(self._on_level_changed)

        # 加药
        lbl_dos = QLabel("加药(ml)")
        lbl_dos.setStyleSheet("font-size: 11px; color: #606266;")
        self.spin_dosing = self._create_digital_spinbox(0, 500, 50, " ml")

        # 药剂
        lbl_rag = QLabel("药剂")
        lbl_rag.setStyleSheet("font-size: 11px; color: #606266;")
        self.combo_rag = QComboBox()
        self.combo_rag.addItems(["2#油", "丁黄药", "乙硫氮"])
        self.combo_rag.setStyleSheet("""
            QComboBox {
                border: 1px solid #dcdfe6; border-radius: 3px; 
                padding: 2px 5px; font-size: 11px; background: #f4f6f7;
            }
            QComboBox::drop-down { border: none; }
        """)

        ctrl_layout.addWidget(lbl_lvl, 0, 0)
        ctrl_layout.addWidget(self.spin_level, 0, 1)

        ctrl_layout.addWidget(lbl_dos, 1, 0)
        ctrl_layout.addWidget(self.spin_dosing, 1, 1)

        ctrl_layout.addWidget(lbl_rag, 2, 0)
        ctrl_layout.addWidget(self.combo_rag, 2, 1)

        layout.addLayout(ctrl_layout)

    def _create_digital_spinbox(self, min_val, max_val, val, suffix):
        """创建类似数码管显示的 SpinBox"""
        sb = QDoubleSpinBox()
        sb.setRange(min_val, max_val)
        sb.setValue(val)
        sb.setSuffix(suffix)
        sb.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)  # 隐藏上下按钮，纯数字显示
        sb.setAlignment(Qt.AlignmentFlag.AlignRight)
        sb.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #f0f9eb; /* 浅绿背景代表正常数值 */
                border: 1px solid #c2e7b0;
                border-radius: 3px;
                color: #2c3e50;
                font-family: 'Consolas', monospace;
                font-weight: bold;
                padding-right: 5px;
            }
            QDoubleSpinBox:focus {
                border: 1px solid #67c23a;
                background-color: #ffffff;
            }
        """)
        return sb

    def update_status_led(self, is_running):
        color = "#2ecc71" if is_running else "#95a5a6"  # 绿/灰
        self.status_led.setStyleSheet(f"""
            background-color: {color};
            border-radius: 6px;
            border: 1px solid #fff;
        """)
        self.status_led.setToolTip("运行中" if is_running else "已停止")

    def _on_level_changed(self, val):
        # 假设满量程为 2.5m
        ratio = val / 2.5
        self.tank_graphic.set_water_level(ratio)

    def update_data(self, data):
        """更新数据接口"""
        if 'level' in data:
            self.spin_level.setValue(float(data['level']))
        if 'dosing' in data:
            self.spin_dosing.setValue(float(data['dosing']))
        if 'reagent' in data:
            self.combo_rag.setCurrentText(str(data['reagent']))