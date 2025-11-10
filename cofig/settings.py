"""
主配置文件 - 系统核心配置定义
"""

import os
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from enum import Enum
from cryptography.fernet import Fernet


class CameraPosition(Enum):
    """相机位置枚举"""
    LEAD_ROUGH = "铅快粗泡沫"
    LEAD_CLEAN_1 = "铅精一泡沫"
    LEAD_CLEAN_2 = "铅精二泡沫"
    LEAD_CLEAN_3 = "铅精三泡沫"


class TankType(Enum):
    """浮选槽类型枚举"""
    ROUGH = "粗选"
    CLEAN_1 = "精选一"
    CLEAN_2 = "精选二"
    CLEAN_3 = "精选三"


@dataclass
class CameraConfig:
    """相机配置"""
    name: str
    rtsp_url: str
    position: CameraPosition
    enabled: bool = True
    timeout: int = 10
    reconnect_interval: int = 5
    max_retries: int = 10

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['position'] = self.position.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CameraConfig':
        """从字典创建实例"""
        data = data.copy()
        if isinstance(data.get('position'), str):
            for position in CameraPosition:
                if position.value == data['position']:
                    data['position'] = position
                    break
        return cls(**data)


@dataclass
class TankConfig:
    """浮选槽配置"""
    name: str
    type: TankType
    color: str
    level_range: tuple = (0.5, 2.5)
    dosing_range: tuple = (0, 200)
    default_level: float = 1.2
    default_dosing: float = 50

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['type'] = self.type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TankConfig':
        """从字典创建实例"""
        data = data.copy()
        if isinstance(data.get('type'), str):
            for tank_type in TankType:
                if tank_type.value == data['type']:
                    data['type'] = tank_type
                    break
        return cls(**data)


@dataclass
class UIConfig:
    """界面配置"""
    refresh_rate: int = 100  # ms
    theme: str = "light"
    language: str = "zh-CN"
    max_data_points: int = 1000
    window_size: tuple = (1400, 900)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class NetworkConfig:
    """网络配置"""
    opc_server_url: str = "opc.tcp://localhost:4840"
    api_endpoint: str = "http://localhost:8000/api"
    timeout: int = 30
    retry_count: int = 3

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class SystemConfig:
    """系统主配置"""
    cameras: List[CameraConfig]
    tanks: List[TankConfig]
    ui: UIConfig
    network: NetworkConfig

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'cameras': [cam.to_dict() for cam in self.cameras],
            'tanks': [tank.to_dict() for tank in self.tanks],
            'ui': self.ui.to_dict(),
            'network': self.network.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemConfig':
        """从字典创建实例"""
        cameras = [CameraConfig.from_dict(cam) for cam in data.get('cameras', [])]
        tanks = [TankConfig.from_dict(tank) for tank in data.get('tanks', [])]
        ui = UIConfig(**data.get('ui', {}))
        network = NetworkConfig(**data.get('network', {}))

        return cls(cameras=cameras, tanks=tanks, ui=ui, network=network)


class SecureConfigManager:
    """安全的配置管理器"""

    def __init__(self, config_file: str = "config.json", key_file: str = "secret.key"):
        self.config_file = config_file
        self.key_file = key_file
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
                config_data = json.loads(decrypted_data)
                return SystemConfig.from_dict(config_data)
        except Exception as e:
            print(f"加载配置失败: {e}，使用默认配置")
            return self._create_default_config()

    def _create_default_config(self) -> SystemConfig:
        """创建默认配置"""
        cameras = [
            CameraConfig(
                name="铅快粗泡沫相机",
                rtsp_url="rtsp://admin:fkqxk010@192.168.1.101:554/Streaming/Channels/101",
                position=CameraPosition.LEAD_ROUGH,
                enabled=True
            )
        ]

        tanks = [
            TankConfig(
                name="铅快粗槽",
                type=TankType.ROUGH,
                color="#3498db",
                level_range=(0.5, 2.5),
                dosing_range=(0, 200)
            )
        ]

        ui = UIConfig()
        network = NetworkConfig()

        system_config = SystemConfig(
            cameras=cameras,
            tanks=tanks,
            ui=ui,
            network=network
        )

        self.save_config(system_config)
        return system_config

    def save_config(self, config: SystemConfig = None):
        """保存配置"""
        if config is None:
            config = self.system_config

        try:
            config_dict = config.to_dict()
            json_data = json.dumps(config_dict, ensure_ascii=False, indent=2)
            encrypted_data = self.cipher.encrypt(json_data.encode())

            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(encrypted_data.decode())
        except Exception as e:
            print(f"保存配置失败: {e}")

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

    def update_camera_config(self, camera_config: CameraConfig):
        """更新相机配置"""
        for i, cam in enumerate(self.system_config.cameras):
            if cam.name == camera_config.name:
                self.system_config.cameras[i] = camera_config
                break
        else:
            self.system_config.cameras.append(camera_config)

        self.save_config()

    def update_tank_config(self, tank_config: TankConfig):
        """更新浮选槽配置"""
        for i, tank in enumerate(self.system_config.tanks):
            if tank.name == tank_config.name:
                self.system_config.tanks[i] = tank_config
                break
        else:
            self.system_config.tanks.append(tank_config)

        self.save_config()


# 全局配置实例
config_manager = SecureConfigManager()