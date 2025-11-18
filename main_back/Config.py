"""
配置管理模块 - 集中管理所有系统配置
"""

import os
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from cryptography.fernet import Fernet


@dataclass
class CameraConfig:
    """相机配置"""
    name: str
    rtsp_url: str
    position: str
    enabled: bool = True
    timeout: int = 10
    reconnect_interval: int = 5
    max_retries: int = 10


@dataclass
class TankConfig:
    """浮选槽配置"""
    name: str
    type: str
    color: str
    level_range: tuple = (0.5, 2.5)
    dosing_range: tuple = (0, 200)
    default_level: float = 1.2
    default_dosing: float = 50


@dataclass
class UIConfig:
    """界面配置"""
    refresh_rate: int = 100  # ms
    theme: str = "light"
    language: str = "zh-CN"
    max_data_points: int = 1000
    window_size: tuple = (1400, 900)


@dataclass
class NetworkConfig:
    """网络配置"""
    opc_server_url: str = "opc.tcp://localhost:4840"
    api_endpoint: str = "http://localhost:8000/api"
    timeout: int = 30
    retry_count: int = 3


class SecureConfigManager:
    """安全的配置管理器"""
    
    def __init__(self, config_file: str = "config.json", key_file: str = "secret.key"):
        self.config_file = config_file
        self.key_file = key_file
        self.cipher = self._setup_encryption()
        self.config = self._load_config()
    
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
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        if not os.path.exists(self.config_file):
            return self._create_default_config()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                encrypted_data = f.read()
                decrypted_data = self.cipher.decrypt(encrypted_data.encode()).decode()
                return json.loads(decrypted_data)
        except Exception as e:
            print(f"加载配置失败: {e}，使用默认配置")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """创建默认配置"""
        default_config = {
            "cameras": [
                {
                    "name": "铅快粗泡沫相机",
                    "rtsp_url": "rtsp://admin:fkqxk010@192.168.1.101:554/Streaming/Channels/101",
                    "position": "粗选",
                    "enabled": True
                }
            ],
            "tanks": [
                {
                    "name": "铅快粗槽",
                    "type": "粗选",
                    "color": "#3498db",
                    "level_range": [0.5, 2.5],
                    "dosing_range": [0, 200]
                }
            ],
            "ui": {
                "refresh_rate": 100,
                "theme": "light",
                "max_data_points": 1000
            },
            "network": {
                "opc_server_url": "opc.tcp://localhost:4840",
                "timeout": 30
            }
        }
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config: Dict[str, Any] = None):
        """保存配置"""
        if config is None:
            config = self.config
        
        try:
            json_data = json.dumps(config, ensure_ascii=False, indent=2)
            encrypted_data = self.cipher.encrypt(json_data.encode())
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(encrypted_data.decode())
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get_camera_configs(self) -> List[CameraConfig]:
        """获取相机配置"""
        return [CameraConfig(**cam) for cam in self.config.get('cameras', [])]
    
    def get_tank_configs(self) -> List[TankConfig]:
        """获取浮选槽配置"""
        return [TankConfig(**tank) for tank in self.config.get('tanks', [])]
    
    def get_ui_config(self) -> UIConfig:
        """获取界面配置"""
        return UIConfig(**self.config.get('ui', {}))
    
    def get_network_config(self) -> NetworkConfig:
        """获取网络配置"""
        return NetworkConfig(**self.config.get('network', {}))
    
    def update_camera_config(self, camera_config: CameraConfig):
        """更新相机配置"""
        cameras = self.config.get('cameras', [])
        for i, cam in enumerate(cameras):
            if cam['name'] == camera_config.name:
                cameras[i] = asdict(camera_config)
                break
        else:
            cameras.append(asdict(camera_config))
        
        self.save_config()


# 全局配置实例
config_manager = SecureConfigManager()


if __name__ == "__main__":
    # 测试配置管理
    manager = SecureConfigManager("test_config.json")
    
    print("相机配置:")
    for cam in manager.get_camera_configs():
        print(f"  - {cam.name}: {cam.rtsp_url}")
    
    print("浮选槽配置:")
    for tank in manager.get_tank_configs():
        print(f"  - {tank.name}: {tank.type}")
    
    print("UI配置:")
    ui_config = manager.get_ui_config()
    print(f"  刷新率: {ui_config.refresh_rate}ms")
