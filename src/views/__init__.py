"""
视图层包 - 包含主窗口和所有UI组件
"""

from .main_window import FoamMonitoringSystem

__all__ = ['FoamMonitoringSystem']

# 版本信息
__version__ = "2.1.0"
__author__ = "智能监测技术团队"
__description__ = "铅浮选过程工况智能监测与控制系统视图层"

# 导出主要组件
try:
    from .components.video_widget import VideoDisplayWidget
    from .components.tank_widget import TankVisualizationWidget, SingleTankWidget
    from .components.control_panel import ControlPanel
    from .components.status_bar import StatusBar

    # 导出页面组件
    from .pages.monitoring_page import MonitoringPage
    from .pages.control_page import ControlPage
    from .pages.history_page import HistoryPage
    from .pages.settings_page import SettingsPage

    # 扩展导出列表
    __all__.extend([
        'VideoDisplayWidget',
        'TankVisualizationWidget',
        'SingleTankWidget',
        'ControlPanel',
        'StatusBar',
        'MonitoringPage',
        'ControlPage',
        'HistoryPage',
        'SettingsPage'
    ])

except ImportError as e:
    print(f"导入视图组件时出错: {e}")


# 包初始化函数
def initialize_views():
    """初始化视图层组件"""
    print("铅浮选监测系统视图层初始化完成")
    print(f"版本: {__version__}")
    print(f"描述: {__description__}")


# 当包被导入时自动初始化
if __name__ != "__main__":
    pass
    # initialize_views()
