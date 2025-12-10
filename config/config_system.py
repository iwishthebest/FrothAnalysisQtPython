"""
整合版配置管理系统 - 去安全配置版（增强版）
添加相机UI布局配置
"""

import os
import json
from dataclasses import dataclass, asdict, field
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
class CameraLayoutConfig:
    """相机UI布局配置"""
    row: int
    col: int
    ui_color: str
    display_name: str = ""
    visible: bool = True
    width_ratio: float = 1.0
    height_ratio: float = 1.0

    def validate(self) -> bool:
        """验证布局配置有效性"""
        if self.row < 0 or self.col < 0:
            return False
        if not self.ui_color.startswith('#'):
            return False
        if self.width_ratio <= 0 or self.height_ratio <= 0:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CameraLayoutConfig':
        """从字典创建实例"""
        return cls(**data)


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
    # 新增UI布局配置
    layout: CameraLayoutConfig = field(default_factory=lambda: CameraLayoutConfig(0, 0, "#3498db"))

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
        if not self.layout.validate():
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['position'] = self.position.value
        data['simulation_color'] = list(self.simulation_color)
        data['layout'] = self.layout.to_dict()
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

        # 处理layout配置
        if isinstance(data.get('layout'), dict):
            data['layout'] = CameraLayoutConfig.from_dict(data['layout'])
        else:
            # 默认布局配置
            data['layout'] = CameraLayoutConfig(0, 0, "#3498db")

        return cls(**data)

    @classmethod
    def create_default_configs(cls) -> List['CameraConfig']:
        """创建默认相机配置列表"""
        # 定义四个泡沫相机的UI布局配置
        layout_configs = [
            CameraLayoutConfig(row=0, col=0, ui_color="#3498db", display_name="铅快粗泡沫"),
            CameraLayoutConfig(row=0, col=1, ui_color="#2ecc71", display_name="铅精一泡沫"),
            CameraLayoutConfig(row=1, col=0, ui_color="#e74c3c", display_name="铅精二泡沫"),
            CameraLayoutConfig(row=1, col=1, ui_color="#9b59b6", display_name="铅精三泡沫")
        ]

        return [
            cls(
                camera_index=0,
                name="铅快粗泡沫相机",
                rtsp_url="rtsp://admin:fkqxk010@192.168.1.101:554/Streaming/Channels/101",
                position=CameraPosition.LEAD_ROUGH,
                enabled=False,
                simulation_color=(100, 150, 200),  # 蓝色调
                layout=layout_configs[0]
            ),
            cls(
                camera_index=1,
                name="铅精一泡沫相机",
                rtsp_url="rtsp://admin:fkqxk010@192.168.1.102:554/Streaming/Channels/101",
                position=CameraPosition.LEAD_CLEAN_1,
                enabled=False,
                simulation_color=(200, 200, 100),  # 黄色调
                layout=layout_configs[1]
            ),
            cls(
                camera_index=2,
                name="铅精二泡沫相机",
                rtsp_url="rtsp://admin:fkqxk010@192.168.1.103:554/Streaming/Channels/101",
                position=CameraPosition.LEAD_CLEAN_2,
                enabled=False,
                simulation_color=(150, 100, 100),  # 红色调
                layout=layout_configs[2]
            ),
            cls(
                camera_index=3,
                name="铅精三泡沫相机",
                rtsp_url="rtsp://admin:fkqxk010@192.168.1.104:554/Streaming/Channels/101",
                position=CameraPosition.LEAD_CLEAN_3,
                enabled=False,
                simulation_color=(100, 200, 150),  # 绿色调
                layout=layout_configs[3]
            )
        ]

    def get_ui_position(self) -> Tuple[int, int]:
        """获取UI中的位置（行，列）"""
        return (self.layout.row, self.layout.col)

    def get_ui_color(self) -> str:
        """获取UI显示颜色"""
        return self.layout.ui_color

    def get_display_name(self) -> str:
        """获取显示名称"""
        return self.layout.display_name if self.layout.display_name else self.name

    def is_visible(self) -> bool:
        """检查是否可见"""
        return self.layout.visible and self.enabled


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
class UICameraLayoutConfig:
    """相机UI布局整体配置"""
    grid_rows: int = 2
    grid_cols: int = 2
    spacing: int = 10
    aspect_ratio: Tuple[int, int] = (4, 3)
    show_borders: bool = True
    border_color: str = "#bdc3c7"
    border_width: int = 2

    def validate(self) -> bool:
        """验证布局配置有效性"""
        if self.grid_rows <= 0 or self.grid_cols <= 0:
            return False
        if self.spacing < 0:
            return False
        if self.aspect_ratio[0] <= 0 or self.aspect_ratio[1] <= 0:
            return False
        if not self.border_color.startswith('#'):
            return False
        if self.border_width < 0:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['aspect_ratio'] = list(self.aspect_ratio)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UICameraLayoutConfig':
        """从字典创建实例"""
        data = data.copy()
        if isinstance(data.get('aspect_ratio'), list):
            data['aspect_ratio'] = tuple(data['aspect_ratio'])
        return cls(**data)


@dataclass
class DataConfig:
    """数据存储配置"""
    save_path: str = "./data"
    auto_save_interval: int = 10
    save_format: str = "CSV"
    save_images: bool = True
    auto_backup: bool = True
    backup_path: str = "./backup"
    backup_frequency: str = "weekly"
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
    refresh_rate: int = 100
    theme: str = "light"
    language: str = "zh-CN"
    max_data_points: int = 1000
    window_size: Tuple[int, int] = (1400, 900)
    hardware_acceleration: bool = True
    image_quality: str = "balanced"
    # 新增相机布局配置
    camera_layout: UICameraLayoutConfig = field(default_factory=UICameraLayoutConfig)

    def validate(self) -> bool:
        """验证配置有效性"""
        if self.refresh_rate <= 0:
            return False
        if self.max_data_points <= 0:
            return False
        if self.window_size[0] <= 0 or self.window_size[1] <= 0:
            return False
        if not self.camera_layout.validate():
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['window_size'] = list(self.window_size)
        data['camera_layout'] = self.camera_layout.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UIConfig':
        """从字典创建实例"""
        data = data.copy()
        if isinstance(data.get('window_size'), list):
            data['window_size'] = tuple(data['window_size'])

        # 处理相机布局配置
        if isinstance(data.get('camera_layout'), dict):
            data['camera_layout'] = UICameraLayoutConfig.from_dict(data['camera_layout'])
        else:
            data['camera_layout'] = UICameraLayoutConfig()

        return cls(**data)

    def get_theme_colors(self) -> Dict[str, str]:
        """获取主题颜色配置"""
        if self.theme == "dark":
            return {
                'background': '#2c3e50',
                'foreground': '#ecf0f1',
                'primary': '#3498db',
                'secondary': '#2980b9',
                'accent': '#e74c3c'
            }
        else:
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
    opc_server_url: str = "http://10.12.18.2:8081/open/realdata/snapshot/batchGet"
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
    data: DataConfig

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
                self.logger.info(f"加载配置成功，使用{self.config_file}配置", "SYSTEM")
                return SystemConfig.from_dict(config_data)
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}，使用默认配置", "SYSTEM")
            return self._create_default_config()

    def _create_default_config(self) -> SystemConfig:
        """创建默认配置"""
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

        if not config.validate():
            raise ValueError("配置验证失败，请检查配置参数")

        try:
            config_dict = config.to_dict()
            json_data = json.dumps(config_dict, ensure_ascii=False, indent=2)

            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(json_data)

            self.logger.info("配置保存成功", "SYSTEM")
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}", "SYSTEM")
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

    def get_camera_by_position(self, row: int, col: int) -> Optional[CameraConfig]:
        """根据UI位置获取相机配置"""
        for camera in self.system_config.cameras:
            if camera.layout.row == row and camera.layout.col == col:
                return camera
        return None

    def get_visible_cameras(self) -> List[CameraConfig]:
        """获取可见的相机配置"""
        return [cam for cam in self.system_config.cameras if cam.is_visible()]

    def get_camera_grid_dimensions(self) -> Tuple[int, int]:
        """获取相机网格布局的维度"""
        rows = max([cam.layout.row for cam in self.system_config.cameras if cam.is_visible()], default=0) + 1
        cols = max([cam.layout.col for cam in self.system_config.cameras if cam.is_visible()], default=0) + 1
        return (rows, cols)

    def export_config(self, export_path: str):
        """导出配置到指定路径"""
        try:
            config_dict = self.system_config.to_dict()
            json_data = json.dumps(config_dict, ensure_ascii=False, indent=2)

            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(json_data)

            self.logger.info(f"配置已导出到: {export_path}", "SYSTEM")
        except Exception as e:
            self.logger.error(f"导出配置失败: {e}", "SYSTEM")
            raise

    def import_config(self, import_path: str):
        """从指定路径导入配置"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            new_config = SystemConfig.from_dict(config_data)
            self.system_config = new_config
            self.save_config()

            self.logger.info(f"配置已从 {import_path} 导入", "SYSTEM")
        except Exception as e:
            self.logger.error(f"导入配置失败: {e}", "SYSTEM")
            raise


# 全局配置实例
config_manager = ConfigManager()
