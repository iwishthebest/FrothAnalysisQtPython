"""
视图组件包 - 包含所有可复用的UI组件
"""

# 导出视频相关组件
from .video_widget import VideoDisplayWidget

# 导出浮选槽相关组件
from .tank_widget import TankVisualizationWidget, SingleTankWidget, TankGraphicWidget

# 导出控制面板组件
from .control_panel import ControlPanel

# 导出状态栏组件
from .status_bar import StatusBar

__all__ = [
    'VideoDisplayWidget',
    'TankVisualizationWidget',
    'SingleTankWidget',
    'TankGraphicWidget',
    'ControlPanel',
    'StatusBar'
]

# 组件版本信息
__version__ = "1.0.0"
__author__ = "智能监测技术团队"
__description__ = "铅浮选监测系统UI组件库"

# 组件类别信息
COMPONENT_CATEGORIES = {
    'video': ['VideoDisplayWidget'],
    'tank': ['TankVisualizationWidget', 'SingleTankWidget', 'TankGraphicWidget'],
    'control': ['ControlPanel'],
    'status': ['StatusBar']
}


def get_available_components():
    """获取所有可用组件列表"""
    return {
        'video': {
            'VideoDisplayWidget': '四路视频显示组件'
        },
        'tank': {
            'TankVisualizationWidget': '浮选槽串联可视化组件',
            'SingleTankWidget': '单个浮选槽控制组件',
            'TankGraphicWidget': '浮选槽图形显示组件'
        },
        'control': {
            'ControlPanel': '右侧控制面板组件'
        },
        'status': {
            'StatusBar': '系统状态栏组件'
        }
    }


def create_component(component_name, *args, **kwargs):
    """动态创建组件实例"""
    components = {
        'VideoDisplayWidget': VideoDisplayWidget,
        'TankVisualizationWidget': TankVisualizationWidget,
        'SingleTankWidget': SingleTankWidget,
        'TankGraphicWidget': TankGraphicWidget,
        'ControlPanel': ControlPanel,
        'StatusBar': StatusBar
    }

    if component_name in components:
        return components[component_name](*args, **kwargs)
    else:
        raise ValueError(f"未知组件: {component_name}")


# 包初始化函数
def initialize_components():
    """初始化组件包"""
    print("UI组件库初始化完成")
    print(f"可用组件: {len(__all__)} 个")

    # 打印组件分类信息
    available_comps = get_available_components()
    for category, comps in available_comps.items():
        print(f"{category}: {len(comps)} 个组件")


# 当包被导入时自动初始化
if __name__ != "__main__":
    initialize_components()
