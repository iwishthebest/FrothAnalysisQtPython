"""浮选槽图形显示组件"""
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QBrush, QPen, QColor
from PySide6.QtCore import Qt


class TankGraphicWidget(QWidget):
    def __init__(self, color, tank_id, parent=None):
        super().__init__(parent)
        self.tank_color = color
        self.tank_id = tank_id
        self.level = 0.7  # 初始液位比例(0-1)
        self.setMinimumHeight(120)

    def set_level(self, level):
        """设置液位高度(0-1范围)"""
        self.level = max(0, min(1, level))  # 限制范围
        self.update()  # 触发重绘

    def paintEvent(self, event):
        """绘制浮选槽图形"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制槽体
        rect = self.rect()
        tank_rect = rect.adjusted(20, 10, -20, -10)  # 内边距

        # 槽体边框
        pen = QPen(QColor(self.tank_color), 2)
        painter.setPen(pen)
        painter.drawRect(tank_rect)

        # 绘制液位
        liquid_height = tank_rect.height() * self.level
        liquid_rect = tank_rect.adjusted(1, tank_rect.height() - liquid_height, -1, 0)
        brush = QBrush(QColor(self.tank_color).lighter(150))
        painter.setBrush(brush)
        painter.drawRect(liquid_rect)