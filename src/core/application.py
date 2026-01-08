# src/core/application.py
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import Qt

from .event_bus import get_event_bus
from ..views.main_window import FoamMonitoringSystem
from src.services.opc_service import get_opc_service
from src.services.data_service import get_data_service
from src.services.logging_service import get_logging_service
from src.common.constants import LogCategory

from src.controllers.system_controller import SystemController


class FoamMonitoringApplication:
    """铅浮选监测系统主应用程序"""

    def __init__(self):
        self.event_bus = get_event_bus()
        self.logger = get_logging_service()
        self.main_window = None
        self.qapp = None
        self.system_controller = None

    def initialize(self):
        """初始化应用程序"""
        try:
            self.qapp = QApplication(sys.argv)
            self.qapp.setStyle('Fusion')
            self.qapp.styleHints().setColorScheme(Qt.ColorScheme.Light)

            self._setup_background_services()

            self.main_window = FoamMonitoringSystem()
            self.event_bus.publish('application.initialized')
            return True

        except Exception as e:
            self.logger.critical(f"应用程序初始化失败: {e}", LogCategory.SYSTEM)
            return False

    def _setup_background_services(self):
        """配置和连接后台服务"""
        try:
            opc_service = get_opc_service()
            data_service = get_data_service()

            if data_service.start():
                self.logger.info("数据服务已启动 (Database/CSV)", LogCategory.DATA)

            opc_worker = opc_service.get_worker()
            if opc_worker:
                opc_worker.data_updated.connect(data_service.record_data)
                self.logger.info("信号连接成功: OPC Service -> Data Service", LogCategory.SYSTEM)
            else:
                self.logger.warning("OPC Worker 尚未初始化，无法建立数据存储连接", LogCategory.OPC)

            self.system_controller = SystemController()
            self.logger.info("系统总控制器已启动 (Video <-> Analysis 链路已建立)", LogCategory.SYSTEM)

        except Exception as e:
            self.logger.error(f"后台服务连接配置失败: {e}", LogCategory.SYSTEM)

    def run(self):
        """运行应用程序"""
        if not self.initialize():
            return 1
        try:
            self.main_window.showMaximized()
            self.event_bus.publish('application.started')
            self.logger.info("主窗口已显示，进入事件循环", LogCategory.SYSTEM)  # [新增]
            return self.qapp.exec()
        except Exception as e:
            self.logger.critical(f"应用程序运行错误: {e}", LogCategory.SYSTEM)
            return 1

    def shutdown(self):
        """关闭应用程序"""
        try:
            self.event_bus.publish('application.shutting_down')
            if self.main_window:
                self.main_window.close()
        except Exception as e:
            self.logger.error(f"应用程序关闭错误: {e}", LogCategory.SYSTEM)


def create_application():
    return FoamMonitoringApplication()
