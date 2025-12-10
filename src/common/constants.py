"""
常量定义文件
"""

from enum import Enum


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    """日志类别枚举"""
    SYSTEM = "SYSTEM"
    VIDEO = "VIDEO"
    DATA = "DATA"
    OPC = "OPC"
    UI = "UI"
    CONTROL = "CONTROL"
    NETWORK = "NETWORK"

    def __str__(self):
        """返回枚举的字符串值"""
        return self.value
