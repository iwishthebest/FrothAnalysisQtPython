from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
                               QPushButton, QCheckBox, QLineEdit, QFileDialog,
                               QMessageBox, QTabWidget, QFormLayout, QProgressBar)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QIntValidator
import json
import os
from datetime import datetime


class SettingsPage(QWidget):
    """系统设置页面 - 包含系统配置、相机设置、数据管理等"""

    # 信号定义
    settings_changed = Signal(dict)  # 设置改变时发出新配置

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_file = "config/system_settings.json"
        self.current_settings = self.load_default_settings()
        self.setup_ui()
        self.load_settings()
        self.setup_connections()

    def setup_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)

        # 标题
        title_label = QLabel("系统设置与管理")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin: 10px;")
        layout.addWidget(title_label)

        # 选项卡控件
        self.tab_widget = QTabWidget()

        # 系统设置选项卡
        system_tab = self.create_system_tab()
        self.tab_widget.addTab(system_tab, "系统设置")

        # 相机设置选项卡
        camera_tab = self.create_camera_tab()
        self.tab_widget.addTab(camera_tab, "相机设置")

        # 数据管理选项卡
        data_tab = self.create_data_tab()
        self.tab_widget.addTab(data_tab, "数据管理")

        # 关于选项卡
        about_tab = self.create_about_tab()
        self.tab_widget.addTab(about_tab, "关于")

        layout.addWidget(self.tab_widget)

        # 操作按钮
        button_widget = self.create_button_section()
        layout.addWidget(button_widget)

    def create_system_tab(self):
        """创建系统设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        # 基本设置组
        basic_group = QGroupBox("基本设置")
        basic_layout = QFormLayout(basic_group)

        # 系统语言
        self.language_combo = QComboBox()
        self.language_combo.addItems(["简体中文", "English", "日本語"])
        basic_layout.addRow("系统语言:", self.language_combo)

        # 主题设置
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["默认主题", "深色主题", "蓝色科技", "绿色环保"])
        basic_layout.addRow("界面主题:", self.theme_combo)

        # 数据刷新频率
        self.refresh_rate_spin = QSpinBox()
        self.refresh_rate_spin.setRange(1, 60)
        self.refresh_rate_spin.setSuffix(" 秒")
        basic_layout.addRow("数据刷新频率:", self.refresh_rate_spin)

        layout.addWidget(basic_group)

        # 性能设置组
        performance_group = QGroupBox("性能设置")
        performance_layout = QFormLayout(performance_group)

        # 硬件加速
        self.hardware_accel_check = QCheckBox("启用硬件加速")
        performance_layout.addRow(self.hardware_accel_check)

        # 图像质量
        self.image_quality_combo = QComboBox()
        self.image_quality_combo.addItems(["高性能", "平衡", "高质量"])
        performance_layout.addRow("图像处理质量:", self.image_quality_combo)

        # 缓存大小
        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(100, 5000)
        self.cache_size_spin.setSuffix(" MB")
        performance_layout.addRow("缓存大小:", self.cache_size_spin)

        layout.addWidget(performance_group)

        layout.addStretch()
        return widget

    def create_camera_tab(self):
        """创建相机设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        # 相机参数组
        camera_group = QGroupBox("相机参数设置")
        camera_layout = QFormLayout(camera_group)

        # 分辨率设置
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["640x480", "1280x720", "1920x1080", "3840x2160"])
        camera_layout.addRow("相机分辨率:", self.resolution_combo)

        # 帧率设置
        self.frame_rate_spin = QSpinBox()
        self.frame_rate_spin.setRange(1, 60)
        self.frame_rate_spin.setSuffix(" fps")
        camera_layout.addRow("采集帧率:", self.frame_rate_spin)

        # 曝光设置
        self.exposure_spin = QDoubleSpinBox()
        self.exposure_spin.setRange(0.1, 100.0)
        self.exposure_spin.setSuffix(" ms")
        camera_layout.addRow("曝光时间:", self.exposure_spin)

        # 增益设置
        self.gain_spin = QDoubleSpinBox()
        self.gain_spin.setRange(0, 30.0)
        self.gain_spin.setSuffix(" dB")
        camera_layout.addRow("增益:", self.gain_spin)

        layout.addWidget(camera_group)

        # 相机连接组
        connection_group = QGroupBox("相机连接设置")
        connection_layout = QFormLayout(connection_group)

        # RTSP地址设置
        rtsp_layout = QHBoxLayout()
        self.rtsp_edit = QLineEdit()
        self.rtsp_edit.setPlaceholderText("rtsp://username:password@ip:port/stream")
        rtsp_layout.addWidget(self.rtsp_edit)
        self.test_rtsp_btn = QPushButton("测试连接")
        self.test_rtsp_btn.setFixedSize(80, 30)
        rtsp_layout.addWidget(self.test_rtsp_btn)
        connection_layout.addRow("RTSP地址:", rtsp_layout)

        # 连接超时
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 30)
        self.timeout_spin.setSuffix(" 秒")
        connection_layout.addRow("连接超时:", self.timeout_spin)

        # 重连间隔
        self.reconnect_spin = QSpinBox()
        self.reconnect_spin.setRange(1, 60)
        self.reconnect_spin.setSuffix(" 秒")
        connection_layout.addRow("重连间隔:", self.reconnect_spin)

        layout.addWidget(connection_group)

        # 相机状态显示
        status_group = QGroupBox("相机状态")
        status_layout = QVBoxLayout(status_group)

        self.camera_status_label = QLabel("相机状态: 未连接")
        status_layout.addWidget(self.camera_status_label)

        # 连接进度
        self.connection_progress = QProgressBar()
        self.connection_progress.setVisible(False)
        status_layout.addWidget(self.connection_progress)

        layout.addWidget(status_group)

        layout.addStretch()
        return widget

    def create_data_tab(self):
        """创建数据管理选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        # 数据保存设置组
        save_group = QGroupBox("数据保存设置")
        save_layout = QFormLayout(save_group)

        # 数据保存路径
        path_layout = QHBoxLayout()
        self.data_path_edit = QLineEdit()
        self.data_path_edit.setPlaceholderText("选择数据保存目录")
        path_layout.addWidget(self.data_path_edit)
        self.browse_path_btn = QPushButton("浏览")
        self.browse_path_btn.setFixedSize(60, 30)
        path_layout.addWidget(self.browse_path_btn)
        save_layout.addRow("数据保存路径:", path_layout)

        # 自动保存间隔
        self.auto_save_spin = QSpinBox()
        self.auto_save_spin.setRange(1, 60)
        self.auto_save_spin.setSuffix(" 分钟")
        save_layout.addRow("自动保存间隔:", self.auto_save_spin)

        # 数据保存格式
        self.save_format_combo = QComboBox()
        self.save_format_combo.addItems(["CSV格式", "JSON格式", "Excel格式", "数据库"])
        save_layout.addRow("数据格式:", self.save_format_combo)

        # 保存图像数据
        self.save_images_check = QCheckBox("保存图像数据")
        save_layout.addRow(self.save_images_check)

        layout.addWidget(save_group)

        # 数据备份组
        backup_group = QGroupBox("数据备份设置")
        backup_layout = QFormLayout(backup_group)

        # 自动备份
        self.auto_backup_check = QCheckBox("启用自动备份")
        backup_layout.addRow(self.auto_backup_check)

        # 备份路径
        backup_path_layout = QHBoxLayout()
        self.backup_path_edit = QLineEdit()
        self.backup_path_edit.setPlaceholderText("选择备份目录")
        backup_path_layout.addWidget(self.backup_path_edit)
        self.browse_backup_btn = QPushButton("浏览")
        self.browse_backup_btn.setFixedSize(60, 30)
        backup_path_layout.addWidget(self.browse_backup_btn)
        backup_layout.addRow("备份路径:", backup_path_layout)

        # 备份频率
        self.backup_frequency_combo = QComboBox()
        self.backup_frequency_combo.addItems(["每天", "每周", "每月"])
        backup_layout.addRow("备份频率:", self.backup_frequency_combo)

        layout.addWidget(backup_group)

        # 数据清理组
        cleanup_group = QGroupBox("数据清理设置")
        cleanup_layout = QFormLayout(cleanup_group)

        # 自动清理
        self.auto_cleanup_check = QCheckBox("启用自动清理")
        cleanup_layout.addRow(self.auto_cleanup_check)

        # 保留天数
        self.retention_days_spin = QSpinBox()
        self.retention_days_spin.setRange(1, 365)
        self.retention_days_spin.setSuffix(" 天")
        cleanup_layout.addRow("数据保留时间:", self.retention_days_spin)

        # 立即清理按钮
        self.cleanup_now_btn = QPushButton("立即清理旧数据")
        self.cleanup_now_btn.setFixedSize(120, 30)
        cleanup_layout.addRow("", self.cleanup_now_btn)

        layout.addWidget(cleanup_group)

        layout.addStretch()
        return widget

    def create_about_tab(self):
        """创建关于选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 应用信息
        info_group = QGroupBox("应用信息")
        info_layout = QFormLayout(info_group)

        app_name_label = QLabel("铅浮选过程工况智能监测与控制系统")
        app_name_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        info_layout.addRow("应用名称:", app_name_label)

        version_label = QLabel("v2.1.0")
        info_layout.addRow("版本号:", version_label)

        build_date_label = QLabel("2024-01-15")
        info_layout.addRow("构建日期:", build_date_label)

        developer_label = QLabel("智能监测技术团队")
        info_layout.addRow("开发团队:", developer_label)

        layout.addWidget(info_group)

        # 系统信息
        system_group = QGroupBox("系统信息")
        system_layout = QFormLayout(system_group)

        python_version_label = QLabel("Python 3.9.7")
        system_layout.addRow("Python版本:", python_version_label)

        qt_version_label = QLabel("PySide6 6.5.0")
        system_layout.addRow("Qt版本:", qt_version_label)

        os_label = QLabel("Windows 10/11")
        system_layout.addRow("支持平台:", os_label)

        layout.addWidget(system_group)

        # 技术支持
        support_group = QGroupBox("技术支持")
        support_layout = QVBoxLayout(support_group)

        support_label = QLabel(
            "如有问题请联系技术支持团队：\n"
            "邮箱: support@intelligent-monitoring.com\n"
            "电话: 400-123-4567\n"
            "工作时间: 周一至周五 9:00-18:00"
        )
        support_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        support_layout.addWidget(support_label)

        layout.addWidget(support_group)

        # 检查更新按钮
        self.update_btn = QPushButton("检查更新")
        self.update_btn.setFixedSize(100, 35)
        layout.addWidget(self.update_btn)

        layout.addStretch()
        return widget

    def create_button_section(self):
        """创建操作按钮区域"""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # 保存设置按钮
        self.save_btn = QPushButton("保存设置")
        self.save_btn.setFixedSize(100, 35)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)

        # 恢复默认按钮
        self.default_btn = QPushButton("恢复默认")
        self.default_btn.setFixedSize(100, 35)

        # 应用设置按钮
        self.apply_btn = QPushButton("应用设置")
        self.apply_btn.setFixedSize(100, 35)

        # 取消按钮
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedSize(100, 35)

        layout.addStretch()
        layout.addWidget(self.save_btn)
        layout.addWidget(self.apply_btn)
        layout.addWidget(self.default_btn)
        layout.addWidget(self.cancel_btn)

        return widget

    def setup_connections(self):
        """设置信号连接"""
        # 按钮连接
        self.save_btn.clicked.connect(self.on_save_clicked)
        self.apply_btn.clicked.connect(self.on_apply_clicked)
        self.default_btn.clicked.connect(self.on_default_clicked)
        self.cancel_btn.clicked.connect(self.on_cancel_clicked)

        # 路径浏览按钮
        self.browse_path_btn.clicked.connect(self.on_browse_data_path)
        self.browse_backup_btn.clicked.connect(self.on_browse_backup_path)

        # 测试连接按钮
        self.test_rtsp_btn.clicked.connect(self.on_test_rtsp_clicked)

        # 清理按钮
        self.cleanup_now_btn.clicked.connect(self.on_cleanup_clicked)

        # 更新按钮
        self.update_btn.clicked.connect(self.on_update_clicked)

    def load_default_settings(self):
        """加载默认设置"""
        return {
            "system": {
                "language": "简体中文",
                "theme": "默认主题",
                "refresh_rate": 5,
                "hardware_acceleration": True,
                "image_quality": "平衡",
                "cache_size": 500
            },
            "camera": {
                "resolution": "1920x1080",
                "frame_rate": 30,
                "exposure": 10.0,
                "gain": 5.0,
                "rtsp_url": "rtsp://admin:password@192.168.1.101:554/stream",
                "timeout": 10,
                "reconnect_interval": 5
            },
            "data": {
                "save_path": "./data",
                "auto_save_interval": 10,
                "save_format": "CSV格式",
                "save_images": True,
                "auto_backup": True,
                "backup_path": "./backup",
                "backup_frequency": "每周",
                "auto_cleanup": True,
                "retention_days": 30
            }
        }

    def load_settings(self):
        """从文件加载设置"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    # 合并设置，确保所有键都存在
                    self.merge_settings(loaded_settings)
            else:
                self.save_settings()  # 创建默认设置文件

            self.apply_settings_to_ui()

        except Exception as e:
            QMessageBox.warning(self, "加载设置错误", f"无法加载设置文件: {str(e)}")

    def merge_settings(self, new_settings):
        """合并设置，确保所有键都存在"""
        for category, settings in new_settings.items():
            if category in self.current_settings:
                for key, value in settings.items():
                    if key in self.current_settings[category]:
                        self.current_settings[category][key] = value

    def apply_settings_to_ui(self):
        """将当前设置应用到UI"""
        # 系统设置
        system = self.current_settings["system"]
        self.language_combo.setCurrentText(system["language"])
        self.theme_combo.setCurrentText(system["theme"])
        self.refresh_rate_spin.setValue(system["refresh_rate"])
        self.hardware_accel_check.setChecked(system["hardware_acceleration"])
        self.image_quality_combo.setCurrentText(system["image_quality"])
        self.cache_size_spin.setValue(system["cache_size"])

        # 相机设置
        camera = self.current_settings["camera"]
        self.resolution_combo.setCurrentText(camera["resolution"])
        self.frame_rate_spin.setValue(camera["frame_rate"])
        self.exposure_spin.setValue(camera["exposure"])
        self.gain_spin.setValue(camera["gain"])
        self.rtsp_edit.setText(camera["rtsp_url"])
        self.timeout_spin.setValue(camera["timeout"])
        self.reconnect_spin.setValue(camera["reconnect_interval"])

        # 数据设置
        data = self.current_settings["data"]
        self.data_path_edit.setText(data["save_path"])
        self.auto_save_spin.setValue(data["auto_save_interval"])
        self.save_format_combo.setCurrentText(data["save_format"])
        self.save_images_check.setChecked(data["save_images"])
        self.auto_backup_check.setChecked(data["auto_backup"])
        self.backup_path_edit.setText(data["backup_path"])
        self.backup_frequency_combo.setCurrentText(data["backup_frequency"])
        self.auto_cleanup_check.setChecked(data["auto_cleanup"])
        self.retention_days_spin.setValue(data["retention_days"])

    def get_settings_from_ui(self):
        """从UI获取当前设置"""
        settings = self.current_settings.copy()

        # 系统设置
        settings["system"]["language"] = self.language_combo.currentText()
        settings["system"]["theme"] = self.theme_combo.currentText()
        settings["system"]["refresh_rate"] = self.refresh_rate_spin.value()
        settings["system"]["hardware_acceleration"] = self.hardware_accel_check.isChecked()
        settings["system"]["image_quality"] = self.image_quality_combo.currentText()
        settings["system"]["cache_size"] = self.cache_size_spin.value()

        # 相机设置
        settings["camera"]["resolution"] = self.resolution_combo.currentText()
        settings["camera"]["frame_rate"] = self.frame_rate_spin.value()
        settings["camera"]["exposure"] = self.exposure_spin.value()
        settings["camera"]["gain"] = self.gain_spin.value()
        settings["camera"]["rtsp_url"] = self.rtsp_edit.text()
        settings["camera"]["timeout"] = self.timeout_spin.value()
        settings["camera"]["reconnect_interval"] = self.reconnect_spin.value()

        # 数据设置
        settings["data"]["save_path"] = self.data_path_edit.text()
        settings["data"]["auto_save_interval"] = self.auto_save_spin.value()
        settings["data"]["save_format"] = self.save_format_combo.currentText()
        settings["data"]["save_images"] = self.save_images_check.isChecked()
        settings["data"]["auto_backup"] = self.auto_backup_check.isChecked()
        settings["data"]["backup_path"] = self.backup_path_edit.text()
        settings["data"]["backup_frequency"] = self.backup_frequency_combo.currentText()
        settings["data"]["auto_cleanup"] = self.auto_cleanup_check.isChecked()
        settings["data"]["retention_days"] = self.retention_days_spin.value()

        return settings

    def save_settings(self):
        """保存设置到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)

            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_settings, f, indent=4, ensure_ascii=False)

            return True
        except Exception as e:
            QMessageBox.critical(self, "保存设置错误", f"无法保存设置: {str(e)}")
            return False

    def on_save_clicked(self):
        """保存按钮点击事件"""
        self.current_settings = self.get_settings_from_ui()
        if self.save_settings():
            QMessageBox.information(self, "保存成功", "设置已保存成功！")
            self.settings_changed.emit(self.current_settings)

    def on_apply_clicked(self):
        """应用按钮点击事件"""
        self.current_settings = self.get_settings_from_ui()
        self.settings_changed.emit(self.current_settings)
        QMessageBox.information(self, "应用成功", "设置已应用！")

    def on_default_clicked(self):
        """恢复默认按钮点击事件"""
        reply = QMessageBox.question(self, "确认恢复",
                                     "确定要恢复默认设置吗？当前设置将丢失。",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.current_settings = self.load_default_settings()
            self.apply_settings_to_ui()
            QMessageBox.information(self, "恢复成功", "已恢复默认设置！")

    def on_cancel_clicked(self):
        """取消按钮点击事件"""
        self.apply_settings_to_ui()  # 重新加载当前设置
        QMessageBox.information(self, "取消操作", "已取消未保存的更改。")

    def on_browse_data_path(self):
        """浏览数据保存路径"""
        path = QFileDialog.getExistingDirectory(self, "选择数据保存目录",
                                                self.data_path_edit.text())
        if path:
            self.data_path_edit.setText(path)

    def on_browse_backup_path(self):
        """浏览备份路径"""
        path = QFileDialog.getExistingDirectory(self, "选择备份目录",
                                                self.backup_path_edit.text())
        if path:
            self.backup_path_edit.setText(path)

    def on_test_rtsp_clicked(self):
        """测试RTSP连接"""
        rtsp_url = self.rtsp_edit.text()
        if not rtsp_url:
            QMessageBox.warning(self, "测试连接", "请输入RTSP地址")
            return

        self.connection_progress.setVisible(True)
        self.camera_status_label.setText("正在测试连接...")

        # 模拟连接测试
        QTimer.singleShot(2000, self.simulate_connection_test)

    def simulate_connection_test(self):
        """模拟连接测试"""
        rtsp_url = self.rtsp_edit.text()

        # 简单的URL格式检查
        if rtsp_url.startswith("rtsp://") and "@" in rtsp_url:
            self.camera_status_label.setText("相机状态: 连接成功")
            self.connection_progress.setValue(100)
            QMessageBox.information(self, "连接测试", "RTSP连接测试成功！")
        else:
            self.camera_status_label.setText("相机状态: 连接失败")
            self.connection_progress.setValue(0)
            QMessageBox.warning(self, "连接测试", "RTSP连接测试失败，请检查地址格式")

        self.connection_progress.setVisible(False)

    def on_cleanup_clicked(self):
        """立即清理旧数据"""
        reply = QMessageBox.question(self, "确认清理",
                                     "确定要立即清理旧数据吗？此操作不可恢复。",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            # 模拟清理过程
            self.cleanup_now_btn.setEnabled(False)
            self.cleanup_now_btn.setText("清理中...")

            QTimer.singleShot(3000, self.simulate_cleanup_complete)

    def simulate_cleanup_complete(self):
        """模拟清理完成"""
        self.cleanup_now_btn.setEnabled(True)
        self.cleanup_now_btn.setText("立即清理旧数据")
        QMessageBox.information(self, "清理完成", "旧数据清理完成！")

    def on_update_clicked(self):
        """检查更新"""
        # 模拟检查更新
        QMessageBox.information(self, "检查更新",
                                "当前已是最新版本！\n版本: v2.1.0\n发布日期: 2024-01-15")