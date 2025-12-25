import os
from datetime import datetime
import numpy as np
from PySide6.QtWidgets import (QWidget, QGridLayout, QLabel, QFrame,
                               QVBoxLayout, QHBoxLayout, QSizePolicy, QPushButton, QStyle)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QTimer
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
        self.is_paused = False  # 记录当前的暂停状态
        self.current_image = None  # [新增] 用于缓存当前帧以便抓拍

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
        self.header_bg.setFixedHeight(28)
        header_layout = QHBoxLayout(self.header_bg)
        header_layout.setContentsMargins(5, 0, 5, 0)
        header_layout.setSpacing(5)

        # 标题
        self.title_label = QLabel(self.config.get_display_name())
        self.title_label.setStyleSheet("color: white; font-weight: bold;")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        # [控制按钮组]
        # 1. 连接按钮
        self.btn_connect = QPushButton()
        self.btn_connect.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.btn_connect.setToolTip("连接相机")
        self.btn_connect.setFixedSize(22, 22)
        self._set_btn_style(self.btn_connect)

        # 2. 暂停按钮
        self.btn_pause = QPushButton()
        self.btn_pause.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
        self.btn_pause.setToolTip("暂停/冻结画面")
        self.btn_pause.setFixedSize(22, 22)
        self.btn_pause.setCheckable(True)  # 设置为可选中状态
        self._set_btn_style(self.btn_pause)

        # 3. [新增] 抓拍按钮
        self.btn_capture = QPushButton()
        # 使用保存图标 (SP_DialogSaveButton) 或 相机图标
        self.btn_capture.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.btn_capture.setToolTip("采集当前帧 (Snapshot)")
        self.btn_capture.setFixedSize(22, 22)
        self._set_btn_style(self.btn_capture)

        # 4. 断开按钮
        self.btn_disconnect = QPushButton()
        self.btn_disconnect.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.btn_disconnect.setToolTip("断开连接")
        self.btn_disconnect.setFixedSize(22, 22)
        self._set_btn_style(self.btn_disconnect)

        header_layout.addWidget(self.btn_connect)
        header_layout.addWidget(self.btn_pause)
        header_layout.addWidget(self.btn_capture)  # 添加到布局
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
            self.btn_pause.setEnabled(True)
            self.btn_capture.setEnabled(True)  # 启用抓拍
            self.btn_disconnect.setEnabled(True)
        else:
            self.video_label.setText("已禁用 (点击播放连接)")
            self.btn_connect.setEnabled(True)
            self.btn_pause.setEnabled(False)
            self.btn_capture.setEnabled(False)  # 禁用抓拍
            self.btn_disconnect.setEnabled(False)
            self.status_indicator.setStyleSheet("background-color: #7f8c8d; border-radius: 5px;")  # 灰色

        self.video_label.setScaledContents(True)

        layout.addWidget(self.video_label)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def _set_btn_style(self, btn):
        btn.setStyleSheet("""
            QPushButton { background-color: transparent; border: none; border-radius: 3px; }
            QPushButton:hover { background-color: rgba(255, 255, 255, 50); }
            QPushButton:disabled { opacity: 0.3; }
            QPushButton:checked { background-color: rgba(255, 255, 255, 80); border: 1px solid #bdc3c7;}
        """)

    def _update_style(self):
        ui_color = self.config.get_ui_color()
        self.setStyleSheet(
            f"VideoFrame {{ border: 1px solid {ui_color}; border-radius: 4px; background-color: #34495e; }}")
        self.header_bg.setStyleSheet(
            f"background-color: {ui_color}; border-top-left-radius: 3px; border-top-right-radius: 3px;")

    def _setup_connections(self):
        """按钮事件连接"""
        self.btn_connect.clicked.connect(self.on_connect_clicked)
        self.btn_disconnect.clicked.connect(self.on_disconnect_clicked)
        self.btn_pause.clicked.connect(self.on_pause_clicked)
        self.btn_capture.clicked.connect(self.on_capture_clicked)  # [新增]

    def on_connect_clicked(self):
        """点击连接"""
        self.video_label.setText("正在连接...")
        self.btn_connect.setEnabled(False)
        # 重置暂停状态
        self.is_paused = False
        self.btn_pause.setChecked(False)
        self.btn_pause.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))

        get_video_service().start_camera(self.camera_index)

    def on_disconnect_clicked(self):
        """点击断开"""
        self.video_label.setText("正在断开...")
        self.btn_disconnect.setEnabled(False)
        self.btn_pause.setEnabled(False)
        self.btn_capture.setEnabled(False)
        get_video_service().stop_camera(self.camera_index)

    def on_pause_clicked(self, checked):
        """点击暂停/继续"""
        self.is_paused = checked
        if self.is_paused:
            # 切换为"播放"图标，表示点击可恢复
            self.btn_pause.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
            self.btn_pause.setToolTip("恢复画面")
        else:
            # 切换为"暂停"图标
            self.btn_pause.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
            self.btn_pause.setToolTip("暂停/冻结画面")

        get_video_service().pause_camera(self.camera_index, self.is_paused)

    def on_capture_clicked(self):
        """[新增] 点击抓拍"""
        # 如果当前没有缓存帧，尝试从界面获取（适用于暂停状态）
        target_image = self.current_image
        if target_image is None or target_image.isNull():
            pixmap = self.video_label.pixmap()
            if pixmap and not pixmap.isNull():
                target_image = pixmap.toImage()

        if target_image is None or target_image.isNull():
            print(f"相机 {self.config.name} 无图像，无法抓拍")
            return

        try:
            # 确保保存目录存在
            save_dir = "data/snapshots"
            os.makedirs(save_dir, exist_ok=True)

            # 生成文件名: 相机名_时间戳.jpg
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 精确到毫秒
            cam_name = self.config.name.replace(" ", "_")  # 去除空格
            filename = f"{save_dir}/{cam_name}_{timestamp}.jpg"

            # 保存图片
            if target_image.save(filename, "JPG"):
                print(f"截图已保存: {filename}")
                # 视觉反馈：指示灯闪烁白色
                self.status_indicator.setStyleSheet("background-color: #ffffff; border-radius: 5px;")
                QTimer.singleShot(200, lambda: self.handle_status_change(
                    self.camera_index,
                    {'status': 'connected' if not self.is_paused else 'simulation'}  # 简单恢复颜色
                ))
            else:
                print(f"保存截图失败: {filename}")

        except Exception as e:
            print(f"抓拍过程发生异常: {e}")

    @Slot(int, QImage)
    def handle_frame_ready(self, camera_index: int, image: QImage):
        if camera_index != self.camera_index:
            return

        # [新增] 缓存当前帧用于抓拍
        self.current_image = image

        # 如果前端认为暂停了，也不更新（虽然 Worker 已经不发了，双重保险）
        if not self.is_paused:
            self.video_label.setPixmap(QPixmap.fromImage(image))
            self.status_indicator.setStyleSheet("background-color: #2ecc71; border-radius: 5px;")

    @Slot(int, dict)
    def handle_status_change(self, camera_index: int, status: dict):
        if camera_index != self.camera_index:
            return

        status_code = status.get('status')

        # 根据状态更新按钮可用性
        if status_code in ['connected', 'simulation']:
            self.btn_connect.setEnabled(False)
            self.btn_disconnect.setEnabled(True)
            self.btn_pause.setEnabled(True)
            self.btn_capture.setEnabled(True)  # 连接成功允许抓拍

            color = "#2ecc71" if status_code == 'connected' else "#f39c12"  # 绿/橙
            self.status_indicator.setStyleSheet(f"background-color: {color}; border-radius: 5px;")

        elif status_code == 'stopped':
            self.video_label.setText("已断开")
            self.video_label.setPixmap(QPixmap())  # 清除画面
            self.current_image = None  # 清除缓存

            self.btn_connect.setEnabled(True)
            self.btn_disconnect.setEnabled(False)
            self.btn_pause.setEnabled(False)
            self.btn_capture.setEnabled(False)
            self.btn_pause.setChecked(False)  # 重置选中状态
            self.is_paused = False

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