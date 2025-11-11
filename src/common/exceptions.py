"""
自定义异常定义
"""

class ServiceError(Exception):
    """服务层异常基类"""
    pass

class LoggingError(ServiceError):
    """日志服务异常"""
    pass