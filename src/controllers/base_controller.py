"""
控制器基类 - 所有控制器的抽象基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from PySide6.QtCore import QObject

from ..core.event_bus import EventBus, EventType
from ..services.logging_service import LoggingService


class BaseController(QObject, ABC):
    """控制器基类，提供通用功能"""

    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.logger = LoggingService().get_logger(f"Controller.{name}")
        self.event_bus = EventBus()
        self.is_initialized = False
        self.is_running = False
        self.dependencies = {}

    @abstractmethod
    def initialize(self):
        """初始化控制器"""
        pass

    @abstractmethod
    def start(self):
        """启动控制器"""
        pass

    @abstractmethod
    def stop(self):
        """停止控制器"""
        pass

    def _setup_event_handlers(self):
        """设置事件处理器 - 子类可重写"""
        pass

    def _initialize_dependencies(self):
        """初始化依赖项"""
        pass

    def get_status(self) -> Dict[str, Any]:
        """获取控制器状态"""
        return {
            'name': self.name,
            'is_initialized': self.is_initialized,
            'is_running': self.is_running,
            'is_healthy': self._health_check()
        }

    def _health_check(self) -> bool:
        """健康检查 - 子类可重写"""
        return self.is_initialized and self.is_running

    def cleanup(self):
        """清理控制器资源"""
        try:
            self.stop()
            self.is_initialized = False
            self.logger.info(f"控制器 {self.name} 已清理")
        except Exception as e:
            self.logger.error(f"清理控制器 {self.name} 失败: {e}")

    def set_dependency(self, name: str, dependency: Any):
        """设置依赖项"""
        self.dependencies[name] = dependency
        self.logger.debug(f"设置依赖项: {name}")

    def get_dependency(self, name: str) -> Any:
        """获取依赖项"""
        return self.dependencies.get(name)


class ControllerWithTimer(BaseController):
    """带定时器的控制器基类"""

    def __init__(self, name: str, interval: int = 1000):
        super().__init__(name)
        self.interval = interval  # 毫秒
        self.timer = None

    def start(self):
        """启动定时器"""
        from PySide6.QtCore import QTimer
        if self.timer is None:
            self.timer = QTimer()
            self.timer.timeout.connect(self._on_timer)

        self.timer.start(self.interval)
        self.is_running = True
        self.logger.info(f"控制器 {self.name} 定时器已启动，间隔: {self.interval}ms")

    def stop(self):
        """停止定时器"""
        if self.timer and self.timer.isActive():
            self.timer.stop()
        self.is_running = False
        self.logger.info(f"控制器 {self.name} 定时器已停止")

    @abstractmethod
    def _on_timer(self):
        """定时器回调函数"""
        pass


class ControllerWithThread(BaseController):
    """带线程的控制器基类"""

    def __init__(self, name: str):
        super().__init__(name)
        self.thread = None
        self.worker = None

    def start(self):
        """启动工作线程"""
        from PySide6.QtCore import QThread
        if self.thread is None:
            self.thread = QThread()
            self.worker = self._create_worker()
            self.worker.moveToThread(self.thread)

            # 连接信号
            self.thread.started.connect(self.worker.start)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()
        self.is_running = True
        self.logger.info(f"控制器 {self.name} 工作线程已启动")

    def stop(self):
        """停止工作线程"""
        if self.worker:
            self.worker.stop()
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait(5000)  # 等待5秒
        self.is_running = False
        self.logger.info(f"控制器 {self.name} 工作线程已停止")

    @abstractmethod
    def _create_worker(self):
        """创建工作线程对象"""
        pass


# 测试代码
if __name__ == "__main__":
    # 测试基础控制器
    class TestController(BaseController):
        def initialize(self):
            self.is_initialized = True
            self.logger.info("测试控制器已初始化")

        def start(self):
            self.is_running = True
            self.logger.info("测试控制器已启动")

        def stop(self):
            self.is_running = False
            self.logger.info("测试控制器已停止")


    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 测试
    controller = TestController("Test")
    controller.initialize()
    controller.start()

    status = controller.get_status()
    print(f"控制器状态: {status}")

    controller.stop()
    controller.cleanup()
