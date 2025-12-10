"""
配置管理模块 - 统一管理所有系统配置
导出整合后的配置类和管理器
"""

from .config_system import (
    CameraConfig, TankConfig, UIConfig, NetworkConfig, SystemConfig, DataConfig,
    CameraPosition, TankType, ConfigManager, config_manager
)

__all__ = [
    'CameraConfig', 'TankConfig', 'UIConfig', 'NetworkConfig', 'SystemConfig', 'DataConfig',
    'CameraPosition', 'TankType', 'ConfigManager', 'config_manager'
]