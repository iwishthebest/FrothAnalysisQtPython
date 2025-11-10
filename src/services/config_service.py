"""
配置管理服务
统一管理系统配置，支持热更新和配置验证
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from threading import RLock
from . import BaseService, ServiceStatus, ServiceError


class ConfigService(BaseService):
    """配置管理服务"""

    def __init__(self, config_dir: str = "config"):
        super().__init__("config_service")
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

        self._config: Dict[str, Any] = {}
        self._lock = RLock()
        self.config_file = self.config_dir / "system_config.json"

        # 默认配置
        self._default_config = {
            "system": {
                "name": "铅浮选监测系统",
                "version": "1.0.0",
                "debug": False
            },
            "camera": {
                "max_retries": 3,
                "timeout": 30,
                "resolution": "1920x1080"
            },
            "opc": {
                "server_url": "opc.tcp://localhost:4840",
                "update_interval": 1000
            }
        }

    def start(self) -> bool:
        """启动配置服务"""
        try:
            self.status = ServiceStatus.STARTING
            self._load_config()
            self.status = ServiceStatus.RUNNING
            return True
        except Exception as e:
            self.status = ServiceStatus.ERROR
            raise ServiceError(f"配置服务启动失败: {e}")

    def stop(self) -> bool:
        """停止配置服务"""
        self.status = ServiceStatus.STOPPING
        self._save_config()
        self.status = ServiceStatus.STOPPED
        return True

    def restart(self) -> bool:
        """重启配置服务"""
        self.stop()
        return self.start()

    def _load_config(self) -> None:
        """加载配置文件"""
        with self._lock:
            if self.config_file.exists():
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        loaded_config = json.load(f)
                    self._config = self._deep_merge(
                        self._default_config,
                        loaded_config
                    )
                except Exception as e:
                    print(f"加载配置文件失败，使用默认配置: {e}")
                    self._config = self._default_config.copy()
            else:
                self._config = self._default_config.copy()
                self._save_config()

    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        """深度合并字典"""
        result = base.copy()

        for key, value in update.items():
            if (key in result and isinstance(result[key], dict)
                    and isinstance(value, dict)):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _save_config(self) -> None:
        """保存配置到文件"""
        with self._lock:
            try:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(self._config, f, indent=2, ensure_ascii=False)
            except Exception as e:
                raise ServiceError(f"保存配置失败: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any, save: bool = True) -> bool:
        """设置配置值"""
        with self._lock:
            keys = key.split('.')
            config = self._config

            # 导航到最后一个键的父级
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]

            config[keys[-1]] = value

            if save:
                self._save_config()

            return True

    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()