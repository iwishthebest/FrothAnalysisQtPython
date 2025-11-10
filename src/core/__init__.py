"""
核心业务逻辑模块
"""

from .application import (
    FoamMonitoringApplication,
    create_application
)
from .di_container import (
    DIContainer,
    ServiceNotFoundError,
    DependencyResolutionError,
    singleton_factory
)
from .event_bus import (
    EventBus,
    Event,
    SystemEvent,
    EventPriority
)
from .service_locator import (
    ServiceLocator,
    ServiceNotRegisteredError,
    get_service_locator,
    register_service,
    get_service,
    resolve_service
)

__all__ = [
    # Application
    'FoamMonitoringApplication',
    'create_application',

    # DI Container
    'DIContainer',
    'ServiceNotFoundError',
    'DependencyResolutionError',
    'singleton_factory',

    # Event Bus
    'EventBus',
    'Event',
    'SystemEvent',
    'EventPriority',

    # Service Locator
    'ServiceLocator',
    'ServiceNotRegisteredError',
    'get_service_locator',
    'register_service',
    'get_service',
    'resolve_service'
]