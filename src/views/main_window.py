import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QStackedWidget)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QFont

from .components.status_bar import StatusBar

from src.services.logging_service import get_logging_service, LogLevel, LogCategory


class FoamMonitoringSystem(QMainWindow):
    """铅浮选监测系统主窗口"""

    def __init__(self):
        super().__init__()
        self.logger = get_logging_service()
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("铅浮选过程工况智能监测与控制系统")
        self.setGeometry(0, 0, 1920, 1000)
        self.setWindowIcon(QIcon("resources/icons/icon.png"))

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        # 左侧区域 - 视频监控和浮选槽可视化 (70%)
        left_widget = self.create_left_panel()
        main_layout.addWidget(left_widget, 70)

        # 右侧区域 - 控制面板 (30%)
        right_widget = self.create_right_panel()
        main_layout.addWidget(right_widget, 30)

        # 状态栏
        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)

    def create_left_panel(self):
        """创建左侧面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 堆叠窗口管理不同界面
        self.left_stack = QStackedWidget()

        # 视频预览页面
        from .components.video_widget import VideoDisplayWidget
        self.video_page = VideoDisplayWidget()
        self.left_stack.addWidget(self.video_page)

        # 控制参数页面
        from .components.tank_widget import TankVisualizationWidget
        self.control_page = TankVisualizationWidget()
        self.left_stack.addWidget(self.control_page)

        layout.addWidget(self.left_stack)
        return widget

    def create_right_panel(self):
        """创建右侧控制面板"""
        from .components.control_panel import ControlPanel
        self.control_panel = ControlPanel()
        return self.control_panel

    def setup_connections(self):
        """设置信号连接"""
        # 连接控制面板的选项卡切换信号
        self.control_panel.tab_changed.connect(self.on_tab_changed)

        # 设置定时器
        self.setup_timers()

    def setup_timers(self):
        """设置定时器"""
        # 数据更新定时器
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self.update_data)
        self.data_timer.start(1000)  # 1秒更新

        # 状态更新定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # 5秒更新

    def on_tab_changed(self, index):
        """处理选项卡切换"""
        tab_names = ["monitoring", "control", "history", "settings"]
        current_tab = tab_names[index] if index < len(tab_names) else "unknown"

        # 根据选项卡切换左侧界面
        if current_tab == "control":
            self.left_stack.setCurrentWidget(self.control_page)
        else:
            self.left_stack.setCurrentWidget(self.video_page)

        self.logger.info(f"切换到{current_tab}界面")

    def update_data(self):
        """更新数据"""
        try:
            # 更新视频显示
            self.video_page.update_display()

            # 更新监控页面数据
            self.control_panel.monitoring_page.update_data()

            # 更新状态栏
            self.status_bar.update_display()

        except Exception as e:
            self.logger.info(f"更新数据时出错: {e}")

    def update_status(self):
        """更新系统状态"""
        self.status_bar.update_time()

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        self.data_timer.stop()
        self.status_timer.stop()
        self.logger.info("系统已关闭")
        super().closeEvent(event)