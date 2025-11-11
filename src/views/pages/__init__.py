"""
页面视图包 - 包含所有功能页面
"""

# 导出监测页面
from .monitoring_page import MonitoringPage

# 导出控制页面
from .control_page import ControlPage

# 导出历史数据页面
from .history_page import HistoryPage

# 导出设置页面
from .settings_page import SettingsPage

__all__ = [
    'MonitoringPage',
    'ControlPage',
    'HistoryPage',
    'SettingsPage'
]

# 页面版本信息
__version__ = "1.0.0"
__author__ = "智能监测技术团队"
__description__ = "铅浮选监测系统功能页面"

# 页面配置信息
PAGE_CONFIG = {
    'monitoring': {
        'class': MonitoringPage,
        'name': '实时监测',
        'description': '显示实时数据和图表',
        'icon': 'monitor',
        'order': 0
    },
    'control': {
        'class': ControlPage,
        'name': '控制参数',
        'description': '系统参数设置和控制',
        'icon': 'settings',
        'order': 1
    },
    'history': {
        'class': HistoryPage,
        'name': '历史数据',
        'description': '历史数据查询和分析',
        'icon': 'history',
        'order': 2
    },
    'settings': {
        'class': SettingsPage,
        'name': '系统设置',
        'description': '系统配置和管理',
        'icon': 'gear',
        'order': 3
    }
}

def get_page_info(page_name):
    """获取页面信息"""
    return PAGE_CONFIG.get(page_name, {})

def get_all_pages():
    """获取所有页面信息"""
    return PAGE_CONFIG

def create_page(page_name, *args, **kwargs):
    """动态创建页面实例"""
    page_info = get_page_info(page_name)
    if page_info and 'class' in page_info:
        return page_info['class'](*args, **kwargs)
    else:
        raise ValueError(f"未知页面: {page_name}")

def get_ordered_pages():
    """按顺序获取页面列表"""
    return sorted(PAGE_CONFIG.items(), key=lambda x: x[1]['order'])

# 包初始化函数
def initialize_pages():
    """初始化页面包"""
    print("功能页面初始化完成")
    print(f"可用页面: {len(__all__)} 个")

    # 打印页面信息
    pages = get_ordered_pages()
    for page_key, page_info in pages:
        print(f"- {page_info['name']}: {page_info['description']}")

# 当包被导入时自动初始化
if __name__ != "__main__":
    initialize_pages()