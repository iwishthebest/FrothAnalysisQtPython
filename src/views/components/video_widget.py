import cv2
import numpy as np
from PySide6.QtWidgets import (QWidget, QGridLayout, QLabel, QFrame,
                               QVBoxLayout, QHBoxLayout, QSizePolicy)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QImage, QPixmap, QColor

from config.config_system import config_manager
from src.services.video_service import get_video_service


class VideoFrame(QFrame):
    """单个视频画面帧控件"""

    # 定义固定的显示尺寸 (4:3 比例，经典监控大小)
    DISPLAY_WIDTH = 640
    DISPLAY_HEIGHT = 480

    def __init__(self, camera_config, parent=None):
        super().__init__(parent)
        self.config = camera_config
        self.camera_index = camera_config.camera_index

        # 设置边框样式
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setLineWidth(1)

        # 初始化UI
        self._setup_ui()
        self._update_style()

    def _setup_ui(self):
        """初始化内部布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)

        # 1. 标题栏
        self.header_bg = QWidget()
        self.header_bg.setFixedHeight(24)
        header_layout = QHBoxLayout(self.header_bg)
        header_layout.setContentsMargins(5, 0, 5, 0)

        self.title_label = QLabel(self.config.get_display_name())
        font = self.title_label.font()
        font.setBold(True)
        font.setPointSize(9)
        self.title_label.setFont(font)
        self.title_label.setStyleSheet("color: white;")

        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(10, 10)
        self.status_indicator.setStyleSheet("background-color: #95a5a6; border-radius: 5px;")

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_indicator)

        layout.addWidget(self.header_bg)

        # 2. 视频显示区域
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # [修改点 1] 设置固定大小，防止画面填满全屏
        self.video_label.setFixedSize(self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT)
        self.video_label.setStyleSheet("background-color: #2c3e50; color: #7f8c8d; font-size: 14px;")
        self.video_label.setText("模拟信号" if not self.config.enabled else "等待连接...")
        self.video_label.setScaledContents(True)

        layout.addWidget(self.video_label)

        # 设置 Frame 本身的大小策略为固定，紧贴内容
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def _update_style(self):
        """根据配置更新颜色"""
        ui_color = self.config.get_ui_color()
        self.setStyleSheet(
            f"VideoFrame {{ border: 1px solid {ui_color}; border-radius: 4px; background-color: #34495e; }}")
        self.header_bg.setStyleSheet(
            f"background-color: {ui_color}; border-top-left-radius: 3px; border-top-right-radius: 3px;")

    def update_frame(self, frame_data: np.ndarray):
        """更新视频帧"""
        if frame_data is None:
            self.video_label.setText("无信号")
            self.status_indicator.setStyleSheet("background-color: #e74c3c; border-radius: 5px;")
            self.video_label.setPixmap(QPixmap())
            return

        try:
            # 更新状态灯为绿色
            self.status_indicator.setStyleSheet("background-color: #2ecc71; border-radius: 5px;")

            # [修改点 2] 预先缩放图像到显示尺寸
            # 这能极大提高性能，避免 Qt 渲染巨大的 1080p/4K 图像
            resized_frame = cv2.resize(frame_data, (self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT))

            # OpenCV (BGR) -> Qt (RGB)
            height, width, channel = resized_frame.shape
            bytes_per_line = 3 * width

            rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
            q_img = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)

            self.video_label.setPixmap(QPixmap.fromImage(q_img))

        except Exception as e:
            pass


class VideoDisplayWidget(QWidget):
    """主视频监控网格区域"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_service = get_video_service()
        self.frames = {}
        self.setup_ui()

    def setup_ui(self):
        """根据配置生成网格布局"""
        self.main_layout = QGridLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # [修改点 3] 让整个网格居中

        ui_config = config_manager.get_ui_config()
        spacing = ui_config.camera_layout.spacing

        self.main_layout.setContentsMargins(spacing, spacing, spacing, spacing)
        self.main_layout.setSpacing(spacing)

        # 获取所有在布局配置中标记为可见的相机
        all_cameras = config_manager.get_camera_configs()
        cameras = [cam for cam in all_cameras if cam.layout.visible]

        if not cameras:
            no_cam_label = QLabel("未配置显示任何相机")
            no_cam_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.main_layout.addWidget(no_cam_label, 0, 0)
            return

        # 动态生成画面
        for cam_config in cameras:
            frame = VideoFrame(cam_config)
            row, col = cam_config.get_ui_position()
            self.main_layout.addWidget(frame, row, col)
            self.frames[cam_config.camera_index] = frame

    @Slot()
    def update_display(self):
        """被定时器调用，刷新所有画面"""
        for cam_index, frame_widget in self.frames.items():
            image = self.video_service.capture_frame(cam_index, timeout=0.1)
            frame_widget.update_frame(image)