import numpy as np
from PySide6.QtWidgets import (QWidget, QGridLayout, QLabel, QFrame,
                               QVBoxLayout, QHBoxLayout, QSizePolicy)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QImage, QPixmap

from config.config_system import config_manager
from src.services.video_service import get_video_service, CameraWorker


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

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)

        # 标题栏
        self.header_bg = QWidget()
        self.header_bg.setFixedHeight(24)
        header_layout = QHBoxLayout(self.header_bg)
        header_layout.setContentsMargins(5, 0, 5, 0)

        self.title_label = QLabel(self.config.get_display_name())
        self.title_label.setStyleSheet("color: white; font-weight: bold;")

        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(10, 10)
        self.status_indicator.setStyleSheet("background-color: #95a5a6; border-radius: 5px;")

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_indicator)
        layout.addWidget(self.header_bg)

        # 视频区域
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setFixedSize(self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT)
        self.video_label.setStyleSheet("background-color: #2c3e50; color: #7f8c8d; font-size: 14px;")
        self.video_label.setText("等待信号..." if self.config.enabled else "已禁用")
        self.video_label.setScaledContents(True)

        layout.addWidget(self.video_label)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def _update_style(self):
        ui_color = self.config.get_ui_color()
        self.setStyleSheet(
            f"VideoFrame {{ border: 1px solid {ui_color}; border-radius: 4px; background-color: #34495e; }}")
        self.header_bg.setStyleSheet(
            f"background-color: {ui_color}; border-top-left-radius: 3px; border-top-right-radius: 3px;")

    @Slot(int, QImage)
    def handle_frame_ready(self, camera_index: int, image: QImage):
        """槽函数：接收已处理好的 QImage 并显示"""
        # 安全检查：确保是发给自己的
        if camera_index != self.camera_index:
            return

        # 直接显示，耗时极低
        self.video_label.setPixmap(QPixmap.fromImage(image))

        # 简单的状态指示 (有信号即绿灯)
        self.status_indicator.setStyleSheet("background-color: #2ecc71; border-radius: 5px;")

    @Slot(int, dict)
    def handle_status_change(self, camera_index: int, status: dict):
        if camera_index != self.camera_index:
            return
        # 这里可以根据 status['status'] 改变指示灯颜色
        pass


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
                # 信号连接：Worker线程 -> UI线程
                worker.frame_ready.connect(frame_widget.handle_frame_ready)
                worker.status_changed.connect(frame_widget.handle_status_change)

    # 注意：不再需要 update_display 方法
