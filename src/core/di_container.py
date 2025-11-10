"""
依赖注入容器 - 管理对象生命周期和依赖关系
"""

from typing import Any, Dict, Type, Callable, Optional


class DIContainer:
    """依赖注入容器"""

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}

    def register(self, service_name: str, instance: Any) -> None:
        """注册服务实例"""
        self._services[service_name] = instance

    def register_factory(self, service_name: str, factory: Callable) -> None:
        """注册服务工厂"""
        self._factories[service_name] = factory

    def register_singleton(self, service_name: str, instance: Any) -> None:
        """注册单例服务"""
        self._singletons[service_name] = instance

    def get(self, service_name: str) -> Any:
        """获取服务实例"""
        # 首先检查单例
        if service_name in self._singletons:
            return self._singletons[service_name]

        # 检查已注册的实例
        if service_name in self._services:
            return self._services[service_name]

        # 检查工厂
        if service_name in self._factories:
            instance = self._factories[service_name]()
            # 如果是单例工厂，缓存实例
            if hasattr(self._factories[service_name], '_is_singleton'):
                self._singletons[service_name] = instance
            return instance

        raise ServiceNotFoundError(f"服务未找到: {service_name}")

    def resolve(self, service_class: Type) -> Any:
        """解析依赖并创建实例"""
        try:
            # 获取类的依赖
            dependencies = self._get_dependencies(service_class)

            # 创建实例
            instance = service_class(**dependencies)
            return instance

        except Exception as e:
            raise DependencyResolutionError(
                f"解析依赖失败 {service_class.__name__}: {e}"
            )

    def _get_dependencies(self, service_class: Type) -> Dict[str, Any]:
        """获取类的依赖项"""
        dependencies = {}

        # 检查类的__init__方法签名
        import inspect
        signature = inspect.signature(service_class.__init__)

        for param_name, param in signature.parameters.items():
            if param_name == 'self':
                continue

            # 检查参数是否有类型注解
            if param.annotation != inspect.Parameter.empty:
                # 根据类型解析依赖
                dep_name = param.annotation.__name__
                dependencies[param_name] = self.get(dep_name)
            else:
                # 如果没有类型注解，尝试按名称解析
                dependencies[param_name] = self.get(param_name)

        return dependencies

    def has_service(self, service_name: str) -> bool:
        """检查服务是否存在"""
        return (service_name in self._services or
                service_name in self._factories or
                service_name in self._singletons)

    def clear(self):
        """清理容器"""
        # 清理单例实例
        for service_name, instance in self._singletons.items():
            if hasattr(instance, 'close'):
                instance.close()
            elif hasattr(instance, 'shutdown'):
                instance.shutdown()

        self._services.clear()
        self._factories.clear()
        self._singletons.clear()


class ServiceNotFoundError(Exception):
    """服务未找到异常"""
    pass


class DependencyResolutionError(Exception):
    """依赖解析异常"""
    pass


def singleton_factory(factory_func: Callable) -> Callable:
    """单例工厂装饰器"""
    factory_func._is_singleton = True
    return factory_func