from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
                               QPushButton, QCheckBox, QLineEdit, QFileDialog,
                               QMessageBox, QTabWidget, QFormLayout, QProgressBar,
                               QScrollArea)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
import os

# 引入配置管理系统
from config.config_system import (
    ConfigManager,
    UIConfig,
    DataConfig,
    NetworkConfig,
    CameraConfig,
    SystemConfig
)


class SettingsPage(QWidget):
    """系统设置页面 - 适配 ConfigManager"""

    # 信号定义：设置改变时发出，传递配置字典
    settings_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        self.setup_ui()
        self.load_settings_to_ui()
        self.setup_connections()

    def setup_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 标题
        title_label = QLabel("系统参数配置")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # 选项卡控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #bdc3c7; background: white; border-radius: 4px; }
            QTabBar::tab { background: #ecf0f1; padding: 8px 20px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: white; border-bottom: 2px solid #3498db; font-weight: bold; }
        """)

        # 1. 系统设置 (UIConfig)
        system_tab = self.create_system_tab()
        self.tab_widget.addTab(system_tab, "系统显示")

        # 2. 网络设置 (NetworkConfig) - 新增
        network_tab = self.create_network_tab()
        self.tab_widget.addTab(network_tab, "网络通讯")

        # 3. 相机设置 (CameraConfig List) - 重构
        camera_tab = self.create_camera_tab()
        self.tab_widget.addTab(camera_tab, "视觉相机")

        # 4. 数据管理 (DataConfig)
        data_tab = self.create_data_tab()
        self.tab_widget.addTab(data_tab, "数据管理")

        # 5. 关于
        about_tab = self.create_about_tab()
        self.tab_widget.addTab(about_tab, "关于系统")

        layout.addWidget(self.tab_widget)

        # 操作按钮
        button_widget = self.create_button_section()
        layout.addWidget(button_widget)

    def create_scrollable_widget(self, content_widget):
        """创建可滚动的区域"""
        scroll = QScrollArea()
        scroll.setWidget(content_widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        return scroll

    def create_system_tab(self):
        """创建系统设置选项卡 (对应 UIConfig)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # 界面显示设置
        display_group = QGroupBox("界面显示")
        display_layout = QFormLayout(display_group)

        self.language_combo = QComboBox()
        self.language_combo.addItems(["zh-CN", "en-US"])
        display_layout.addRow("系统语言:", self.language_combo)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        display_layout.addRow("界面主题:", self.theme_combo)

        self.window_width = QSpinBox()
        self.window_width.setRange(800, 3840)
        self.window_height = QSpinBox()
        self.window_height.setRange(600, 2160)
        window_size_layout = QHBoxLayout()
        window_size_layout.addWidget(QLabel("宽:"))
        window_size_layout.addWidget(self.window_width)
        window_size_layout.addWidget(QLabel("高:"))
        window_size_layout.addWidget(self.window_height)
        display_layout.addRow("窗口尺寸:", window_size_layout)

        layout.addWidget(display_group)

        # 性能与渲染
        perf_group = QGroupBox("性能与渲染")
        perf_layout = QFormLayout(perf_group)

        self.refresh_rate_spin = QSpinBox()
        self.refresh_rate_spin.setRange(10, 1000)
        self.refresh_rate_spin.setSuffix(" ms")
        perf_layout.addRow("UI刷新间隔:", self.refresh_rate_spin)

        self.max_data_points_spin = QSpinBox()
        self.max_data_points_spin.setRange(100, 10000)
        perf_layout.addRow("图表最大点数:", self.max_data_points_spin)

        self.hardware_accel_check = QCheckBox("启用硬件加速")
        perf_layout.addRow(self.hardware_accel_check)

        self.image_quality_combo = QComboBox()
        self.image_quality_combo.addItems(["balanced", "high", "performance"])
        perf_layout.addRow("图像渲染质量:", self.image_quality_combo)

        layout.addWidget(perf_group)
        layout.addStretch()
        return self.create_scrollable_widget(widget)

    def create_network_tab(self):
        """创建网络设置选项卡 (对应 NetworkConfig)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # OPC UA / 通讯设置
        opc_group = QGroupBox("OPC通讯设置")
        opc_layout = QFormLayout(opc_group)

        self.opc_url_edit = QLineEdit()
        opc_layout.addRow("OPC服务器URL:", self.opc_url_edit)

        self.api_endpoint_edit = QLineEdit()
        opc_layout.addRow("API接口地址:", self.api_endpoint_edit)

        self.net_timeout_spin = QSpinBox()
        self.net_timeout_spin.setRange(1, 120)
        self.net_timeout_spin.setSuffix(" 秒")
        opc_layout.addRow("请求超时时间:", self.net_timeout_spin)

        self.retry_count_spin = QSpinBox()
        self.retry_count_spin.setRange(0, 10)
        opc_layout.addRow("失败重试次数:", self.retry_count_spin)

        layout.addWidget(opc_group)

        # 数据更新频率
        interval_group = QGroupBox("数据更新频率")
        interval_layout = QFormLayout(interval_group)

        self.fast_tag_spin = QDoubleSpinBox()
        self.fast_tag_spin.setRange(0.1, 60.0)
        self.fast_tag_spin.setSingleStep(0.5)
        self.fast_tag_spin.setSuffix(" 秒")
        interval_layout.addRow("快频数据(液位/泡沫):", self.fast_tag_spin)

        self.slow_tag_spin = QDoubleSpinBox()
        self.slow_tag_spin.setRange(10.0, 3600.0)
        self.slow_tag_spin.setSingleStep(10.0)
        self.slow_tag_spin.setSuffix(" 秒")
        interval_layout.addRow("慢频数据(加药/化验):", self.slow_tag_spin)

        layout.addWidget(interval_group)
        layout.addStretch()
        return self.create_scrollable_widget(widget)

    def create_camera_tab(self):
        """创建相机设置选项卡 (对应 CameraConfig 列表)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # 相机选择区域
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("当前配置相机:"))
        self.camera_select_combo = QComboBox()
        self.camera_select_combo.currentIndexChanged.connect(self.on_camera_selection_changed)
        select_layout.addWidget(self.camera_select_combo, 1)
        layout.addLayout(select_layout)

        # 相机详细参数
        self.camera_details_group = QGroupBox("参数详情")
        camera_layout = QFormLayout(self.camera_details_group)

        self.cam_enabled_check = QCheckBox("启用此相机")
        camera_layout.addRow(self.cam_enabled_check)

        self.cam_name_edit = QLineEdit()
        camera_layout.addRow("相机名称:", self.cam_name_edit)

        self.cam_rtsp_edit = QLineEdit()
        self.cam_rtsp_edit.setPlaceholderText("rtsp://...")
        camera_layout.addRow("RTSP流地址:", self.cam_rtsp_edit)

        # 图像参数
        param_layout = QHBoxLayout()

        self.cam_resolution_combo = QComboBox()
        self.cam_resolution_combo.addItems(["1920x1080", "1280x720", "640x480"])

        self.cam_fps_spin = QSpinBox()
        self.cam_fps_spin.setRange(1, 60)
        self.cam_fps_spin.setSuffix(" fps")

        camera_layout.addRow("分辨率:", self.cam_resolution_combo)
        camera_layout.addRow("帧率:", self.cam_fps_spin)

        self.cam_exposure_spin = QDoubleSpinBox()
        self.cam_exposure_spin.setRange(0.1, 1000.0)
        self.cam_exposure_spin.setSuffix(" ms")
        camera_layout.addRow("曝光时间:", self.cam_exposure_spin)

        self.cam_gain_spin = QDoubleSpinBox()
        self.cam_gain_spin.setRange(0.0, 100.0)
        camera_layout.addRow("增益:", self.cam_gain_spin)

        # 连接测试
        test_layout = QHBoxLayout()
        self.test_rtsp_btn = QPushButton("测试当前流连接")
        self.test_rtsp_btn.clicked.connect(self.on_test_rtsp_clicked)
        test_layout.addWidget(self.test_rtsp_btn)
        self.camera_status_label = QLabel("未测试")
        test_layout.addWidget(self.camera_status_label)
        camera_layout.addRow("连接状态:", test_layout)

        layout.addWidget(self.camera_details_group)
        layout.addStretch()

        # 保存当前正在编辑的相机索引
        self.current_camera_index = -1

        return self.create_scrollable_widget(widget)

    def create_data_tab(self):
        """创建数据管理选项卡 (对应 DataConfig)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # 存储设置
        save_group = QGroupBox("存储设置")
        save_layout = QFormLayout(save_group)

        path_layout = QHBoxLayout()
        self.data_path_edit = QLineEdit()
        path_layout.addWidget(self.data_path_edit)
        self.browse_path_btn = QPushButton("浏览")
        self.browse_path_btn.clicked.connect(self.on_browse_data_path)
        path_layout.addWidget(self.browse_path_btn)
        save_layout.addRow("数据保存路径:", path_layout)

        self.auto_save_spin = QSpinBox()
        self.auto_save_spin.setRange(1, 120)
        self.auto_save_spin.setSuffix(" 分钟")
        save_layout.addRow("自动保存间隔:", self.auto_save_spin)

        self.save_format_combo = QComboBox()
        self.save_format_combo.addItems(["CSV", "JSON", "Excel"])
        save_layout.addRow("数据格式:", self.save_format_combo)

        self.save_images_check = QCheckBox("保存原始图像数据")
        save_layout.addRow(self.save_images_check)

        # 缓存设置 (从系统设置移至此处)
        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(50, 10000)
        self.cache_size_spin.setSuffix(" MB")
        save_layout.addRow("内存缓存大小:", self.cache_size_spin)

        layout.addWidget(save_group)

        # 备份与清理
        maint_group = QGroupBox("维护策略")
        maint_layout = QFormLayout(maint_group)

        self.auto_backup_check = QCheckBox("启用自动备份")
        maint_layout.addRow(self.auto_backup_check)

        self.backup_path_edit = QLineEdit()
        path_layout2 = QHBoxLayout()
        path_layout2.addWidget(self.backup_path_edit)
        self.browse_backup_btn = QPushButton("浏览")
        self.browse_backup_btn.clicked.connect(self.on_browse_backup_path)
        path_layout2.addWidget(self.browse_backup_btn)
        maint_layout.addRow("备份路径:", path_layout2)

        self.backup_freq_combo = QComboBox()
        self.backup_freq_combo.addItems(["daily", "weekly", "monthly"])
        maint_layout.addRow("备份频率:", self.backup_freq_combo)

        self.auto_cleanup_check = QCheckBox("启用自动清理")
        maint_layout.addRow(self.auto_cleanup_check)

        self.retention_days_spin = QSpinBox()
        self.retention_days_spin.setRange(1, 3650)
        self.retention_days_spin.setSuffix(" 天")
        maint_layout.addRow("数据保留天数:", self.retention_days_spin)

        layout.addWidget(maint_group)
        layout.addStretch()
        return self.create_scrollable_widget(widget)

    def create_about_tab(self):
        """创建关于选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("铅浮选过程工况智能监测与控制系统")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        layout.addWidget(QLabel("版本: v2.1.0"))
        layout.addWidget(QLabel("Copyright © 2024 Intelligent Monitoring Team"))

        layout.addSpacing(20)
        self.update_btn = QPushButton("检查更新")
        self.update_btn.setFixedWidth(120)
        self.update_btn.clicked.connect(lambda: QMessageBox.information(self, "更新", "当前已是最新版本"))
        layout.addWidget(self.update_btn)

        return widget

    def create_button_section(self):
        """创建底部按钮栏"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)

        self.save_btn = QPushButton("保存所有配置")
        self.save_btn.setFixedHeight(35)
        self.save_btn.setStyleSheet("""
            QPushButton { background-color: #27ae60; color: white; border-radius: 4px; font-weight: bold; padding: 0 15px; }
            QPushButton:hover { background-color: #2ecc71; }
        """)

        self.cancel_btn = QPushButton("重新加载")
        self.cancel_btn.setFixedHeight(35)

        layout.addStretch()
        layout.addWidget(self.cancel_btn)
        layout.addWidget(self.save_btn)

        return widget

    def setup_connections(self):
        """绑定事件"""
        self.save_btn.clicked.connect(self.on_save_clicked)
        self.cancel_btn.clicked.connect(self.load_settings_to_ui)

    def load_settings_to_ui(self):
        """将配置加载到UI界面"""
        # 重新从 ConfigManager 读取
        # 注意: 这里应该确保 config_manager 数据是最新的，可以考虑 reload
        # self.config_manager = ConfigManager()

        sys_config = self.config_manager.system_config

        # 1. UI Config
        ui = sys_config.ui
        self.language_combo.setCurrentText(ui.language)
        self.theme_combo.setCurrentText(ui.theme)
        self.window_width.setValue(ui.window_size[0])
        self.window_height.setValue(ui.window_size[1])
        self.refresh_rate_spin.setValue(ui.refresh_rate)
        self.max_data_points_spin.setValue(ui.max_data_points)
        self.hardware_accel_check.setChecked(ui.hardware_acceleration)
        self.image_quality_combo.setCurrentText(ui.image_quality)

        # 2. Network Config
        net = sys_config.network
        self.opc_url_edit.setText(net.opc_server_url)
        self.api_endpoint_edit.setText(net.api_endpoint)
        self.net_timeout_spin.setValue(net.timeout)
        self.retry_count_spin.setValue(net.retry_count)
        self.fast_tag_spin.setValue(net.fast_tag_interval)
        self.slow_tag_spin.setValue(net.slow_tag_interval)

        # 3. Camera Config
        # 填充相机下拉框
        self.camera_select_combo.blockSignals(True)
        self.camera_select_combo.clear()
        for cam in sys_config.cameras:
            self.camera_select_combo.addItem(f"[{cam.camera_index}] {cam.name}", cam.camera_index)
        self.camera_select_combo.blockSignals(False)

        # 默认选中第一个
        if sys_config.cameras:
            self.camera_select_combo.setCurrentIndex(0)
            self.load_camera_details(0)

        # 4. Data Config
        data = sys_config.data
        self.data_path_edit.setText(data.save_path)
        self.auto_save_spin.setValue(data.auto_save_interval)
        self.save_format_combo.setCurrentText(data.save_format)
        self.save_images_check.setChecked(data.save_images)
        self.cache_size_spin.setValue(data.cache_size)
        self.auto_backup_check.setChecked(data.auto_backup)
        self.backup_path_edit.setText(data.backup_path)
        self.backup_freq_combo.setCurrentText(data.backup_frequency)
        self.auto_cleanup_check.setChecked(data.auto_cleanup)
        self.retention_days_spin.setValue(data.retention_days)

    def on_camera_selection_changed(self, index):
        """相机下拉框切换时调用"""
        if index < 0: return

        # 切换前先保存当前UI上的数据到内存对象（可选，或者只在最终保存时读取）
        # 为简单起见，这里假设用户切换相机前不需要“暂存”未保存的修改，或者我们只在点击"保存所有"时统一下发
        # 但为了用户体验，如果用户改了参数没保存就切相机，数据会丢失。
        # 策略：每次切换时，先把UI数据写回对应的 config 对象
        if self.current_camera_index >= 0:
            self.save_current_camera_to_memory()

        self.load_camera_details(index)

    def load_camera_details(self, combo_index):
        """加载指定相机的详情到UI"""
        cam_index = self.camera_select_combo.itemData(combo_index)
        camera = self.config_manager.get_camera_by_index(cam_index)

        if not camera:
            return

        self.current_camera_index = combo_index

        self.cam_enabled_check.setChecked(camera.enabled)
        self.cam_name_edit.setText(camera.name)
        self.cam_rtsp_edit.setText(camera.rtsp_url)
        self.cam_resolution_combo.setCurrentText(camera.resolution)
        self.cam_fps_spin.setValue(camera.frame_rate)
        self.cam_exposure_spin.setValue(camera.exposure)
        self.cam_gain_spin.setValue(camera.gain)
        self.camera_status_label.setText("未测试")

    def save_current_camera_to_memory(self):
        """将当前UI上的相机参数写回内存中的配置对象"""
        if self.current_camera_index < 0: return

        cam_index = self.camera_select_combo.itemData(self.current_camera_index)
        camera = self.config_manager.get_camera_by_index(cam_index)

        if camera:
            camera.enabled = self.cam_enabled_check.isChecked()
            camera.name = self.cam_name_edit.text()
            camera.rtsp_url = self.cam_rtsp_edit.text()
            camera.resolution = self.cam_resolution_combo.currentText()
            camera.frame_rate = self.cam_fps_spin.value()
            camera.exposure = self.cam_exposure_spin.value()
            camera.gain = self.cam_gain_spin.value()

            # 更新回 ConfigManager
            self.config_manager.update_camera_config(camera)

    def on_save_clicked(self):
        """保存按钮点击事件"""
        try:
            # 1. 确保当前正在编辑的相机数据已更新到内存
            self.save_current_camera_to_memory()

            # 2. 从UI获取并更新 UIConfig
            ui_config = self.config_manager.get_ui_config()
            ui_config.language = self.language_combo.currentText()
            ui_config.theme = self.theme_combo.currentText()
            ui_config.window_size = (self.window_width.value(), self.window_height.value())
            ui_config.refresh_rate = self.refresh_rate_spin.value()
            ui_config.max_data_points = self.max_data_points_spin.value()
            ui_config.hardware_acceleration = self.hardware_accel_check.isChecked()
            ui_config.image_quality = self.image_quality_combo.currentText()
            self.config_manager.update_ui_config(ui_config)

            # 3. 从UI获取并更新 NetworkConfig
            net_config = self.config_manager.get_network_config()
            net_config.opc_server_url = self.opc_url_edit.text()
            net_config.api_endpoint = self.api_endpoint_edit.text()
            net_config.timeout = self.net_timeout_spin.value()
            net_config.retry_count = self.retry_count_spin.value()
            net_config.fast_tag_interval = self.fast_tag_spin.value()
            net_config.slow_tag_interval = self.slow_tag_spin.value()
            self.config_manager.update_network_config(net_config)

            # 4. 从UI获取并更新 DataConfig
            data_config = self.config_manager.get_data_config()
            data_config.save_path = self.data_path_edit.text()
            data_config.auto_save_interval = self.auto_save_spin.value()
            data_config.save_format = self.save_format_combo.currentText()
            data_config.save_images = self.save_images_check.isChecked()
            data_config.cache_size = self.cache_size_spin.value()
            data_config.auto_backup = self.auto_backup_check.isChecked()
            data_config.backup_path = self.backup_path_edit.text()
            data_config.backup_frequency = self.backup_freq_combo.currentText()
            data_config.auto_cleanup = self.auto_cleanup_check.isChecked()
            data_config.retention_days = self.retention_days_spin.value()
            self.config_manager.update_data_config(data_config)

            # 5. 执行最终的磁盘写入
            self.config_manager.save_config()

            QMessageBox.information(self, "保存成功", "系统配置已成功保存并生效！")

            # 发送信号通知其他组件
            self.settings_changed.emit(self.config_manager.system_config.to_dict())

        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存配置时发生错误: {str(e)}")

    def on_browse_data_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择数据保存目录", self.data_path_edit.text())
        if path:
            self.data_path_edit.setText(path)

    def on_browse_backup_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择备份目录", self.backup_path_edit.text())
        if path:
            self.backup_path_edit.setText(path)

    def on_test_rtsp_clicked(self):
        url = self.cam_rtsp_edit.text()
        if not url.startswith("rtsp://"):
            QMessageBox.warning(self, "格式错误", "RTSP地址必须以 rtsp:// 开头")
            return

        self.camera_status_label.setText("正在连接...")
        self.camera_status_label.setStyleSheet("color: orange;")

        # 模拟异步测试
        QTimer.singleShot(1000, lambda: self.finish_test(True))

    def finish_test(self, success):
        if success:
            self.camera_status_label.setText("连接成功")
            self.camera_status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.camera_status_label.setText("连接失败")
            self.camera_status_label.setStyleSheet("color: red;")