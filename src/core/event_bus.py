"""
src/core/event_bus.py
事件总线系统 - 实现发布-订阅模式
"""

from typing import Any, Dict, List, Callable
from dataclasses import dataclass
from enum import Enum
import threading
import time

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

    def subscribe(self, event_type: str, callback: Callable,
                  priority: EventPriority = EventPriority.NORMAL,
                  filter_func: Callable = None) -> None:
        """订阅事件"""
        with self._lock:
            if event_type not in self._subscriptions:
                self._subscriptions[event_type] = []

            subscription = EventSubscription(callback, priority, filter_func)
            # 按优先级插入
            subs = self._subscriptions[event_type]
            for i, sub in enumerate(subs):
                if sub.priority.value < priority.value:
                    subs.insert(i, subscription)
                    break
            else:
                subs.append(subscription)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        with self._lock:
            if event_type in self._subscriptions:
                self._subscriptions[event_type] = [
                    s for s in self._subscriptions[event_type]
                    if s.callback != callback
                ]

    def publish(self, event_type: str, data: Any = None) -> None:
        """发布事件"""
        with self._lock:
            if event_type not in self._subscriptions:
                return
            subscriptions = self._subscriptions[event_type].copy()

        for sub in subscriptions:
            try:
                if sub.filter and not sub.filter(data):
                    continue

                if self._async_mode:
                    threading.Thread(target=sub.callback, args=(data,) if data else ()).start()
                else:
                    sub.callback(data)
            except Exception as e:
                print(f"事件处理错误 {event_type}: {e}")

    def clear_subscriptions(self, event_type: str = None) -> None:
        with self._lock:
            if event_type:
                self._subscriptions.pop(event_type, None)
            else:
                self._subscriptions.clear()

# === [修复] 新增 EventType 类 ===
class EventType:
    """事件类型定义"""
    # 系统事件
    APPLICATION_INITIALIZED = "application.initialized"
    APPLICATION_STARTED = "application.started"
    APPLICATION_SHUTTING_DOWN = "application.shutting_down"

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

# 基础事件类
class Event:
    def __init__(self, event_type: str, data: Any = None, source: Any = None):
        self.type = event_type
        self.data = data
        self.source = source
        self.timestamp = time.time()
        self._prevent_default = False

class SystemEvent(Event):
    """系统事件包装类 (保留以兼容旧代码，但建议逐步迁移到 EventType)"""
    pass

# === [核心修改] 全局单例模式 ===
_event_bus_instance = None

def get_event_bus() -> EventBus:
    """获取事件总线单例"""
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    return _event_bus_instance