from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QGridLayout, QGroupBox, QLabel)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QImage, QFont
import cv2
import numpy as np

from src.services.logging_service import get_logging_service
from src.services.video_service import get_video_service


class VideoDisplayWidget(QWidget):
    """视频显示组件 - 显示四个泡沫相机视频流"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logging_service()
        self.video_labels = []
        self.video_service = get_video_service()
        self.setup_ui()
        self.setup_video_simulation()
        # self.setup_video_capture()

    def setup_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("泡沫实时监控")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 视频网格布局
        grid_widget = self.create_video_grid()
        layout.addWidget(grid_widget)

    def create_video_grid(self):
        """创建视频网格布局"""
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(5, 5, 5, 5)

        # 四个泡沫相机位置
        camera_configs = [
            {"name": "铅快粗泡沫", "row": 0, "col": 0, "color": "#3498db"},
            {"name": "铅精一泡沫", "row": 0, "col": 1, "color": "#2ecc71"},
            {"name": "铅精二泡沫", "row": 1, "col": 0, "color": "#e74c3c"},
            {"name": "铅精三泡沫", "row": 1, "col": 1, "color": "#9b59b6"}
        ]

        for config in camera_configs:
            camera_widget = self.create_camera_widget(config)
            layout.addWidget(camera_widget, config["row"], config["col"])

        return widget

    def create_camera_widget(self, config):
        """创建单个相机显示组件"""
        group = QGroupBox(config["name"])
        group.setStyleSheet(f"""
            QGroupBox {{
                border: 2px solid {config['color']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {config['color']};
                font-weight: bold;
            }}
        """)

        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 15, 8, 8)

        # 视频显示标签
        video_label = QLabel()
        video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        video_label.setMinimumSize(320, 240)
        video_label.setStyleSheet("""
            QLabel {
                background-color: #2c3e50;
                border: 1px solid #34495e;
                border-radius: 4px;
            }
        """)

        # 状态标签
        status_label = QLabel("模拟模式")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")

        layout.addWidget(video_label)
        layout.addWidget(status_label)

        # 存储引用
        self.video_labels.append({
            'video_label': video_label,
            'status_label': status_label,
            'config': config
        })

        return group

    def setup_video_simulation(self):
        """设置视频模拟"""
        self.video_timer = QTimer()
        self.video_timer.timeout.connect(self.update_video_frames)
        self.video_timer.start(100)  # 10fps

    def update_video_frames(self):
        """更新视频帧显示"""
        # self.logger.info("test","VIDEO")
        for i, video_info in enumerate(self.video_labels):
            # frame = self.generate_simulated_frame(i, video_info['config'])
            frame = self.video_service.capture_frame(i)
            self.display_frame(video_info['video_label'], frame)

    def generate_simulated_frame(self, camera_index, config):
        """生成模拟视频帧"""
        width, height = 320, 240

        # 创建基础图像
        base_color = self.hex_to_rgb(config['color'])
        frame = np.full((height, width, 3), base_color, dtype=np.uint8)

        # 添加噪声
        noise = np.random.randint(0, 30, (height, width, 3), dtype=np.uint8)
        frame = cv2.add(frame, noise)

        # 添加泡沫效果
        bubble_count = [30, 50, 70, 100][camera_index]
        bubble_size_range = [(15, 30), (8, 20), (5, 15), (3, 10)][camera_index]

        for _ in range(bubble_count):
            x = np.random.randint(0, width)
            y = np.random.randint(0, height // 2)
            radius = np.random.randint(bubble_size_range[0], bubble_size_range[1])
            cv2.circle(frame, (x, y), radius, (255, 255, 255), -1)

        # 添加文本
        cv2.putText(frame, config['name'], (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        return frame

    def hex_to_rgb(self, hex_color):
        """将十六进制颜色转换为RGB元组"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    def display_frame(self, label, frame):
        """在QLabel中显示视频帧"""
        try:
            # 转换颜色空间
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w

            # 创建QImage
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line,
                              QImage.Format.Format_RGB888)

            # 缩放图像以适应标签大小
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(
                label.width(),
                label.height(),
                Qt.AspectRatioMode.KeepAspectRatio
            )

            label.setPixmap(scaled_pixmap)

        except Exception as e:
            self.logger.error(f"显示视频帧时出错: {e}", "VIDEO")

    def update_display(self):
        """更新显示（供外部调用）"""
        self.update_video_frames()
