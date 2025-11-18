"""
整合版配置管理系统 - 去安全配置版
"""

import os
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

from src.services.logging_service import get_logging_service


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
    camera_index: int
    name: str
    rtsp_url: str
    position: CameraPosition
    simulation_color: Tuple[int, int, int] = (100, 150, 200)
    enabled: bool = True
    timeout: int = 10
    reconnect_interval: int = 5
    max_retries: int = 10
    resolution: str = "1920x1080"
    frame_rate: int = 30
    exposure: float = 10.0
    gain: float = 5.0

    def validate(self) -> bool:
        """验证配置有效性"""
        if not self.name.strip():
            return False
        if not self.rtsp_url.startswith('rtsp://'):
            return False
        if self.timeout <= 0:
            return False
        if self.frame_rate <= 0:
            return False
        if self.exposure < 0:
            return False
        if self.gain < 0:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['position'] = self.position.value
        # 转换tuple为list以便JSON序列化
        data['simulation_color'] = list(self.simulation_color)
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
            else:
                data['position'] = CameraPosition.LEAD_ROUGH

        # 处理simulation_color的list/tuple转换
        if isinstance(data.get('simulation_color'), list):
            data['simulation_color'] = tuple(data['simulation_color'])

        return cls(**data)

    @classmethod
    def create_default_configs(cls) -> List['CameraConfig']:
        """创建默认相机配置列表"""
        return [
            cls(
                camera_index=0,
                name="铅快粗泡沫相机",
                rtsp_url="rtsp://admin:fkqxk010@192.168.1.101:554/Streaming/Channels/101",
                position=CameraPosition.LEAD_ROUGH,
                enabled=False,
                simulation_color=(100, 150, 200)  # 蓝色调
            ),
            cls(
                camera_index=1,
                name="铅精一泡沫相机",
                rtsp_url="rtsp://admin:fkqxk010@192.168.1.102:554/Streaming/Channels/101",
                position=CameraPosition.LEAD_CLEAN_1,
                enabled=False,
                simulation_color=(200, 200, 100),  # 黄色调
            ),
            cls(
                camera_index=2,
                name="铅精二泡沫相机",
                rtsp_url="rtsp://admin:fkqxk010@192.168.1.103:554/Streaming/Channels/101",
                position=CameraPosition.LEAD_CLEAN_2,
                enabled=False,
                simulation_color=(150, 100, 100),  # 红色调
            ),
            cls(
                camera_index=3,
                name="铅精三泡沫相机",
                rtsp_url="rtsp://admin:fkqxk010@192.168.1.104:554/Streaming/Channels/101",
                position=CameraPosition.LEAD_CLEAN_3,
                enabled=False,
                simulation_color=(100, 200, 150),  # 绿色调
            )
        ]


@dataclass
class TankConfig:
    """浮选槽配置"""
    name: str
    type: TankType
    color: str
    level_range: Tuple[float, float] = (0.5, 2.5)
    dosing_range: Tuple[float, float] = (0, 200)
    default_level: float = 1.2
    default_dosing: float = 50

    def validate(self) -> bool:
        """验证配置有效性"""
        if not self.name.strip():
            return False
        if not self.color.startswith('#'):
            return False
        if self.level_range[0] >= self.level_range[1]:
            return False
        if self.dosing_range[0] >= self.dosing_range[1]:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['type'] = self.type.value
        # 转换tuple为list以便JSON序列化
        data['level_range'] = list(self.level_range)
        data['dosing_range'] = list(self.dosing_range)
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
            else:
                data['type'] = TankType.ROUGH

        # 转换list为tuple
        if isinstance(data.get('level_range'), list):
            data['level_range'] = tuple(data['level_range'])
        if isinstance(data.get('dosing_range'), list):
            data['dosing_range'] = tuple(data['dosing_range'])

        return cls(**data)

    @classmethod
    def create_default_configs(cls) -> List['TankConfig']:
        """创建默认浮选槽配置列表"""
        return [
            cls(
                name="铅快粗槽",
                type=TankType.ROUGH,
                color="#3498db",
                level_range=(0.5, 2.5),
                dosing_range=(0, 200)
            ),
            cls(
                name="铅精一槽",
                type=TankType.CLEAN_1,
                color="#2ecc71",
                level_range=(0.5, 2.5),
                dosing_range=(0, 200)
            ),
            cls(
                name="铅精二槽",
                type=TankType.CLEAN_2,
                color="#e74c3c",
                level_range=(0.5, 2.5),
                dosing_range=(0, 200)
            ),
            cls(
                name="铅精三槽",
                type=TankType.CLEAN_3,
                color="#9b59b6",
                level_range=(0.5, 2.5),
                dosing_range=(0, 200)
            )
        ]


@dataclass
class DataConfig:
    """数据存储配置"""
    save_path: str = "./data"
    auto_save_interval: int = 10  # 分钟
    save_format: str = "CSV"
    save_images: bool = True
    auto_backup: bool = True
    backup_path: str = "./backup"
    backup_frequency: str = "weekly"  # daily, weekly, monthly
    auto_cleanup: bool = True
    retention_days: int = 30
    cache_size: int = 500

    def validate(self) -> bool:
        """验证配置有效性"""
        if self.auto_save_interval <= 0:
            return False
        if self.retention_days <= 0:
            return False
        if self.cache_size <= 0:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataConfig':
        """从字典创建实例"""
        return cls(**data)


@dataclass
class UIConfig:
    """界面配置"""
    refresh_rate: int = 100  # ms
    theme: str = "light"
    language: str = "zh-CN"
    max_data_points: int = 1000
    window_size: Tuple[int, int] = (1400, 900)
    hardware_acceleration: bool = True
    image_quality: str = "balanced"

    def validate(self) -> bool:
        """验证配置有效性"""
        if self.refresh_rate <= 0:
            return False
        if self.max_data_points <= 0:
            return False
        if self.window_size[0] <= 0 or self.window_size[1] <= 0:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 转换tuple为list以便JSON序列化
        data['window_size'] = list(self.window_size)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UIConfig':
        """从字典创建实例"""
        data = data.copy()
        # 转换list为tuple
        if isinstance(data.get('window_size'), list):
            data['window_size'] = tuple(data['window_size'])
        return cls(**data)

    def get_theme_colors(self) -> Dict[str, str]:
        """获取主题颜色配置c6整合"""
        if self.theme == "dark":
            return {
                'background': '#2c3e50',
                'foreground': '#ecf0f1',
                'primary': '#3498db',
                'secondary': '#2980b9',
                'accent': '#e74c3c'
            }
        else:  # light theme
            return {
                'background': '#ecf0f1',
                'foreground': '#2c3e50',
                'primary': '#3498db',
                'secondary': '#2980b9',
                'accent': '#e74c3c'
            }


@dataclass
class NetworkConfig:
    """网络配置"""
    opc_server_url: str = "opc.tcp://localhost:4840"
    api_endpoint: str = "http://localhost:8000/api"
    timeout: int = 30
    retry_count: int = 3

    def validate(self) -> bool:
        """验证配置有效性"""
        if self.timeout <= 0:
            return False
        if self.retry_count < 0:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NetworkConfig':
        """从字典创建实例"""
        return cls(**data)


@dataclass
class SystemConfig:
    """系统主配置"""
    cameras: List[CameraConfig]
    tanks: List[TankConfig]
    ui: UIConfig
    network: NetworkConfig
    data: DataConfig  # 新增数据配置

    def validate(self) -> bool:
        """验证所有配置的有效性"""
        if not all(cam.validate() for cam in self.cameras):
            return False
        if not all(tank.validate() for tank in self.tanks):
            return False
        if not self.ui.validate():
            return False
        if not self.network.validate():
            return False
        if not self.data.validate():
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'cameras': [cam.to_dict() for cam in self.cameras],
            'tanks': [tank.to_dict() for tank in self.tanks],
            'ui': self.ui.to_dict(),
            'network': self.network.to_dict(),
            'data': self.data.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemConfig':
        """从字典创建实例"""
        cameras = [CameraConfig.from_dict(cam) for cam in data.get('cameras', [])]
        tanks = [TankConfig.from_dict(tank) for tank in data.get('tanks', [])]
        ui = UIConfig.from_dict(data.get('ui', {}))
        network = NetworkConfig.from_dict(data.get('network', {}))
        data_config = DataConfig.from_dict(data.get('data', {}))

        return cls(
            cameras=cameras,
            tanks=tanks,
            ui=ui,
            network=network,
            data=data_config
        )


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_file: str = "config/config.json"):
        # 确保配置文件路径有效
        if not config_file:
            config_file = "config/config.json"
        self.config_file = config_file
        self.logger = get_logging_service()
        self.system_config = self._load_config()

    def _load_config(self) -> SystemConfig:
        """加载配置"""
        if not os.path.exists(self.config_file):
            return self._create_default_config()

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                self.logger.info(f"加载配置成功，使用{self.config_file}配置")
                return SystemConfig.from_dict(config_data)
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}，使用默认配置")
            return self._create_default_config()

    def _create_default_config(self) -> SystemConfig:
        """创建默认配置 - 使用各配置类的create_default_configs方法"""
        cameras = CameraConfig.create_default_configs()
        tanks = TankConfig.create_default_configs()
        ui = UIConfig()
        network = NetworkConfig()
        data_config = DataConfig()

        system_config = SystemConfig(
            cameras=cameras,
            tanks=tanks,
            ui=ui,
            network=network,
            data=data_config
        )

        self.save_config(system_config)
        return system_config

    def save_config(self, config: SystemConfig = None):
        """保存配置"""
        if config is None:
            config = self.system_config

        # 验证配置有效性
        if not config.validate():
            raise ValueError("配置验证失败，请检查配置参数")

        try:
            config_dict = config.to_dict()
            json_data = json.dumps(config_dict, ensure_ascii=False, indent=2)

            # 确保目录存在
            # os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(json_data)

            self.logger.info("配置保存成功","SYSTEM")
        except Exception as e:
            print(f"保存配置失败: {e}","SYSTEM")
            raise

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

    def get_data_config(self) -> DataConfig:
        """获取数据配置"""
        return self.system_config.data

    def update_camera_config(self, camera_config: CameraConfig):
        """更新相机配置"""
        for i, cam in enumerate(self.system_config.cameras):
            if cam.camera_index == camera_config.camera_index:
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

    def update_ui_config(self, ui_config: UIConfig):
        """更新界面配置"""
        self.system_config.ui = ui_config
        self.save_config()

    def update_network_config(self, network_config: NetworkConfig):
        """更新网络配置"""
        self.system_config.network = network_config
        self.save_config()

    def update_data_config(self, data_config: DataConfig):
        """更新数据配置"""
        self.system_config.data = data_config
        self.save_config()

    def get_camera_by_index(self, index: int) -> Optional[CameraConfig]:
        """根据索引获取相机配置"""
        for camera in self.system_config.cameras:
            if camera.camera_index == index:
                return camera
        return None

    def get_tank_by_name(self, name: str) -> Optional[TankConfig]:
        """根据名称获取浮选槽配置"""
        for tank in self.system_config.tanks:
            if tank.name == name:
                return tank
        return None

    def export_config(self, export_path: str):
        """导出配置到指定路径"""
        try:
            config_dict = self.system_config.to_dict()
            json_data = json.dumps(config_dict, ensure_ascii=False, indent=2)

            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(json_data)

            self.logger.info(f"配置已导出到: {export_path}","SYSTEM")
        except Exception as e:
            self.logger.error(f"导出配置失败: {e}","SYSTEM")
            raise

    def import_config(self, import_path: str):
        """从指定路径导入配置"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            new_config = SystemConfig.from_dict(config_data)
            self.system_config = new_config
            self.save_config()

            self.logger.info(f"配置已从 {import_path} 导入","SYSTEM")
        except Exception as e:
            self.logger.error(f"导入配置失败: {e}","SYSTEM")
            raise


# 全局配置实例
config_manager = ConfigManager()
