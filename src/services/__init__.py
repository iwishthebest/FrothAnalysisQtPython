"""
服务层 - 统一的服务接口和基类定义
提供所有业务服务的基类和接口规范
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from enum import Enum


class ServiceStatus(Enum):
    """服务状态枚举"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class BaseService(ABC):
    """服务基类 - 定义统一的服务接口"""

    def __init__(self, name: str):
        self.name = name
        self.status = ServiceStatus.STOPPED
        self.config: Dict[str, Any] = {}

    @abstractmethod
    def start(self) -> bool:
        """启动服务"""
        pass

    @abstractmethod
    def stop(self) -> bool:
        """停止服务"""
        pass

    @abstractmethod
    def restart(self) -> bool:
        """重启服务"""
        pass

    def get_status(self) -> Dict[str, Any]:
        """获取服务状态信息"""
        return {
            "name": self.name,
            "status": self.status.value,
            "config": self.config
        }

    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """更新服务配置"""
        self.config.update(new_config)
        return True


class ServiceError(Exception):
    """服务异常基类"""
    pass


# 服务管理器
class ServiceManager:
    """服务管理器 - 统一管理所有服务的生命周期"""

    def __init__(self):
        self._services: Dict[str, BaseService] = {}

    def register_service(self, name: str, service: BaseService) -> bool:
        """注册服务"""
        self._services[name] = service
        return True

    def start_all(self) -> bool:
        """启动所有服务"""
        return all(
            service.start()
            for service in self._services.values()
        )

    def stop_all(self) -> bool:
        """停止所有服务"""
        return all(
            service.stop()
            for service in self._services.values()
        )

    def get_service(self, name: str) -> Optional[BaseService]:
        """获取服务实例"""
        return self._services.get(name)


# 创建全局服务管理器实例
service_manager = ServiceManager()

__all__ = [
    'BaseService',
    'ServiceStatus',
    'ServiceError',
    'ServiceManager',
    'service_manager'
]