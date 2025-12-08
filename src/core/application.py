"""
应用程序主类 - 负责系统启动、关闭和主窗口管理
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import Qt

# 移除 DI 和 ServiceLocator 的引用
# from .di_container import DIContainer
# from .service_locator import ServiceLocator
from .event_bus import get_event_bus  # 改用 get_event_bus
from ..views.main_window import FoamMonitoringSystem

class FoamMonitoringApplication:
    """铅浮选监测系统主应用程序"""

    def __init__(self):
        # 移除 self.di_container = DIContainer()
        # 移除 self.service_locator = ServiceLocator()

        # 使用单例获取事件总线
        self.event_bus = get_event_bus()

        self.main_window = None
        self.qapp = None

        # 移除 self._register_services() 调用及定义

    def initialize(self):
        """初始化应用程序"""
        try:
            self.qapp = QApplication(sys.argv)
            self.qapp.setStyle('Fusion')
            self.qapp.styleHints().setColorScheme(Qt.ColorScheme.Light)

            self.main_window = FoamMonitoringSystem()

            # 使用单例发布事件
            self.event_bus.publish('application.initialized')
            return True

        except Exception as e:
            print(f"应用程序初始化失败: {e}")
            return False

    def run(self):
        """运行应用程序"""
        if not self.initialize():
            return 1
        try:
            self.main_window.showMaximized()
            self.event_bus.publish('application.started')
            return self.qapp.exec()
        except Exception as e:
            print(f"应用程序运行错误: {e}")
            return 1

    def shutdown(self):
        """关闭应用程序"""
        try:
            self.event_bus.publish('application.shutting_down')
            if self.main_window:
                self.main_window.close()
            # 移除容器清理代码
        except Exception as e:
            print(f"应用程序关闭错误: {e}")

def create_application():
    return FoamMonitoringApplication()