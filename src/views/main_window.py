"""
主窗口实现 - 应用程序的主界面框架
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QTabWidget, QStackedWidget)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon

from .components.video_widget import VideoWidget
from .components.tank_widget import TankWidget
from .components.control_panel import ControlPanel
from .components.status_bar import StatusBar


class FoamMonitoringSystem(QMainWindow):
    """铅浮选监测系统主窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("铅浮选过程工况智能监测与控制系统")
        self.setGeometry(100, 100, 1400, 900)
        self.setWindowIcon(QIcon("resources/icons/icon.png"))

        self._setup_ui()
        self._setup_timers()

    def _setup_ui(self):
        """初始化用户界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        # 左侧区域（70%宽度）- 视频监控和浮选槽显示
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 视频监控区域
        video_group = QWidget()
        video_layout = QHBoxLayout(video_group)
        video_layout.addWidget(VideoWidget("铅快粗泡沫相机", "rtsp://192.168.1.101"))
        video_layout.addWidget(VideoWidget("铅精一泡沫相机", "rtsp://192.168.1.102"))
        left_layout.addWidget(video_group, 40)  # 40%高度

        # 浮选槽显示区域
        tank_group = QWidget()
        tank_layout = QHBoxLayout(tank_group)
        tank_layout.addWidget(TankWidget("铅快粗槽", 1.2, 50))
        tank_layout.addWidget(TankWidget("铅精一槽", 1.3, 45))
        tank_layout.addWidget(TankWidget("铅精二槽", 1.4, 40))
        tank_layout.addWidget(TankWidget("铅精三槽", 1.5, 35))
        left_layout.addWidget(tank_group, 60)  # 60%高度

        main_layout.addWidget(left_widget, 70)  # 70%宽度

        # 右侧区域（30%宽度）- 控制面板和状态信息
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # 控制面板
        control_panel = ControlPanel()
        right_layout.addWidget(control_panel, 70)  # 70%高度

        # 状态栏
        status_bar = StatusBar()
        right_layout.addWidget(status_bar, 30)  # 30%高度

        main_layout.addWidget(right_widget, 30)  # 30%宽度

    def _setup_timers(self):
        """设置定时器用于数据更新"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(1000)  # 1秒更新一次

    def _update_display(self):
        """更新界面显示"""
        # 这里可以添加数据更新逻辑
        pass

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        self.update_timer.stop()
        super().closeEvent(event)
