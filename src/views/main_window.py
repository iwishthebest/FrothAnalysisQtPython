import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QStackedWidget, QMessageBox)  # [修改] 导入 QMessageBox
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QFont, QKeyEvent

from .components.status_bar import StatusBar

from src.services.logging_service import get_logging_service, LogLevel, LogCategory
from src.services.video_service import get_video_service
from src.services.opc_service import get_opc_service
from src.services.data_service import get_data_service


class FoamMonitoringSystem(QMainWindow):
    """铅浮选监测系统主窗口"""

    def __init__(self):
        super().__init__()
        self.logger = get_logging_service()
        self.setup_ui()
        self.setup_connections()

    def keyPressEvent(self, event: QKeyEvent):
        """重写键盘按下事件处理"""
        if event.key() == Qt.Key.Key_F5:
            # 按下F5键时重载QSS
            self.reload_qss()
            event.accept()
        else:
            super().keyPressEvent(event)

    def load_stylesheet(self):
        """加载样式表"""
        try:
            with open("resources/styles/diy.qss", "r", encoding="utf-8") as f:
                stylesheet = f.read()
                self.setStyleSheet(stylesheet)
        except FileNotFoundError:
            self.logger.warning("样式文件未找到", "SYSTEM")

    def reload_qss(self):
        """重载QSS样式表"""
        self.load_stylesheet()
        self.logger.info("reload qss", "SYSTEM")

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
        # 1. 业务数据更新 (1秒)
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self.update_business_data)
        self.data_timer.start(1000)

        # 2. 系统状态更新 (5秒)
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_system_status)
        self.status_timer.start(5000)

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

    def update_business_data(self):
        """更新业务数据"""
        try:
            # 状态栏和其他组件可能仍需要定时更新
            if hasattr(self, 'status_bar'):
                self.status_bar.update_display()
        except Exception as e:
            self.logger.error(f"Data update error: {e}", "SYSTEM")

    def update_system_status(self):
        """更新系统状态 (时间/连接状态)"""
        self.status_bar.update_time()

    def closeEvent(self, event):
        """[修改] 处理窗口关闭事件，增加确认提示"""

        # 弹出确认对话框
        reply = QMessageBox.question(
            self,
            '系统退出',
            '确定要退出铅浮选监控系统吗？\n所有后台服务（视频/OPC）将停止运行。',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 用户选择"是"，执行清理并关闭
            self.logger.info("用户确认退出系统", "SYSTEM")

            # 停止定时器
            if hasattr(self, 'data_timer') and self.data_timer.isActive():
                self.data_timer.stop()
            if hasattr(self, 'status_timer') and self.status_timer.isActive():
                self.status_timer.stop()

            # 清理视频线程
            get_video_service().cleanup()

            # 清理OPC服务
            get_opc_service().cleanup()

            # [新增] 停止数据服务 (确保缓存写入磁盘)
            get_data_service().stop()

            event.accept()  # 接受关闭事件，窗口将关闭
        else:
            # 用户选择"否"，取消关闭
            event.ignore()  # 忽略关闭事件，窗口保持打开