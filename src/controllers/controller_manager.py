"""
控制器管理器 - 统一管理所有控制器的生命周期
"""

from typing import Dict, List, Optional, Type
import logging
from PySide6.QtCore import QObject

from .base_controller import BaseController
from ..core.di_container import DIContainer
from ..core.event_bus import EventBus, EventType
from ..services.logging_service import LoggingService


class ControllerManager(QObject):
    """控制器管理器 - 负责控制器的初始化、启动、停止和状态监控"""

    def __init__(self, di_container: DIContainer, event_bus: EventBus):
        super().__init__()
        self.di_container = di_container
        self.event_bus = event_bus
        self.logger = LoggingService().get_logger("ControllerManager")

        self.controllers: Dict[str, BaseController] = {}
        self.controller_dependencies: Dict[str, List[str]] = {}
        self.initialization_order: List[str] = []

    def register_controller(self, name: str, controller_class: Type[BaseController],
                            dependencies: List[str] = None):
        """注册控制器"""
        if dependencies is None:
            dependencies = []

        # 创建控制器实例
        controller = controller_class(name)
        self.controllers[name] = controller
        self.controller_dependencies[name] = dependencies

        self.logger.info(f"注册控制器: {name}, 依赖: {dependencies}")

    def initialize_all(self):
        """初始化所有控制器"""
        self.logger.info("开始初始化所有控制器...")

        try:
            # 计算初始化顺序（基于依赖关系）
            self._calculate_initialization_order()

            # 按顺序初始化控制器
            for controller_name in self.initialization_order:
                self._initialize_single_controller(controller_name)

            self.logger.info("所有控制器初始化完成")
            self.event_bus.publish(EventType.SYSTEM_EVENT, "控制器初始化完成")

        except Exception as e:
            self.logger.error(f"控制器初始化失败: {e}")
            raise

    def _calculate_initialization_order(self):
        """计算控制器初始化顺序（拓扑排序）"""
        visited = set()
        temp_visited = set()
        order = []

        def visit(controller_name):
            if controller_name in temp_visited:
                raise RuntimeError(f"检测到循环依赖: {controller_name}")
            if controller_name in visited:
                return

            temp_visited.add(controller_name)

            # 先访问依赖项
            for dependency in self.controller_dependencies.get(controller_name, []):
                if dependency in self.controllers:
                    visit(dependency)

            temp_visited.remove(controller_name)
            visited.add(controller_name)
            order.append(controller_name)

        # 对每个控制器进行拓扑排序
        for controller_name in self.controllers.keys():
            if controller_name not in visited:
                visit(controller_name)

        self.initialization_order = order
        self.logger.debug(f"控制器初始化顺序: {order}")

    def _initialize_single_controller(self, controller_name: str):
        """初始化单个控制器"""
        controller = self.controllers[controller_name]

        try:
            # 设置依赖项
            dependencies = self.controller_dependencies.get(controller_name, [])
            for dep_name in dependencies:
                if dep_name in self.controllers:
                    controller.set_dependency(dep_name, self.controllers[dep_name])

            # 设置服务依赖
            controller.set_dependency('di_container', self.di_container)
            controller.set_dependency('event_bus', self.event_bus)

            # 初始化控制器
            controller.initialize()
            controller.is_initialized = True

            self.logger.info(f"控制器 {controller_name} 初始化成功")

        except Exception as e:
            self.logger.error(f"初始化控制器 {controller_name} 失败: {e}")
            raise

    def start_all(self):
        """启动所有控制器"""
        self.logger.info("启动所有控制器...")

        success_count = 0
        for controller_name in self.initialization_order:
            if self._start_single_controller(controller_name):
                success_count += 1

        self.logger.info(f"控制器启动完成: {success_count}/{len(self.controllers)} 个成功")
        self.event_bus.publish(EventType.SYSTEM_EVENT, f"控制器启动完成: {success_count}/{len(self.controllers)}")

    def _start_single_controller(self, controller_name: str) -> bool:
        """启动单个控制器"""
        controller = self.controllers[controller_name]

        if not controller.is_initialized:
            self.logger.warning(f"控制器 {controller_name} 未初始化，跳过启动")
            return False

        try:
            controller.start()
            controller.is_running = True
            self.logger.info(f"控制器 {controller_name} 启动成功")
            return True
        except Exception as e:
            self.logger.error(f"启动控制器 {controller_name} 失败: {e}")
            return False

    def stop_all(self):
        """停止所有控制器"""
        self.logger.info("停止所有控制器...")

        # 逆序停止（依赖关系反向）
        success_count = 0
        for controller_name in reversed(self.initialization_order):
            if self._stop_single_controller(controller_name):
                success_count += 1

        self.logger.info(f"控制器停止完成: {success_count}/{len(self.controllers)} 个成功")

    def _stop_single_controller(self, controller_name: str) -> bool:
        """停止单个控制器"""
        controller = self.controllers[controller_name]

        if not controller.is_running:
            self.logger.debug(f"控制器 {controller_name} 未运行，跳过停止")
            return True

        try:
            controller.stop()
            controller.is_running = False
            self.logger.info(f"控制器 {controller_name} 停止成功")
            return True
        except Exception as e:
            self.logger.error(f"停止控制器 {controller_name} 失败: {e}")
            return False

    def cleanup_all(self):
        """清理所有控制器"""
        self.logger.info("清理所有控制器资源...")

        for controller_name in reversed(self.initialization_order):
            self._cleanup_single_controller(controller_name)

        self.controllers.clear()
        self.controller_dependencies.clear()
        self.initialization_order.clear()

        self.logger.info("所有控制器资源已清理")

    def _cleanup_single_controller(self, controller_name: str):
        """清理单个控制器"""
        controller = self.controllers.get(controller_name)
        if controller:
            try:
                controller.cleanup()
            except Exception as e:
                self.logger.error(f"清理控制器 {controller_name} 失败: {e}")

    def get_controller(self, name: str) -> Optional[BaseController]:
        """获取指定控制器"""
        return self.controllers.get(name)

    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有控制器状态"""
        status = {}
        for name, controller in self.controllers.items():
            status[name] = controller.get_status()
        return status

    def restart_controller(self, name: str) -> bool:
        """重启指定控制器"""
        controller = self.get_controller(name)
        if not controller:
            self.logger.error(f"控制器 {name} 不存在")
            return False

        try:
            self.logger.info(f"重启控制器 {name}...")
            controller.stop()
            controller.initialize()
            controller.start()
            self.logger.info(f"控制器 {name} 重启成功")
            return True
        except Exception as e:
            self.logger.error(f"重启控制器 {name} 失败: {e}")
            return False


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)


    # 创建测试控制器
    class TestController(BaseController):
        def initialize(self):
            self.is_initialized = True

        def start(self):
            self.is_running = True

        def stop(self):
            self.is_running = False


    # 测试控制器管理器
    di_container = DIContainer()
    event_bus = EventBus()

    manager = ControllerManager(di_container, event_bus)

    # 注册控制器
    manager.register_controller("test1", TestController)
    manager.register_controller("test2", TestController, dependencies=["test1"])

    # 初始化并启动
    manager.initialize_all()
    manager.start_all()

    # 检查状态
    status = manager.get_status()
    print(f"控制器状态: {status}")

    # 清理
    manager.stop_all()
    manager.cleanup_all()
