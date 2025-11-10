import os
import json
from cryptography.fernet import Fernet
from typing import Dict, Any, List

from config.settings import (
    CameraConfig, TankConfig, UIConfig, NetworkConfig, SystemConfig
)
from src.services.logging_service import SystemLogger


class ConfigService:
    """配置服务"""

    def __init__(self, config_file: str = "config.json", key_file: str = "secret.key"):
        self.config_file = config_file
        self.key_file = key_file
        self.cipher: Optional[Fernet] = None
        self.system_config: Optional[SystemConfig] = None
        self.logger = SystemLogger()

    def initialize(self):
        """初始化配置服务"""
        self.cipher = self._setup_encryption()
        self.system_config = self._load_config()

    def _setup_encryption(self) -> Fernet:
        """设置加密"""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
        return Fernet(key)

    def _load_config(self) -> SystemConfig:
        """加载配置"""
        if not os.path.exists(self.config_file):
            return self._create_default_config()

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                encrypted_data = f.read()
                decrypted_data = self.cipher.decrypt(encrypted_data.encode()).decode()
                config_dict = json.loads(decrypted_data)
                return self._dict_to_system_config(config_dict)
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}，使用默认配置")
            return self._create_default_config()

    def _create_default_config(self) -> SystemConfig:
        """创建默认配置"""
        default_config = SystemConfig(
            cameras=[
                CameraConfig(
                    name="铅快粗泡沫相机",
                    rtsp_url="rtsp://admin:fkqxk010@192.168.1.101:554/Streaming/Channels/101",
                    position="粗选",
                    enabled=True
                )
            ],
            tanks=[
                TankConfig(
                    name="铅快粗槽",
                    type="粗选",
                    color="#3498db",
                    level_range=(0.5, 2.5),
                    dosing_range=(0, 200)
                )
            ],
            ui=UIConfig(),
            network=NetworkConfig()
        )
        self.save_config(default_config)
        return default_config

    def save_config(self, config: SystemConfig):
        """保存配置"""
        try:
            config_dict = self._system_config_to_dict(config)
            json_data = json.dumps(config_dict, ensure_ascii=False, indent=2)
            encrypted_data = self.cipher.encrypt(json_data.encode())

            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(encrypted_data.decode())
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")

    def get_camera_configs(self) -> List[CameraConfig]:
        """获取相机配置"""
        return self.system_config.cameras

    def get_tank_configs(self) -> List[TankConfig]:
        """获取浮选槽配置"""
        return self.system_config.tanks

    def get_ui_config(self) -> UIConfig:
        """获取界面配置"""
        return self.system_config.ui

    def get_network_config(self) -> NetworkConfig:
        """获取网络配置"""
        return self.system_config.network