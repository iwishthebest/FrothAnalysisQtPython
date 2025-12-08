from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QGridLayout, QGroupBox, QLabel, QSpacerItem, QSizePolicy, QPushButton)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPixmap, QImage, QFont
import cv2

from config.config_system import config_manager
from src.services.logging_service import get_logging_service
from src.services.video_service import get_video_service


class VideoDisplayWidget(QWidget):
    """视频显示组件 - 显示四个泡沫相机视频流"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logging_service()
        self.camera_configs = config_manager.get_camera_configs()
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
        title_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        title_layout.addWidget(title_label)
        title_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

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

        for camera_config in self.camera_configs:
            layout = camera_config.layout
            camera_widget = self.create_camera_widget(camera_config)
            # 设置视频组件的拉伸策略，使其在窗口变化时均匀缩放
            grid_layout.addWidget(camera_widget, layout.row, layout.col)
            grid_layout.setRowStretch(layout.row, 1)
            grid_layout.setColumnStretch(layout.col, 1)

        main_layout.addWidget(video_container, 1)  # 视频区域占主要空间

    def create_camera_widget(self, config):
        """创建单个相机显示组件"""
        group = QGroupBox(config.layout.display_name)

        group.setMinimumSize(320, 240)  # 设置最小尺寸
        group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)  # 允许扩展

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
        video_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)  # 视频区域可扩展

        # 状态和控制按钮容器
        status_control_container = QWidget()
        status_control_container.setStyleSheet("background-color: #f8f9fa; border-radius: 4px;")
        status_control_layout = QHBoxLayout(status_control_container)
        status_control_layout.setContentsMargins(5, 5, 5, 5)
        status_control_layout.setSpacing(10)

        # 状态标签
        status_label = QLabel("模拟模式")
        status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        status_label.setStyleSheet("color: #2c3e50; font-size: 13px; font-weight: 500;")
        status_label.setMinimumWidth(120)

        # 连接按钮
        connect_btn = QPushButton("连接")
        connect_btn.setFixedSize(60, 25)
        connect_btn.clicked.connect(lambda checked, idx=config.camera_index: self.connect_camera(idx))
        # 添加自定义样式以改进按钮外观
        connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; /* 按钮背景色 */
                border: none; /* 移除边框 */
                color: white; /* 文字颜色 */
                padding: 5px 10px; /* 内边距 */
                text-align: center; /* 文字居中 */
                text-decoration: none;
                display: inline-block;
                font-size: 12px; /* 字体大小 */
                margin: 1px 2px;
                cursor: pointer;
                border-radius: 4px; /* 圆角 */
            }

            QPushButton:hover {
                background-color: #45a049; /* 鼠标悬停时的背景色 */
            }
        """)
        # 断开按钮
        disconnect_btn = QPushButton("断开")
        disconnect_btn.setFixedSize(60, 25)
        disconnect_btn.clicked.connect(lambda checked, idx=config.camera_index: self.disconnect_camera(idx))

        # 添加弹簧使按钮靠右显示
        status_control_layout.addWidget(status_label)
        status_control_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        status_control_layout.addWidget(connect_btn)
        status_control_layout.addWidget(disconnect_btn)

        layout.addWidget(video_label, 1)  # 视频区域占大部分空间
        layout.addWidget(status_control_container)

        # 存储引用
        self.video_labels.append({
            'video_label': video_label,
            'status_label': status_label,
            'config': config,
            'connect_btn': connect_btn,
            'disconnect_btn': disconnect_btn
        })

        return group

    def connect_camera(self, camera_index):
        """连接指定相机"""
        self.logger.info(f"尝试连接相机 {camera_index}", "VIDEO")
        # 更新相机配置为启用状态
        if 0 <= camera_index < len(self.camera_configs):
            self.camera_configs[camera_index].enabled = True
            config_manager.save_config()  # 保存配置更改

        # 如果处于模拟模式，先切换到真实模式
        if self.video_service.simulation_mode:
            self.video_service.set_simulation_mode(False)
        # 重新连接相机
        success = self.video_service.reconnect_camera(camera_index)
        if success:
            self.logger.info(f"相机 {camera_index} 连接成功", "VIDEO")
        else:
            self.logger.error(f"相机 {camera_index} 连接失败", "VIDEO")
        # 立即更新显示
        self.update_video_frames()

    def disconnect_camera(self, camera_index):
        """断开指定相机连接"""
        self.logger.info(f"尝试断开相机 {camera_index}", "VIDEO")
        # 更新相机配置为禁用状态
        if 0 <= camera_index < len(self.camera_configs):
            self.camera_configs[camera_index].enabled = False
            config_manager.save_config()  # 保存配置更改

        # 断开相机连接
        self.video_service.disconnect_camera(camera_index)
        # 立即更新显示
        self.update_video_frames()

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

            # 获取相机状态
            camera_status = self.video_service.get_camera_status(i)
            status_message = f"{camera_status['name']} - {camera_status['message']}"

            # 更新状态标签文字
            is_error = camera_status["status"] not in ["connected", "simulation"]
            video_info['status_label'].setText(status_message)  # 更新状态文字

            # 更新按钮状态
            if camera_status["status"] == "connected":
                video_info['connect_btn'].setEnabled(False)
                video_info['disconnect_btn'].setEnabled(True)
            else:
                video_info['connect_btn'].setEnabled(True)
                video_info['disconnect_btn'].setEnabled(False)

            if hasattr(self, 'set_status'):
                self.set_status(status_message, is_error)  # 如果有set_status方法，则调用它

    def display_frame(self, label, frame):
        """在QLabel中显示视频帧"""
        try:
            if frame is None:
                return

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