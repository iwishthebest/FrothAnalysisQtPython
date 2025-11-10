"""
事件总线系统 - 实现发布-订阅模式，用于组件间通信
"""

from typing import Any, Dict, List, Callable, Set
from dataclasses import dataclass
from enum import Enum
import threading


class EventPriority(Enum):
    """事件优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class EventSubscription:
    """事件订阅信息"""
    callback: Callable
    priority: EventPriority
    filter: Callable = None


class EventBus:
    """事件总线"""

    def __init__(self):
        self._subscriptions: Dict[str, List[EventSubscription]] = {}
        self._lock = threading.RLock()
        self._async_mode = False

    def subscribe(self,
                 event_type: str,
                 callback: Callable,
                 priority: EventPriority = EventPriority.NORMAL,
                 filter_func: Callable = None) -> None:
        """订阅事件"""
        with self._lock:
            if event_type not in self._subscriptions:
                self._subscriptions[event_type] = []

            subscription = EventSubscription(
                callback=callback,
                priority=priority,
                filter=filter_func
            )

            # 按优先级插入
            subscriptions = self._subscriptions[event_type]
            for i, sub in enumerate(subscriptions):
                if sub.priority.value < priority.value:
                    subscriptions.insert(i, subscription)
                    break
            else:
                subscriptions.append(subscription)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """取消订阅事件"""
        with self._lock:
            if event_type in self._subscriptions:
                self._subscriptions[event_type] = [
                    sub for sub in self._subscriptions[event_type]
                    if sub.callback != callback
                ]

    def publish(self, event_type: str, data: Any = None) -> None:
        """发布事件"""
        with self._lock:
            if event_type not in self._subscriptions:
                return

            subscriptions = self._subscriptions[event_type].copy()

        # 按优先级顺序执行回调
        for subscription in subscriptions:
            try:
                # 检查过滤器
                if subscription.filter and not subscription.filter(data):
                    continue

                # 执行回调
                if self._async_mode:
                    threading.Thread(
                        target=subscription.callback,
                        args=(data,) if data is not None else ()
                    ).start()
                else:
                    subscription.callback(data)

            except Exception as e:
                print(f"事件处理错误 {event_type}: {e}")

    def publish_async(self, event_type: str, data: Any = None) -> None:
        """异步发布事件"""
        threading.Thread(
            target=self.publish,
            args=(event_type, data)
        ).start()

    def set_async_mode(self, enabled: bool) -> None:
        """设置异步模式"""
        self._async_mode = enabled

    def get_subscribers(self, event_type: str) -> List[EventSubscription]:
        """获取事件订阅者"""
        with self._lock:
            return self._subscriptions.get(event_type, []).copy()

    def clear_subscriptions(self, event_type: str = None) -> None:
        """清理订阅"""
        with self._lock:
            if event_type:
                if event_type in self._subscriptions:
                    del self._subscriptions[event_type]
            else:
                self._subscriptions.clear()


class Event:
    """基础事件类"""

    def __init__(self, event_type: str, data: Any = None, source: Any = None):
        self.type = event_type
        self.data = data
        self.source = source
        self.timestamp = None
        self._prevent_default = False

        import time
        self.timestamp = time.time()

    def prevent_default(self) -> None:
        """阻止默认行为"""
        self._prevent_default = True

    def is_default_prevented(self) -> bool:
        """检查是否阻止了默认行为"""
        return self._prevent_default


class SystemEvent(Event):
    """系统事件"""

    # 应用程序事件
    APPLICATION_STARTED = "application.started"
    APPLICATION_SHUTTING_DOWN = "application.shutting_down"
    APPLICATION_INITIALIZED = "application.initialized"

    # 配置事件
    CONFIG_LOADED = "config.loaded"
    CONFIG_CHANGED = "config.changed"

    # 相机事件
    CAMERA_CONNECTED = "camera.connected"
    CAMERA_DISCONNECTED = "camera.disconnected"
    CAMERA_FRAME_RECEIVED = "camera.frame_received"

    # 浮选过程事件
    PROCESS_DATA_UPDATED = "process.data_updated"
    TANK_LEVEL_CHANGED = "tank.level_changed"
    DOSING_RATE_CHANGED = "dosing.rate_changed"

    def __init__(self, event_type: str, data: Any = None, source: Any = None):
        super().__init__(event_type, data, source)