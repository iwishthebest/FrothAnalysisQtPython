"""视频预览页面 - 包含四个相机预览区域"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout,
                               QGroupBox, QLabel, QVBoxLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class VideoPreviewPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_labels = []  # 存储视频标签信息
        self._setup_ui()

    def _setup_ui(self):
        """初始化视频预览界面"""
        layout = QVBoxLayout(self)

        # 网格布局放置四个相机
        grid_layout = QGridLayout()

        # 相机位置配置
        foam_positions = [
            ("铅快粗泡沫", 0, 0),
            ("铅精一泡沫", 0, 1),
            ("铅精二泡沫", 1, 0),
            ("铅精三泡沫", 1, 1)
        ]

        for foam_name, row, col in foam_positions:
            self._add_camera_widget(grid_layout, foam_name, row, col)

        layout.addLayout(grid_layout)

    def _add_camera_widget(self, parent_layout, foam_name, row, col):
        """添加单个相机预览组件"""
        foam_group = QGroupBox(foam_name)
        foam_group.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        foam_group_layout = QVBoxLayout(foam_group)

        # 视频显示标签
        video_label = QLabel()
        video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        video_label.setProperty("videoLabel", "true")
        video_label.setStyleSheet("background-color: #2c3e50; color: white;")

        # 状态标签
        status_label = QLabel("相机连接中...")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.setStyleSheet("color: #f39c12;")

        # 布局组合
        video_container = QWidget()
        video_container_layout = QVBoxLayout(video_container)
        video_container_layout.addWidget(video_label)
        video_container_layout.addWidget(status_label)

        foam_group_layout.addWidget(video_container)
        parent_layout.addWidget(foam_group, row, col)

        # 存储标签引用
        self.video_labels.append({
            'video_label': video_label,
            'status_label': status_label,
            'foam_name': foam_name
        })

    def update_camera_status(self, foam_name, status, color="#27ae60"):
        """更新相机状态显示"""
        for item in self.video_labels:
            if item['foam_name'] == foam_name:
                item['status_label'].setText(status)
                item['status_label'].setStyleSheet(f"color: {color};")
                break