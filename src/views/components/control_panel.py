from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget)
from PySide6.QtCore import Signal

from ..pages.monitoring_page import MonitoringPage
from ..pages.control_page import ControlPage
from ..pages.history_page import HistoryPage
from ..pages.settings_page import SettingsPage


class ControlPanel(QWidget):
    """控制面板组件 - 包含所有功能选项卡"""
    
    # 信号定义
    tab_changed = Signal(int)  # 选项卡索引
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)
        
        # 创建选项卡控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        
        # 创建各个页面
        self.monitoring_page = MonitoringPage()
        self.control_page = ControlPage()
        self.history_page = HistoryPage()
        self.settings_page = SettingsPage()
        
        # 添加选项卡
        self.tab_widget.addTab(self.monitoring_page, "实时监测")
        self.tab_widget.addTab(self.control_page, "控制参数")
        self.tab_widget.addTab(self.history_page, "历史数据")
        self.tab_widget.addTab(self.settings_page, "系统设置")
        
        layout.addWidget(self.tab_widget)
        
    def setup_connections(self):
        """设置信号连接"""
        self.tab_widget.currentChanged.connect(self.tab_changed.emit)