"""
应用程序主类 - 负责系统启动、关闭和主窗口管理
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import Qt

from .di_container import DIContainer
from .event_bus import EventBus
from .service_locator import ServiceLocator
from ..views.main_window import FoamMonitoringSystem


class FoamMonitoringApplication:
    """铅浮选监测系统主应用程序"""

    def __init__(self):
        self.di_container = DIContainer()
        self.event_bus = EventBus()
        self.service_locator = ServiceLocator()
        self.main_window = None
        self.qapp = None

        # 注册核心服务
        self._register_services()

    def _register_services(self):
        """注册核心服务到容器和定位器"""
        # 注册到依赖注入容器
        self.di_container.register('event_bus', self.event_bus)
        self.di_container.register('service_locator', self.service_locator)

        # 注册到服务定位器
        self.service_locator.register('di_container', self.di_container)
        self.service_locator.register('event_bus', self.event_bus)

    def initialize(self):
        """初始化应用程序"""
        try:
            # 创建QApplication实例
            self.qapp = QApplication(sys.argv)
            self.qapp.setStyle('Fusion')
            self.qapp.styleHints().setColorScheme(Qt.ColorScheme.Light)

            # 创建主窗口
            self.main_window = FoamMonitoringSystem()

            # 发布应用程序初始化完成事件
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
            # 显示主窗口
            self.main_window.showMaximized()

            # 发布应用程序启动事件
            self.event_bus.publish('application.started')

            # 运行事件循环
            return self.qapp.exec()

        except Exception as e:
            print(f"应用程序运行错误: {e}")
            return 1

    def shutdown(self):
        """关闭应用程序"""
        try:
            # 发布应用程序关闭事件
            self.event_bus.publish('application.shutting_down')

            # 关闭主窗口
            if self.main_window:
                self.main_window.close()

            # 清理资源
            self.di_container.clear()
            self.service_locator.clear()

        except Exception as e:
            print(f"应用程序关闭错误: {e}")


def create_application():
    """创建应用程序实例（工厂函数）"""
    return FoamMonitoringApplication()
