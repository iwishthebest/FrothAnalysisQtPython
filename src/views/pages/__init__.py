"""
页面视图包初始化文件
"""

from .monitoring_page import MonitoringPage
from .control_page import ControlPage
from .history_page import HistoryPage
from .settings_page import SettingsPage

__all__ = [
    'MonitoringPage',
    'ControlPage',
    'HistoryPage',
    'SettingsPage'
]
