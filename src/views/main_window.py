"""主窗口实现 - 应用程序的主界面框架"""
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QStackedWidget)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon

from .pages.video_preview_page import VideoPreviewPage
from .pages.control_parameters_page import ControlParametersPage
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
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        # 左侧堆叠窗口（70%宽度）
        self.left_stack = QStackedWidget()
        self.left_stack.addWidget(VideoPreviewPage())         # 视频预览页面
        self.left_stack.addWidget(ControlParametersPage())    # 控制参数页面
        main_layout.addWidget(self.left_stack, 70)

        # 右侧区域（30%宽度）
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # 控制面板
        self.control_panel = ControlPanel()
        right_layout.addWidget(self.control_panel, 70)

        # 状态栏
        self.status_bar = StatusBar()
        right_layout.addWidget(self.status_bar, 30)

        main_layout.addWidget(right_widget, 30)

    def _setup_timers(self):
        """设置定时器用于数据更新"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(1000)  # 1秒更新一次

    def _update_display(self):
        """更新界面显示"""
        # 这里添加数据更新逻辑
        pass

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        self.update_timer.stop()
        super().closeEvent(event)