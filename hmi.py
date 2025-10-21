import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPalette, QColor, QLinearGradient, QPainter


class TechWidget(QFrame):
    """科技风控件基类"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "tech-widget")


class DigitalDisplay(QLabel):
    """数码管风格显示控件"""

    def __init__(self, text="0", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setProperty("class", "digital-display")


class TechButton(QPushButton):
    """科技风按钮"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setProperty("class", "tech-button")


class TechHMI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("科技风 HMI 界面")
        self.resize(1200, 800)

        self.setup_ui()

    def setup_ui(self):
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)

        # 左侧控制面板
        left_panel = self.create_control_panel()
        main_layout.addWidget(left_panel, 1)

        # 右侧数据显示面板
        right_panel = self.create_data_panel()
        main_layout.addWidget(right_panel, 2)

    def create_control_panel(self):
        panel = TechWidget()
        panel.setMaximumWidth(300)
        layout = QVBoxLayout(panel)

        # 标题
        title = QLabel("控制系统")
        title.setProperty("class", "control-title")
        layout.addWidget(title)

        # 控制按钮
        buttons = [
            ("启动系统", self.start_system),
            ("停止系统", self.stop_system),
            ("参数设置", self.open_settings),
            ("数据记录", self.toggle_logging),
            ("紧急停止", self.emergency_stop)
        ]

        for text, slot in buttons:
            btn = TechButton(text)
            btn.clicked.connect(slot)
            layout.addWidget(btn)

        layout.addStretch()
        return panel

    def create_data_panel(self):
        panel = TechWidget()
        layout = QVBoxLayout(panel)

        # 数据标题
        data_title = QLabel("实时数据监控")
        data_title.setProperty("class", "data-title")
        layout.addWidget(data_title)

        # 创建数据网格
        grid_layout = QHBoxLayout()

        # 左侧数据列
        left_data = QVBoxLayout()
        right_data = QVBoxLayout()

        # 模拟数据项
        data_items = [
            ("温度", "75.3°C", "#ff5555"),
            ("压力", "101.3 kPa", "#5555ff"),
            ("流量", "12.5 L/min", "#55ff55"),
            ("转速", "1500 rpm", "#ffff55"),
            ("电压", "380 V", "#ff55ff"),
            ("电流", "25.3 A", "#55ffff")
        ]

        for i, (name, value, color) in enumerate(data_items):
            data_widget = self.create_data_item(name, value, color)
            if i % 2 == 0:
                left_data.addWidget(data_widget)
            else:
                right_data.addWidget(data_widget)

        grid_layout.addLayout(left_data)
        grid_layout.addLayout(right_data)
        layout.addLayout(grid_layout)

        # 状态显示
        status_label = QLabel("系统运行正常")
        status_label.setProperty("class", "status-label")
        layout.addWidget(status_label)

        return panel

    def create_data_item(self, name, value, color):
        widget = QWidget()
        # 动态样式保留在代码中
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(20, 30, 50, 0.6);
                border: 1px solid {color};
                border-radius: 8px;
                margin: 5px;
                padding: 5px;
            }}
        """)

        layout = QVBoxLayout(widget)

        name_label = QLabel(name)
        name_label.setStyleSheet("color: #aaaaaa; font-size: 12px;")

        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            color: {color}; 
            font-size: 16px; 
            font-weight: bold;
        """)

        layout.addWidget(name_label)
        layout.addWidget(value_label)

        return widget

    # 槽函数
    def start_system(self):
        print("系统启动")

    def stop_system(self):
        print("系统停止")

    def open_settings(self):
        print("打开设置")

    def toggle_logging(self):
        print("切换数据记录")

    def emergency_stop(self):
        print("紧急停止")


def load_stylesheet(filename):
    """加载CSS文件"""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        print(f"警告: 样式文件 {filename} 未找到")
        return ""


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 设置应用字体
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # 加载CSS样式
    stylesheet = load_stylesheet("styles.qss")
    app.setStyleSheet(stylesheet)

    window = TechHMI()
    window.show()
    sys.exit(app.exec())
