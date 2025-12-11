import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QStackedWidget, QMessageBox)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QFont, QKeyEvent

from .components.status_bar import StatusBar

from src.services.logging_service import get_logging_service, LogLevel, LogCategory
from src.services.video_service import get_video_service
from src.services.opc_service import get_opc_service
from src.services.data_service import get_data_service
from config.config_system import config_manager  # [新增] 导入配置管理器以便遍历相机


class FoamMonitoringSystem(QMainWindow):
    """铅浮选监测系统主窗口"""

    def __init__(self):
        super().__init__()
        self.logger = get_logging_service()
        self.setup_ui()
        self.setup_connections()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_F5:
            self.reload_qss()
            event.accept()
        else:
            super().keyPressEvent(event)

    def load_stylesheet(self):
        try:
            with open("resources/styles/diy.qss", "r", encoding="utf-8") as f:
                stylesheet = f.read()
                self.setStyleSheet(stylesheet)
        except FileNotFoundError:
            self.logger.warning("样式文件未找到", "SYSTEM")

    def reload_qss(self):
        self.load_stylesheet()
        self.logger.info("reload qss", "SYSTEM")

    def setup_ui(self):
        self.setWindowTitle("铅浮选过程工况智能监测与控制系统")
        self.setGeometry(0, 0, 1920, 1000)
        self.setWindowIcon(QIcon("resources/icons/icon.png"))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        left_widget = self.create_left_panel()
        main_layout.addWidget(left_widget, 70)

        right_widget = self.create_right_panel()
        main_layout.addWidget(right_widget, 30)

        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)

    def create_left_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.left_stack = QStackedWidget()

        from .components.video_widget import VideoDisplayWidget
        self.video_page = VideoDisplayWidget()
        self.left_stack.addWidget(self.video_page)

        from .components.tank_widget import TankVisualizationWidget
        self.control_page = TankVisualizationWidget()
        self.left_stack.addWidget(self.control_page)

        layout.addWidget(self.left_stack)
        return widget

    def create_right_panel(self):
        from .components.control_panel import ControlPanel
        self.control_panel = ControlPanel()
        return self.control_panel

    def setup_connections(self):
        """设置信号连接"""
        self.control_panel.tab_changed.connect(self.on_tab_changed)

        # 1. 连接 OPC 状态 -> 状态栏
        opc_service = get_opc_service()
        opc_worker = opc_service.get_worker()
        if opc_worker:
            opc_worker.status_changed.connect(self.status_bar.update_opc_status)

        # 2. [新增] 连接 相机状态 -> 状态栏
        video_service = get_video_service()
        camera_configs = config_manager.get_camera_configs()

        # 遍历所有配置的相机
        for cam_config in camera_configs:
            worker = video_service.get_worker(cam_config.camera_index)
            if worker:
                # 连接每个相机的状态信号到状态栏的统一处理槽
                worker.status_changed.connect(self.status_bar.update_camera_status)

        self.setup_timers()

    def setup_timers(self):
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self.update_business_data)
        self.data_timer.start(1000)

        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_system_status)
        self.status_timer.start(5000)

    def on_tab_changed(self, index):
        tab_names = ["monitoring", "control", "history", "settings"]
        current_tab = tab_names[index] if index < len(tab_names) else "unknown"

        if current_tab == "control":
            self.left_stack.setCurrentWidget(self.control_page)
        else:
            self.left_stack.setCurrentWidget(self.video_page)

        self.logger.info(f"切换到{current_tab}界面")

    def update_business_data(self):
        try:
            if hasattr(self, 'status_bar'):
                self.status_bar.update_display()
        except Exception as e:
            self.logger.error(f"Data update error: {e}", "SYSTEM")

    def update_system_status(self):
        self.status_bar.update_time()

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            '系统退出',
            '确定要退出铅浮选监控系统吗？\n所有后台服务（视频/OPC）将停止运行。',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.logger.info("用户确认退出系统", "SYSTEM")

            if hasattr(self, 'data_timer') and self.data_timer.isActive():
                self.data_timer.stop()
            if hasattr(self, 'status_timer') and self.status_timer.isActive():
                self.status_timer.stop()

            get_video_service().cleanup()
            get_opc_service().cleanup()
            get_data_service().stop()

            event.accept()
        else:
            event.ignore()