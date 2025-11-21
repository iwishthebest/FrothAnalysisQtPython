from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QGridLayout, QGroupBox, QLabel, QSpacerItem, 
                               QSizePolicy, QPushButton)
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
            camera_widget = self.create_camera_widget(layout)
            # 设置视频组件的拉伸策略，使其在窗口变化时均匀缩放
            grid_layout.addWidget(camera_widget, layout.row, layout.col)
            grid_layout.setRowStretch(layout.row, 1)
            grid_layout.setColumnStretch(layout.col, 1)

        main_layout.addWidget(video_container, 1)  # 视频区域占主要空间

    def create_camera_widget(self, config):
        """创建单个相机显示组件"""
        group = QGroupBox(config.display_name)
        group.setMinimumSize(320, 240)  # 保持原有尺寸
        group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

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
        video_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # 状态标签和按钮容器 - 修改为水平布局
        status_container = QWidget()
        status_container.setStyleSheet("background-color: #f8f9fa; border-radius: 4px;")
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(10, 5, 10, 5)  # 增加左右边距
        
        # 状态标签
        status_label = QLabel("模拟模式")
        status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        status_label.setStyleSheet("color: #2c3e50; font-size: 13px; font-weight: 500;")
        status_label.setMinimumWidth(120)  # 设置最小宽度确保文字显示完整
        
        # 连接按钮
        connect_button = QPushButton("连接")
        connect_button.setFixedSize(60, 25)  # 固定按钮大小
        connect_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)

        # 断开按钮
        disconnect_button = QPushButton("断开")
        disconnect_button.setFixedSize(60, 25)  # 固定按钮大小
        disconnect_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)

        # 添加控件到状态布局
        status_layout.addWidget(status_label)
        status_layout.addStretch(1)  # 添加弹簧使按钮靠右
        status_layout.addWidget(connect_button)
        status_layout.addWidget(disconnect_button)

        layout.addWidget(video_label, 1)
        layout.addWidget(status_container)

        # 存储引用
        camera_info = {
            'video_label': video_label,
            'status_label': status_label,
            'connect_button': connect_button,
            'disconnect_button': disconnect_button,
            'config': config,
            'camera_index': len(self.video_labels)  # 存储相机索引
        }
        self.video_labels.append(camera_info)

        # 连接按钮信号
        connect_button.clicked.connect(lambda checked, idx=len(self.video_labels)-1: self.connect_camera(idx))
        disconnect_button.clicked.connect(lambda checked, idx=len(self.video_labels)-1: self.disconnect_camera(idx))

        # 初始按钮状态
        self.update_button_states(camera_info)

        return group

    def connect_camera(self, camera_index):
        """连接指定相机"""
        try:
            success = self.video_service.reconnect_camera(camera_index)
            if success:
                self.logger.info(f"相机 {camera_index} 连接成功")
                # 更新按钮状态
                self.update_button_states(self.video_labels[camera_index])
            else:
                self.logger.error(f"相机 {camera_index} 连接失败")
        except Exception as e:
            self.logger.error(f"连接相机 {camera_index} 时出错: {e}")

    def disconnect_camera(self, camera_index):
        """断开指定相机"""
        try:
            success = self.video_service.disconnect_camera(camera_index)
            if success:
                self.logger.info(f"相机 {camera_index} 已断开")
                # 更新按钮状态
                self.update_button_states(self.video_labels[camera_index])
            else:
                self.logger.error(f"断开相机 {camera_index} 失败")
        except Exception as e:
            self.logger.error(f"断开相机 {camera_index} 时出错: {e}")

    def update_button_states(self, camera_info):
        """根据相机状态更新按钮状态"""
        camera_status = self.video_service.get_camera_status(camera_info['camera_index'])
        
        is_connected = camera_status["status"] == "connected"
        is_disconnected = camera_status["status"] == "disconnected"
        is_simulation = camera_status["status"] == "simulation"
        
        # 设置按钮启用状态
        camera_info['connect_button'].setEnabled(is_disconnected or is_simulation)
        camera_info['disconnect_button'].setEnabled(is_connected)
        
        # 设置按钮提示文本
        if is_simulation:
            camera_info['connect_button'].setToolTip("切换到真实相机模式")
            camera_info['disconnect_button'].setToolTip("模拟模式下无法断开")
        else:
            camera_info['connect_button'].setToolTip("连接相机")
            camera_info['disconnect_button'].setToolTip("断开相机连接")

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
            video_info['status_label'].setText(status_message)
            
            # 更新按钮状态
            self.update_button_states(video_info)
            
            if hasattr(self, 'set_status'):
                self.set_status(status_message, is_error)

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
                Qt.TransformationMode.SmoothTransformation
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