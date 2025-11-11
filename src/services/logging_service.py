"""
日志服务模块
提供统一的日志记录和管理功能
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from PySide6.QtCore import QObject, Signal

from ..common.exceptions import ServiceError
from ..common.constants import LogLevel, LogCategory


class LoggingService(QObject):
    """
    日志管理服务
    提供统一的日志记录、存储和管理功能
    """

    # 信号定义
    log_added = Signal(str, str, str)  # 消息, 级别, 类别
    log_cleared = Signal()
    log_exported = Signal(str)

    def __init__(self, log_dir: str = "logs", max_files: int = 10, max_file_size: int = 10 * 1024 * 1024):
        """
        初始化日志服务

        Args:
            log_dir: 日志目录路径
            max_files: 最大日志文件数
            max_file_size: 单个日志文件最大大小（字节）
        """
        super().__init__()

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        self.max_files = max_files
        self.max_file_size = max_file_size

        # 日志存储
        self.logs: List[Dict[str, Any]] = []
        self.max_entries = 1000  # 内存中最大日志条目数

        # 日志缓冲区（用于UI显示）
        self.log_buffer: List[str] = []
        self.max_buffer_size = 500

        # 日志级别映射
        self.level_mapping = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL
        }

        # 初始化日志系统
        self._setup_logging_system()

    def _setup_logging_system(self):
        """设置Python日志系统"""
        try:
            # 创建格式化器
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

            # 主日志文件处理器
            main_log_file = self.log_dir / f"system_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.handlers.RotatingFileHandler(
                main_log_file,
                maxBytes=self.max_file_size,
                backupCount=self.max_files,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.INFO)

            # 控制台处理器（仅用于调试）
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.DEBUG)

            # 配置根日志记录器
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.DEBUG)
            root_logger.addHandler(file_handler)
            root_logger.addHandler(console_handler)

            # 应用程序专用日志记录器
            self.logger = logging.getLogger('FrothAnalysisSystem')
            self.logger.setLevel(logging.DEBUG)

        except Exception as e:
            raise ServiceError(f"设置日志系统失败: {e}")

    def log(self, message: str, level: LogLevel = LogLevel.INFO, category: Union[str, LogCategory] = LogCategory.SYSTEM):
        """
        记录日志

        Args:
            message: 日志消息
            level: 日志级别
            category: 日志类别（字符串或枚举）
        """
        try:
            # 将category转换为字符串
            category_str = category.value if isinstance(category, LogCategory) else str(category)

            timestamp = datetime.now()
            log_entry = {
                'timestamp': timestamp,
                'message': message,
                'level': level,
                'category': category_str
            }

            # 添加到内存存储
            self.logs.append(log_entry)
            if len(self.logs) > self.max_entries:
                self.logs.pop(0)

            # 添加到缓冲区（用于UI显示）
            formatted_entry = self._format_log_entry(log_entry)
            self.log_buffer.append(formatted_entry)
            if len(self.log_buffer) > self.max_buffer_size:
                self.log_buffer.pop(0)

            # 使用Python日志系统记录
            log_method = getattr(self.logger, level.value.lower())
            log_method(f"[{category_str}] {message}")

            # 发射信号
            self.log_added.emit(message, level.value, category_str)

        except Exception as e:
            print(f"记录日志时出错: {e}")

    @staticmethod
    def _format_log_entry(self, log_entry: Dict[str, Any]) -> str:
        """格式化日志条目"""
        timestamp = log_entry['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
        level = log_entry['level'].value
        category = log_entry['category']
        message = log_entry['message']

        return f"[{timestamp}] [{level}] [{category}] {message}"

    def debug(self, message: str, category: Union[str, LogCategory] = LogCategory.SYSTEM):
        """记录调试级别日志"""
        self.log(message, LogLevel.DEBUG, category)

    def info(self, message: str, category: Union[str, LogCategory] = LogCategory.SYSTEM):
        """记录信息级别日志"""
        self.log(message, LogLevel.INFO, category)

    def warning(self, message: str, category: Union[str, LogCategory] = LogCategory.SYSTEM):
        """记录警告级别日志"""
        self.log(message, LogLevel.WARNING, category)

    def error(self, message: str, category: Union[str, LogCategory] = LogCategory.SYSTEM):
        """记录错误级别日志"""
        self.log(message, LogLevel.ERROR, category)

    def critical(self, message: str, category: Union[str, LogCategory] = LogCategory.SYSTEM):
        """记录严重错误级别日志"""
        self.log(message, LogLevel.CRITICAL, category)

    def get_recent_logs(self, count: int = 100) -> List[str]:
        """
        获取最近的日志条目

        Args:
            count: 要获取的日志条数

        Returns:
            格式化后的日志条目列表
        """
        return self.log_buffer[-count:] if self.log_buffer else []

    def get_logs_by_level(self, level: LogLevel, count: int = 100) -> List[Dict[str, Any]]:
        """
        按级别获取日志

        Args:
            level: 日志级别
            count: 最大返回条数

        Returns:
            原始日志条目列表
        """
        filtered_logs = [log for log in self.logs if log['level'] == level]
        return filtered_logs[-count:] if filtered_logs else []

    def get_logs_by_category(self, category: str, count: int = 100) -> List[Dict[str, Any]]:
        """
        按类别获取日志

        Args:
            category: 日志类别
            count: 最大返回条数

        Returns:
            原始日志条目列表
        """
        filtered_logs = [log for log in self.logs if log['category'] == category]
        return filtered_logs[-count:] if filtered_logs else []

    def clear_logs(self):
        """清空内存中的日志"""
        self.logs.clear()
        self.log_buffer.clear()
        self.log_cleared.emit()

    def export_logs(self, filepath: Optional[str] = None) -> bool:
        """
        导出日志到文件

        Args:
            filepath: 导出文件路径，如果为None则使用默认路径

        Returns:
            导出是否成功
        """
        try:
            if filepath is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = self.log_dir / f"export_{timestamp}.log"

            with open(filepath, 'w', encoding='utf-8') as f:
                for log_entry in self.logs:
                    formatted_entry = self._format_log_entry(log_entry)
                    f.write(formatted_entry + "\n")

            self.log_exported.emit(str(filepath))
            self.info(f"日志已导出到: {filepath}", LogCategory.SYSTEM)
            return True

        except Exception as e:
            self.error(f"导出日志失败: {e}", LogCategory.SYSTEM)
            return False

    def set_log_level(self, level: LogLevel):
        """
        设置日志记录级别

        Args:
            level: 新的日志级别
        """
        if level in self.level_mapping:
            self.logger.setLevel(self.level_mapping[level])
            self.info(f"日志级别设置为: {level.value}", LogCategory.SYSTEM)

    def get_log_statistics(self) -> Dict[str, int]:
        """
        获取日志统计信息

        Returns:
            包含各级别日志数量的字典
        """
        stats = {}
        for level in LogLevel:
            stats[level.value] = len([log for log in self.logs if log['level'] == level])

        return stats


# 单例模式实例
_logging_service_instance = None

def get_logging_service() -> LoggingService:
    """获取日志服务单例实例"""
    global _logging_service_instance
    if _logging_service_instance is None:
        _logging_service_instance = LoggingService()
    return _logging_service_instance