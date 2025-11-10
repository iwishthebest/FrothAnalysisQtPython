"""
日志服务
提供统一的日志记录和管理功能
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any
from . import BaseService, ServiceError, ServiceStatus


class LoggingService(BaseService):
    """日志管理服务"""

    def __init__(self, log_dir: str = "logs", max_files: int = 10):
        super().__init__("logging_service")
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        self.max_files = max_files
        self.loggers: Dict[str, logging.Logger] = {}

    def start(self) -> bool:
        """启动日志服务"""
        try:
            self.status = ServiceStatus.STARTING

            # 配置根日志记录器
            self._setup_root_logger()

            self.status = ServiceStatus.RUNNING
            return True

        except Exception as e:
            self.status = ServiceStatus.ERROR
            raise ServiceError(f"日志服务启动失败: {e}")

    def stop(self) -> bool:
        """停止日志服务"""
        self.status = ServiceStatus.STOPPING

        # 关闭所有日志处理器
        for logger in self.loggers.values():
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)

        self.status = ServiceStatus.STOPPED
        return True

    def restart(self) -> bool:
        """重启日志服务"""
        self.stop()
        return self.start()

    def _setup_root_logger(self) -> None:
        """设置根日志记录器配置"""
        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # 文件处理器（按文件大小轮转）
        log_file = self.log_dir / "system.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=self.max_files,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志记录器"""
        if name not in self.loggers:
            logger = logging.getLogger(name)
            self.loggers[name] = logger
        return self.loggers[name]

    def set_level(self, level: str) -> None:
        """设置日志级别"""
        level_mapping = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }

        if level in level_mapping:
            logging.getLogger().setLevel(level_mapping[level])
