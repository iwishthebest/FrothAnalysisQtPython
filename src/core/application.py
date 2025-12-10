"""
应用程序主类 - 负责系统启动、关闭和主窗口管理
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import Qt

from .event_bus import get_event_bus
from ..views.main_window import FoamMonitoringSystem

# === [新增] 导入后台服务 ===
from src.services.opc_service import get_opc_service
from src.services.data_service import get_data_service


class FoamMonitoringApplication:
    """铅浮选监测系统主应用程序"""

    def __init__(self):
        # 使用单例获取事件总线
        self.event_bus = get_event_bus()

        self.main_window = None
        self.qapp = None

    def initialize(self):
        """初始化应用程序"""
        try:
            self.qapp = QApplication(sys.argv)
            self.qapp.setStyle('Fusion')
            self.qapp.styleHints().setColorScheme(Qt.ColorScheme.Light)

            # === [核心修改] 配置后台服务连接 ===
            self._setup_background_services()

            # 创建主窗口
            self.main_window = FoamMonitoringSystem()

            # 使用单例发布事件
            self.event_bus.publish('application.initialized')
            return True

        except Exception as e:
            print(f"应用程序初始化失败: {e}")
            return False

    def _setup_background_services(self):
        """配置和连接后台服务 (OPC -> DataService)"""
        try:
            # 1. 获取服务实例
            opc_service = get_opc_service()
            data_service = get_data_service()

            # 2. 启动数据服务 (确保数据库表已创建)
            if data_service.start():
                print("[System] 数据服务已启动 (Database/CSV)")

            # 3. 建立信号连接
            # 获取 OPC 的工作线程
            opc_worker = opc_service.get_worker()

            if opc_worker:
                # [关键] 将 OPC 的数据更新信号 连接到 DataService 的记录方法
                opc_worker.data_updated.connect(data_service.record_data)
                print("[System] 信号连接成功: OPC Service -> Data Service")
            else:
                print("[System] 警告: OPC Worker 尚未初始化，无法建立数据存储连接")

        except Exception as e:
            print(f"[System] 后台服务连接配置失败: {e}")

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

            # 这里可以添加额外的清理逻辑，但主要清理通常在 MainWindow.closeEvent 中触发

        except Exception as e:
            print(f"应用程序关闭错误: {e}")


def create_application():
    return FoamMonitoringApplication()