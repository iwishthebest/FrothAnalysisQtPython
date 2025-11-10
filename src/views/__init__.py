"""
视图层包初始化文件 - 导出所有视图组件
"""

from .main_window import FoamMonitoringSystem
from .components.video_widget import VideoWidget
from .components.tank_widget import TankWidget, TankGraphicWidget
from .components.control_panel import ControlPanel
from .components.status_bar import StatusBar

__all__ = [
    'FoamMonitoringSystem',
    'VideoWidget',
    'TankWidget',
    'TankGraphicWidget',
    'ControlPanel',
    'StatusBar'
]
