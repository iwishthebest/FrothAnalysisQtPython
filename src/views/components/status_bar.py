from PySide6.QtWidgets import QStatusBar, QLabel
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from datetime import datetime


class StatusBar(QStatusBar):
    """状态栏组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        """初始化用户界面"""
        # 系统状态
        self.status_label = QLabel("系统运行正常")
        self.status_label.setFont(QFont("Microsoft YaHei", 9))
        self.addWidget(self.status_label)
        
        # 时间显示
        self.time_label = QLabel()
        self.time_label.setFont(QFont("Microsoft YaHei", 9))
        self.addPermanentWidget(self.time_label)
        
        # 连接状态
        self.connection_label = QLabel("PLC: 已连接 | 相机: 4/4 正常")
        self.connection_label.setFont(QFont("Microsoft YaHei", 9))
        self.addPermanentWidget(self.connection_label)
        
        self.update_time()
        
    def setup_timer(self):
        """设置定时器"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # 1秒更新一次
        
    def update_time(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)
        
    def update_display(self):
        """更新状态显示"""
        # 可以在这里更新连接状态等信息
        pass
        
    def set_status(self, message, is_error=False):
        """设置状态消息"""
        color = "#e74c3c" if is_error else "#27ae60"
        self.status_label.setStyleSheet(f"color: {color};")
        self.status_label.setText(message)