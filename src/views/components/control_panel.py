from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PySide6.QtCore import Signal

# 引入各个页面组件
from ..pages.monitoring_page import MonitoringPage
from ..pages.control_page import ControlPage
from ..pages.history_page import HistoryPage
from ..pages.settings_page import SettingsPage


class ControlPanel(QWidget):
    """右侧控制面板 - 包含功能选项卡"""

    # 信号：当前Tab改变 (index)
    tab_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建选项卡控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #dcdfe6; background: white; }
            QTabBar::tab { height: 35px; min-width: 80px; }
        """)

        # 1. 监控总览
        self.monitoring_page = MonitoringPage()
        self.tab_widget.addTab(self.monitoring_page, "监控总览")

        # 2. 控制参数
        self.control_page_tab = ControlPage()  # 为了不与MainWindow的control_page混淆，命名为tab
        self.tab_widget.addTab(self.control_page_tab, "参数控制")

        # 3. 历史数据
        self.history_page = HistoryPage()
        self.tab_widget.addTab(self.history_page, "历史数据")

        # 4. 系统设置
        # [关键修改] 实例化 SettingsPage 并保存为成员变量，供外部访问
        self.settings_page = SettingsPage()
        self.tab_widget.addTab(self.settings_page, "系统设置")

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