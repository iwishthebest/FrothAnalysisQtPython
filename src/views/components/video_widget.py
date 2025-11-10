"""
视频显示组件 - 用于显示RTSP视频流
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel,
                               QGroupBox, QHBoxLayout)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap, QPainter, QColor
import cv2
import numpy as np


class VideoWidget(QWidget):
    """视频显示组件"""

    def __init__(self, camera_name, rtsp_url, parent=None):
        super().__init__(parent)
        self.camera_name = camera_name
        self.rtsp_url = rtsp_url
        self.is_connected = False

        self._setup_ui()
        self._setup_video()

    def _setup_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 视频组框
        group_box = QGroupBox(self.camera_name)
        group_layout = QVBoxLayout(group_box)

        # 视频显示区域
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(320, 240)
        self.video_label.setStyleSheet("""
            QLabel {
                border: 2px solid #cccccc;
                border-radius: 5px;
                background-color: #2c3e50;
            }
        """)

        # 状态指示
        self.status_label = QLabel("连接中...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #e74c3c;")

        group_layout.addWidget(self.video_label)
        group_layout.addWidget(self.status_label)
        layout.addWidget(group_box)

    def _setup_video(self):
        """设置视频流"""
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frame)
        self.timer.start(33)  # 30fps

    def _update_frame(self):
        """更新视频帧"""
        try:
            # 模拟视频帧生成
            frame = self._generate_frame()
            self._display_frame(frame)
            self.status_label.setText("已连接")
            self.status_label.setStyleSheet("color: #2ecc71;")
            self.is_connected = True
        except Exception as e:
            self.status_label.setText(f"错误: {str(e)}")
            self.status_label.setStyleSheet("color: #e74c3c;")
            self.is_connected = False

    def _generate_frame(self):
        """生成模拟视频帧"""
        width, height = 640, 480
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        # 设置背景颜色
        frame[:, :] = [40, 40, 40]  # 深灰色背景

        # 添加相机名称
        cv2.putText(frame, self.camera_name, (50, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # 添加模拟泡沫效果
        if "铅快粗" in self.camera_name:
            self._add_foam_effect(frame, (255, 100, 100), 30)  # 红色泡沫
        elif "铅精一" in self.camera_name:
            self._add_foam_effect(frame, (100, 255, 100), 20)  # 绿色泡沫
        elif "铅精二" in self.camera_name:
            self._add_foam_effect(frame, (100, 100, 255), 15)  # 蓝色泡沫
        elif "铅精三" in self.camera_name:
            self._add_foam_effect(frame, (255, 255, 100), 10)  # 黄色泡沫

        return frame

    def _add_foam_effect(self, frame, color, bubble_count):
        """添加泡沫效果"""
        height, width, _ = frame.shape
        for _ in range(bubble_count):
            x = np.random.randint(0, width)
            y = np.random.randint(0, height // 2)
            radius = np.random.randint(5, 20)
            cv2.circle(frame, (x, y), radius, color, -1)

    def _display_frame(self, frame):
        """显示视频帧"""
        # 转换颜色空间
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w

        # 创建QImage并显示
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line,
                         QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)

        # 缩放以适应标签
        scaled_pixmap = pixmap.scaled(self.video_label.width(),
                                     self.video_label.height(),
                                     Qt.AspectRatioMode.KeepAspectRatio)
        self.video_label.setPixmap(scaled_pixmap)

    def stop(self):
        """停止视频流"""
        self.timer.stop()
