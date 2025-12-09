import sys
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QLabel,
                               QFrame, QSizePolicy)
from PySide6.QtCore import Signal, Qt

# 导入各页面组件
from ..pages.monitoring_page import MonitoringPage
from ..pages.control_page import ControlPage
from ..pages.history_page import HistoryPage
from ..pages.settings_page import SettingsPage


class ControlPanel(QWidget):
    """右侧控制面板容器"""

    # 转发 Tab 切换信号
    tab_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """初始化 UI 布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. 顶部标题栏 (可选，增加一点层级感)
        self.header = QFrame()
        self.header.setFixedHeight(40)
        self.header.setStyleSheet("background-color: #ecf0f1; border-bottom: 1px solid #bdc3c7;")
        header_layout = QVBoxLayout(self.header)
        header_layout.setContentsMargins(15, 0, 0, 0)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        title_label = QLabel("SYSTEM CONTROL")
        title_label.setStyleSheet("font-weight: bold; color: #7f8c8d; letter-spacing: 1px;")
        header_layout.addWidget(title_label)
        layout.addWidget(self.header)

        # 2. 主要 Tab 控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)

        # 初始化各个页面
        self.monitoring_page = MonitoringPage()
        self.control_page = ControlPage()
        self.history_page = HistoryPage()
        self.settings_page = SettingsPage()

        # 添加页面
        self.tab_widget.addTab(self.monitoring_page, " 实时监控 ")
        self.tab_widget.addTab(self.control_page, " 过程控制 ")
        self.tab_widget.addTab(self.history_page, " 历史趋势 ")
        self.tab_widget.addTab(self.settings_page, " 系统设置 ")

        layout.addWidget(self.tab_widget)

        # 应用现代样式的 QSS
        self._apply_styles()

    def _apply_styles(self):
        """应用自定义样式表"""
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #f5f6fa;
                border-top: 2px solid #3498db;
            }
            QTabBar::tab {
                background: #ecf0f1;
                color: #7f8c8d;
                padding: 10px 20px;
                border: none;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-family: "Microsoft YaHei", sans-serif;
                font-size: 14px;
                min-width: 80px;
            }
            QTabBar::tab:hover {
                background: #dcdde1;
            }
            QTabBar::tab:selected {
                background: #3498db;
                color: white;
                font-weight: bold;
            }
        """)

    def setup_connections(self):
        """连接信号"""
        self.tab_widget.currentChanged.connect(self.tab_changed)