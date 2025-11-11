"""
服务定位器 - 提供全局服务访问点
"""

from typing import Any, Type, Optional
import threading


class ServiceLocator:
    """服务定位器"""

    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        """单例模式"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._services = {}
                cls._instance._default_services = {}
            return cls._instance

    def register(self, service_name: str, service_instance: Any) -> None:
        """注册服务"""
        with self._lock:
            self._services[service_name] = service_instance

    def register_default(self, service_name: str, service_instance: Any) -> None:
        """注册默认服务"""
        with self._lock:
            self._default_services[service_name] = service_instance

    def get(self, service_name: str) -> Any:
        """获取服务"""
        with self._lock:
            if service_name in self._services:
                return self._services[service_name]
            elif service_name in self._default_services:
                return self._default_services[service_name]
            else:
                raise ServiceNotRegisteredError(
                    f"服务未注册: {service_name}"
                )

    def get_optional(self, service_name: str) -> Optional[Any]:
        """获取可选服务（不存在时返回None）"""
        try:
            return self.get(service_name)
        except ServiceNotRegisteredError:
            return None

    def resolve(self, service_type: Type) -> Any:
        """根据类型解析服务"""
        with self._lock:
            for service in self._services.values():
                if isinstance(service, service_type):
                    return service

            for service in self._default_services.values():
                if isinstance(service, service_type):
                    return service

            raise ServiceNotRegisteredError(
                f"未找到类型为 {service_type.__name__} 的服务"
            )

    def has_service(self, service_name: str) -> bool:
        """检查服务是否存在"""
        with self._lock:
            return (service_name in self._services or
                    service_name in self._default_services)

    def unregister(self, service_name: str) -> None:
        """注销服务"""
        with self._lock:
            if service_name in self._services:
                # 清理服务资源
                service = self._services[service_name]
                if hasattr(service, 'close'):
                    service.close()
                elif hasattr(service, 'shutdown'):
                    service.shutdown()

                del self._services[service_name]

    def clear(self) -> None:
        """清理所有服务"""
        with self._lock:
            # 清理所有注册的服务
            for service_name in list(self._services.keys()):
                self.unregister(service_name)

            # 清理默认服务（不调用close/shutdown）
            self._default_services.clear()


class ServiceNotRegisteredError(Exception):
    """服务未注册异常"""
    pass


# 全局服务定位器实例
_service_locator = None


def get_service_locator() -> ServiceLocator:
    """获取全局服务定位器实例"""
    global _service_locator
    if _service_locator is None:
        _service_locator = ServiceLocator()
    return _service_locator


def register_service(service_name: str, service_instance: Any) -> None:
    """注册服务到全局定位器"""
    get_service_locator().register(service_name, service_instance)


def get_service(service_name: str) -> Any:
    """从全局定位器获取服务"""
    return get_service_locator().get(service_name)


def resolve_service(service_type: Type) -> Any:
    """从全局定位器解析服务"""
    return get_service_locator().resolve(service_type)
