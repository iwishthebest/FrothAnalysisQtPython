from PySide6.QtWidgets import QStatusBar, QLabel
from PySide6.QtCore import QTimer, Slot
from PySide6.QtGui import QFont
from datetime import datetime


class StatusBar(QStatusBar):
    """状态栏组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # 用于记录每个相机的连接状态 {index: is_connected}
        self.camera_states = {}
        self.total_cameras = 4  # 默认4路，也可从配置读取

        self.setup_ui()
        self.setup_timer()

    def setup_ui(self):
        """初始化用户界面"""
        # 1. 左侧系统消息
        self.status_label = QLabel("系统就绪")
        self.status_label.setFont(QFont("Microsoft YaHei", 9))
        self.addWidget(self.status_label, 1)

        # --- 右侧 ---

        # 2. OPC 状态
        self.opc_label = QLabel("OPC: 等待连接")
        self.opc_label.setFont(QFont("Microsoft YaHei", 9))
        self.opc_label.setStyleSheet("padding: 0 10px; color: #7f8c8d;")
        self.addPermanentWidget(self.opc_label)

        # 3. [修改] 动态相机状态
        self.camera_label = QLabel(f"相机: 0/{self.total_cameras} 在线")
        self.camera_label.setFont(QFont("Microsoft YaHei", 9))
        self.camera_label.setStyleSheet("color: #7f8c8d; padding: 0 10px;")
        self.addPermanentWidget(self.camera_label)

        # 4. 时间
        self.time_label = QLabel()
        self.time_label.setFont(QFont("Microsoft YaHei", 9))
        self.time_label.setStyleSheet("padding: 0 10px; font-weight: bold;")
        self.addPermanentWidget(self.time_label)

        self.update_time()

    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

    def update_time(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)

    @Slot(bool, str)
    def update_opc_status(self, connected: bool, message: str):
        color = "#27ae60" if connected else "#e74c3c"
        icon = "🟢" if connected else "🔴"
        self.opc_label.setStyleSheet(f"color: {color}; font-weight: bold; padding: 0 10px;")
        self.opc_label.setText(f"OPC: {message} {icon}")

    @Slot(int, dict)
    def update_camera_status(self, camera_index: int, status_info: dict):
        """
        [新增] 接收单个相机的状态变更并更新总数显示
        """
        status_code = status_info.get('status', '')
        # 判断是否为正常连接状态
        is_online = (status_code == 'connected')

        # 更新该相机的状态记录
        self.camera_states[camera_index] = is_online

        # 统计当前在线数量
        online_count = sum(1 for status in self.camera_states.values() if status)

        # 更新 UI
        if online_count == self.total_cameras:
            # 全都在线，绿色
            self.camera_label.setStyleSheet("color: #27ae60; font-weight: bold; padding: 0 10px;")
            self.camera_label.setText(f"相机: 全部在线 ({online_count}/{self.total_cameras}) 🟢")
        elif online_count == 0:
            # 全部掉线，红色
            self.camera_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 0 10px;")
            self.camera_label.setText(f"相机: 全部离线 🔴")
        else:
            # 部分在线，橙色
            self.camera_label.setStyleSheet("color: #f39c12; font-weight: bold; padding: 0 10px;")
            self.camera_label.setText(f"相机: {online_count}/{self.total_cameras} 在线 🟠")

    def update_display(self):
        pass