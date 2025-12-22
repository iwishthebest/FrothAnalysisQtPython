import numpy as np
from PySide6.QtWidgets import (QWidget, QGridLayout, QLabel, QFrame,
                               QVBoxLayout, QHBoxLayout, QSizePolicy, QPushButton, QStyle)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QImage, QPixmap, QIcon

from config.config_system import config_manager
from src.services.video_service import get_video_service


class VideoFrame(QFrame):
    """单个视频画面帧控件"""

    DISPLAY_WIDTH = 640
    DISPLAY_HEIGHT = 480

    def __init__(self, camera_config, parent=None):
        super().__init__(parent)
        self.config = camera_config
        self.camera_index = camera_config.camera_index

        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setLineWidth(1)
        self._setup_ui()
        self._update_style()
        self._setup_connections()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)

        # === 1. 标题栏 ===
        self.header_bg = QWidget()
        self.header_bg.setFixedHeight(28)  # 稍微加高一点以容纳按钮
        header_layout = QHBoxLayout(self.header_bg)
        header_layout.setContentsMargins(5, 0, 5, 0)
        header_layout.setSpacing(5)

        # 标题
        self.title_label = QLabel(self.config.get_display_name())
        self.title_label.setStyleSheet("color: white; font-weight: bold;")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        # [新增] 控制按钮
        # 连接按钮
        self.btn_connect = QPushButton()
        self.btn_connect.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.btn_connect.setToolTip("连接相机")
        self.btn_connect.setFixedSize(22, 22)
        self.btn_connect.setStyleSheet("""
            QPushButton { background-color: transparent; border: none; border-radius: 3px; }
            QPushButton:hover { background-color: rgba(255, 255, 255, 50); }
            QPushButton:disabled { opacity: 0.5; }
        """)

        # 断开按钮
        self.btn_disconnect = QPushButton()
        self.btn_disconnect.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.btn_disconnect.setToolTip("断开连接")
        self.btn_disconnect.setFixedSize(22, 22)
        self.btn_disconnect.setStyleSheet(self.btn_connect.styleSheet())

        header_layout.addWidget(self.btn_connect)
        header_layout.addWidget(self.btn_disconnect)

        # 状态指示灯
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(10, 10)
        self.status_indicator.setStyleSheet("background-color: #95a5a6; border-radius: 5px;")
        header_layout.addWidget(self.status_indicator)

        layout.addWidget(self.header_bg)

        # === 2. 视频区域 ===
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setFixedSize(self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT)
        self.video_label.setStyleSheet("background-color: #2c3e50; color: #7f8c8d; font-size: 14px;")

        # 初始显示状态
        if self.config.enabled:
            self.video_label.setText("等待信号...")
            self.btn_connect.setEnabled(False)
            self.btn_disconnect.setEnabled(True)
        else:
            self.video_label.setText("已禁用 (点击播放连接)")
            self.btn_connect.setEnabled(True)
            self.btn_disconnect.setEnabled(False)
            self.status_indicator.setStyleSheet("background-color: #7f8c8d; border-radius: 5px;")  # 灰色

        self.video_label.setScaledContents(True)

        layout.addWidget(self.video_label)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def _update_style(self):
        ui_color = self.config.get_ui_color()
        self.setStyleSheet(
            f"VideoFrame {{ border: 1px solid {ui_color}; border-radius: 4px; background-color: #34495e; }}")
        self.header_bg.setStyleSheet(
            f"background-color: {ui_color}; border-top-left-radius: 3px; border-top-right-radius: 3px;")

    def _setup_connections(self):
        """连接按钮点击事件"""
        self.btn_connect.clicked.connect(self.on_connect_clicked)
        self.btn_disconnect.clicked.connect(self.on_disconnect_clicked)

    def on_connect_clicked(self):
        """点击连接"""
        self.video_label.setText("正在连接...")
        self.btn_connect.setEnabled(False)  # 防止重复点击
        get_video_service().start_camera(self.camera_index)

    def on_disconnect_clicked(self):
        """点击断开"""
        self.video_label.setText("正在断开...")
        self.btn_disconnect.setEnabled(False)
        get_video_service().stop_camera(self.camera_index)

    @Slot(int, QImage)
    def handle_frame_ready(self, camera_index: int, image: QImage):
        if camera_index != self.camera_index:
            return
        self.video_label.setPixmap(QPixmap.fromImage(image))
        # 收到帧意味着连接正常，亮绿灯
        self.status_indicator.setStyleSheet("background-color: #2ecc71; border-radius: 5px;")

    @Slot(int, dict)
    def handle_status_change(self, camera_index: int, status: dict):
        if camera_index != self.camera_index:
            return

        status_code = status.get('status')
        msg = status.get('message', '')

        # 根据状态更新按钮可用性
        if status_code in ['connected', 'simulation']:
            self.btn_connect.setEnabled(False)
            self.btn_disconnect.setEnabled(True)
            color = "#2ecc71" if status_code == 'connected' else "#f39c12"  # 绿/橙
            self.status_indicator.setStyleSheet(f"background-color: {color}; border-radius: 5px;")

        elif status_code == 'stopped':
            self.video_label.setText("已断开")
            self.video_label.setPixmap(QPixmap())  # 清除画面
            self.btn_connect.setEnabled(True)
            self.btn_disconnect.setEnabled(False)
            self.status_indicator.setStyleSheet("background-color: #7f8c8d; border-radius: 5px;")  # 灰

        elif status_code == 'starting':
            self.video_label.setText("正在启动...")
            self.status_indicator.setStyleSheet("background-color: #f1c40f; border-radius: 5px;")  # 黄


class VideoDisplayWidget(QWidget):
    """主视频监控网格区域"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_service = get_video_service()
        self.frames = {}
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        self.main_layout = QGridLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ui_config = config_manager.get_ui_config()
        spacing = ui_config.camera_layout.spacing
        self.main_layout.setContentsMargins(spacing, spacing, spacing, spacing)
        self.main_layout.setSpacing(spacing)

        all_cameras = config_manager.get_camera_configs()
        # 显示所有配置中 layout.visible=True 的相机
        visible_cameras = [cam for cam in all_cameras if cam.layout.visible]

        if not visible_cameras:
            no_cam_label = QLabel("未配置显示任何相机")
            no_cam_label.setStyleSheet("color: #7f8c8d; font-size: 18px;")
            self.main_layout.addWidget(no_cam_label, 0, 0)
            return

        for cam_config in visible_cameras:
            frame = VideoFrame(cam_config)
            row, col = cam_config.get_ui_position()
            self.main_layout.addWidget(frame, row, col)
            self.frames[cam_config.camera_index] = frame

    def setup_connections(self):
        """连接所有相机的 Worker 信号"""
        for cam_index, frame_widget in self.frames.items():
            worker = self.video_service.get_worker(cam_index)
            if worker:
                worker.frame_ready.connect(frame_widget.handle_frame_ready)
                worker.status_changed.connect(frame_widget.handle_status_change)