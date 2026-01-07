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
        self.current_image = None  # 缓存当前帧以便抓拍

        # [新增] 连续采集相关属性
        self.is_recording = False
        self.record_timer = QTimer(self)
        self.record_timer.timeout.connect(self.save_frame_for_record)
        self.record_interval = 1000  # 连续采集间隔(ms)

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
        self.btn_pause.setCheckable(True)
        self._set_btn_style(self.btn_pause)

        # 3. 单帧抓拍按钮
        self.btn_capture = QPushButton()
        self.btn_capture.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.btn_capture.setToolTip("单帧抓拍 (Snapshot)")
        self.btn_capture.setFixedSize(22, 22)
        self._set_btn_style(self.btn_capture)

        # 4. [新增] 连续采集按钮 (Start/Stop)
        self.btn_record = QPushButton()
        # 默认显示"电脑/设备"图标代表采集
        self.btn_record.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        self.btn_record.setToolTip("开始连续采集")
        self.btn_record.setFixedSize(22, 22)
        self.btn_record.setCheckable(True)  # 设置为开关按钮
        self._set_btn_style(self.btn_record)

        # 5. 断开按钮
        self.btn_disconnect = QPushButton()
        self.btn_disconnect.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.btn_disconnect.setToolTip("断开连接")
        self.btn_disconnect.setFixedSize(22, 22)
        self._set_btn_style(self.btn_disconnect)

        header_layout.addWidget(self.btn_connect)
        header_layout.addWidget(self.btn_pause)
        header_layout.addWidget(self.btn_capture)
        header_layout.addWidget(self.btn_record)  # 添加到布局
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
            self.btn_capture.setEnabled(True)
            self.btn_record.setEnabled(True)
            self.btn_disconnect.setEnabled(True)
        else:
            self.video_label.setText("已禁用 (点击播放连接)")
            self.btn_connect.setEnabled(True)
            self.btn_pause.setEnabled(False)
            self.btn_capture.setEnabled(False)
            self.btn_record.setEnabled(False)
            self.btn_disconnect.setEnabled(False)
            self.status_indicator.setStyleSheet("background-color: #7f8c8d; border-radius: 5px;")

        self.video_label.setScaledContents(True)

        layout.addWidget(self.video_label)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def _set_btn_style(self, btn):
        btn.setStyleSheet("""
            QPushButton { background-color: transparent; border: none; border-radius: 3px; }
            QPushButton:hover { background-color: rgba(255, 255, 255, 50); }
            QPushButton:disabled { opacity: 0.3; }
            QPushButton:checked { background-color: rgba(255, 100, 100, 150); border: 1px solid #e74c3c;}
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
        self.btn_capture.clicked.connect(self.on_capture_clicked)
        self.btn_record.clicked.connect(self.on_record_clicked)  # [新增]

    def on_connect_clicked(self):
        """点击连接"""
        self.video_label.setText("正在连接...")
        self.btn_connect.setEnabled(False)
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
        self.btn_record.setEnabled(False)
        self.stop_recording()  # 断开时必须停止录制
        get_video_service().stop_camera(self.camera_index)

    def on_pause_clicked(self, checked):
        """点击暂停/继续"""
        self.is_paused = checked
        if self.is_paused:
            self.btn_pause.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
            self.btn_pause.setToolTip("恢复画面")
        else:
            self.btn_pause.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
            self.btn_pause.setToolTip("暂停/冻结画面")
        get_video_service().pause_camera(self.camera_index, self.is_paused)

    def on_capture_clicked(self):
        """点击单帧抓拍"""
        self._save_image(is_continuous=False)

    def on_record_clicked(self, checked):
        """[新增] 点击连续采集"""
        if checked:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """开始连续采集"""
        if self.is_recording: return
        self.is_recording = True
        self.btn_record.setChecked(True)
        # 切换图标为停止
        self.btn_record.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.btn_record.setToolTip("停止连续采集")
        # 启动定时器
        self.record_timer.start(self.record_interval)
        print(f"相机 {self.config.name} 开始连续采集")

    def stop_recording(self):
        """停止连续采集"""
        if not self.is_recording: return
        self.is_recording = False
        self.btn_record.setChecked(False)
        # 切换回开始图标
        self.btn_record.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        self.btn_record.setToolTip("开始连续采集")
        self.record_timer.stop()
        print(f"相机 {self.config.name} 停止连续采集")

    def save_frame_for_record(self):
        """定时器回调：保存连续帧"""
        if self.is_recording:
            self._save_image(is_continuous=True)

    def _save_image(self, is_continuous=False):
        """[核心] 保存图片逻辑，支持分文件夹"""
        target_image = self.current_image
        # 如果没有缓存帧，尝试从UI获取（适用于暂停时抓拍）
        if target_image is None or target_image.isNull():
            pixmap = self.video_label.pixmap()
            if pixmap and not pixmap.isNull():
                target_image = pixmap.toImage()

        if target_image is None or target_image.isNull():
            if not is_continuous:  # 只有手动抓拍才打印无图像警告，避免连续采集刷屏
                print(f"相机 {self.config.name} 无图像，无法保存")
            return

        try:
            # 1. 确定保存目录
            # 根据相机名称创建独立文件夹，去除空格等非法字符
            cam_folder_name = self.config.name.replace(" ", "_")

            # 基础路径 + 模式(snapshot/continuous) + 相机名
            # 例如: data/snapshots/铅快粗泡沫相机/
            mode_folder = "continuous" if is_continuous else "snapshots"
            save_dir = f"data/{mode_folder}/{cam_folder_name}"

            os.makedirs(save_dir, exist_ok=True)

            # 2. 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            prefix = "REC" if is_continuous else "SNAP"
            filename = f"{save_dir}/{prefix}_{timestamp}.jpg"

            # 3. 保存
            if target_image.save(filename, "JPG"):
                if not is_continuous:
                    print(f"截图已保存: {filename}")
                    # 手动抓拍给予视觉反馈
                    self.status_indicator.setStyleSheet("background-color: #ffffff; border-radius: 5px;")
                    QTimer.singleShot(200, lambda: self.handle_status_change(
                        self.camera_index,
                        {'status': 'connected' if not self.is_paused else 'simulation'}
                    ))
            else:
                print(f"保存失败: {filename}")

        except Exception as e:
            print(f"保存图像异常: {e}")

    @Slot(int, QImage)
    def handle_frame_ready(self, camera_index: int, image: QImage):
        if camera_index != self.camera_index:
            return

        self.current_image = image

        if not self.is_paused:
            self.video_label.setPixmap(QPixmap.fromImage(image))
            # 录制中显示红色指示灯，否则绿色
            color = "#e74c3c" if self.is_recording else "#2ecc71"
            self.status_indicator.setStyleSheet(f"background-color: {color}; border-radius: 5px;")

    @Slot(int, dict)
    def handle_status_change(self, camera_index: int, status: dict):
        if camera_index != self.camera_index:
            return

        status_code = status.get('status')

        if status_code in ['connected', 'simulation']:
            self.btn_connect.setEnabled(False)
            self.btn_disconnect.setEnabled(True)
            self.btn_pause.setEnabled(True)
            self.btn_capture.setEnabled(True)
            self.btn_record.setEnabled(True)

            color = "#2ecc71" if status_code == 'connected' else "#f39c12"
            if self.is_recording: color = "#e74c3c"  # 录制状态优先显示红灯
            self.status_indicator.setStyleSheet(f"background-color: {color}; border-radius: 5px;")

        elif status_code == 'stopped':
            self.video_label.setText("已断开")
            self.video_label.setPixmap(QPixmap())
            self.current_image = None

            # 断开时停止录制
            self.stop_recording()

            self.btn_connect.setEnabled(True)
            self.btn_disconnect.setEnabled(False)
            self.btn_pause.setEnabled(False)
            self.btn_capture.setEnabled(False)
            self.btn_record.setEnabled(False)
            self.btn_pause.setChecked(False)
            self.is_paused = False

            self.status_indicator.setStyleSheet("background-color: #7f8c8d; border-radius: 5px;")

        elif status_code == 'starting':
            self.video_label.setText("正在启动...")
            self.status_indicator.setStyleSheet("background-color: #f1c40f; border-radius: 5px;")


class VideoDisplayWidget(QWidget):
    """主视频监控网格区域"""

    # ... (保持不变，省略以节省空间，因为 VideoDisplayWidget 没有逻辑变更)
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
        for cam_index, frame_widget in self.frames.items():
            worker = self.video_service.get_worker(cam_index)
            if worker:
                worker.frame_ready.connect(frame_widget.handle_frame_ready)
                worker.status_changed.connect(frame_widget.handle_status_change)