from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QGridLayout, QGroupBox, QLabel, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPixmap, QImage, QFont
import cv2

from src.services.logging_service import get_logging_service
from src.services.video_service import get_video_service


class VideoDisplayWidget(QWidget):
    """视频显示组件 - 显示四个泡沫相机视频流"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logging_service()
        self.video_labels = []
        self.video_service = get_video_service()
        self.video_timer = None
        self.setup_ui()
        self.setup_video_simulation()

    def setup_ui(self):
        """初始化用户界面"""
        # 主布局使用垂直布局，添加适当边距
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)  # 增加外边框
        main_layout.setSpacing(20)  # 增加控件间距

        # 标题区域
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题标签
        title_label = QLabel("泡沫实时监控")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))  # 增大标题字体
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50;")  # 加深标题颜色
        
        # 标题两侧添加弹簧，使标题居中且在窗口缩放时保持居中
        title_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        title_layout.addWidget(title_label)
        title_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        main_layout.addWidget(title_container)

        # 视频网格区域 - 使用带容器的布局，方便控制整体大小
        video_container = QWidget()
        video_container.setStyleSheet("""
            background-color: #f5f5f5;
            border-radius: 10px;
            padding: 10px;
        """)  # 增加背景和圆角，突出视频区域
        
        grid_layout = QGridLayout(video_container)
        grid_layout.setSpacing(20)  # 增大视频之间的间距
        grid_layout.setContentsMargins(15, 15, 15, 15)  # 网格内边距

        # 四个泡沫相机位置配置
        camera_configs = [
            {"name": "铅快粗泡沫", "row": 0, "col": 0, "color": "#3498db"},
            {"name": "铅精一泡沫", "row": 0, "col": 1, "color": "#2ecc71"},
            {"name": "铅精二泡沫", "row": 1, "col": 0, "color": "#e74c3c"},
            {"name": "铅精三泡沫", "row": 1, "col": 1, "color": "#9b59b6"}
        ]

        for config in camera_configs:
            camera_widget = self.create_camera_widget(config)
            # 设置视频组件的拉伸策略，使其在窗口变化时均匀缩放
            grid_layout.addWidget(camera_widget, config["row"], config["col"])
            grid_layout.setRowStretch(config["row"], 1)
            grid_layout.setColumnStretch(config["col"], 1)

        main_layout.addWidget(video_container, 1)  # 视频区域占主要空间

    def create_camera_widget(self, config):
        """创建单个相机显示组件"""
        group = QGroupBox(config["name"])
    #     group.setStyleSheet(f"""
    #     QGroupBox {{
    #         border: 2px solid {config['color']};
    #         border-radius: 8px;
    #         padding: 15px 10px 10px 10px;
    #         background-color: #ffffff;
    #     }}
    #     QGroupBox::title {{
    #         subcontrol-origin: margin;
    #         subcontrol-position: top left;
    #         left: 15px;
    #         top: -8px;  /* 适当调整上移距离，避免超出边框 */
    #         padding: 0 8px;
    #         color: {config['color']};
    #         font-weight: bold;
    #         font-size: 14px;
    #         background-color: #ffffff;  /* 确保标题背景与容器一致 */
    #         border: 1px solid transparent;
    #     }}
    # """)
        group.setMinimumSize(320, 240)  # 设置最小尺寸
        group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 允许扩展

        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)  # 增加内部控件间距

        # 视频显示标签
        video_label = QLabel()
        video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        video_label.setMinimumSize(300, 200)
        video_label.setStyleSheet("""
            QLabel {
                background-color: #2c3e50;
                border: 1px solid #34495e;
                border-radius: 4px;
            }
        """)
        video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 视频区域可扩展

        # 状态标签 - 增加容器使其更美观
        status_container = QWidget()
        status_container.setStyleSheet("background-color: #f8f9fa; border-radius: 4px;")
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(5, 5, 5, 5)
        
        status_label = QLabel("模拟模式")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.setStyleSheet("color: #2c3e50; font-size: 13px; font-weight: 500;")
        
        status_layout.addWidget(status_label)

        layout.addWidget(video_label, 1)  # 视频区域占大部分空间
        layout.addWidget(status_container)

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
        for i, video_info in enumerate(self.video_labels):
            frame = self.video_service.capture_frame(i)
            self.display_frame(video_info['video_label'], frame)

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

            # 缩放图像以适应标签大小，保持比例并填充
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(
                label.width(),
                label.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation  # 平滑缩放
            )

            label.setPixmap(scaled_pixmap)

        except Exception as e:
            self.logger.error(f"显示视频帧时出错: {e}", "VIDEO")

    def update_display(self):
        """更新显示（供外部调用）"""
        self.update_video_frames()
        
    def sizeHint(self):
        """设置默认大小提示"""
        return QSize(1280, 960)