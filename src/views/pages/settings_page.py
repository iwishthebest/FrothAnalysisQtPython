from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
                               QPushButton, QCheckBox, QLineEdit, QFileDialog,
                               QMessageBox, QTabWidget, QFormLayout, QProgressBar,
                               QScrollArea, QFrame, QSizePolicy)
from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QFont, QIcon, QColor, QPalette

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
    """系统设置页面 - 美化版"""

    # 信号定义：设置改变时发出，传递配置字典
    settings_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        self.setup_style()
        self.setup_ui()
        self.load_settings_to_ui()
        self.setup_connections()

    def setup_style(self):
        """配置页面整体样式表"""
        # 定义现代化的配色和控件样式
        self.setStyleSheet("""
            QWidget {
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
                font-size: 14px;
                color: #2c3e50;
            }

            /* 背景色 */
            QWidget#SettingsPage {
                background-color: #f5f7fa; 
            }

            /* 滚动区域背景透明 */
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QWidget#ScrollContents {
                background-color: transparent;
            }

            /* Tab 样式 */
            QTabWidget::pane {
                border: 1px solid #e1e4e8;
                background: white;
                border-radius: 8px;
                top: -1px; 
            }
            QTabBar::tab {
                background: #eef2f5;
                color: #5c6b7f;
                border: 1px solid #e1e4e8;
                padding: 10px 20px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background: white;
                color: #3498db;
                border-bottom-color: white; /* 遮住pane的边框，实现融合效果 */
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background: #e1e8ed;
            }

            /* GroupBox 卡片式设计 */
            QGroupBox {
                background-color: white;
                border: 1px solid #e1e4e8;
                border-radius: 8px;
                margin-top: 1.2em; /* 为标题留出空间 */
                padding-top: 20px;
                padding-bottom: 15px;
                padding-left: 15px;
                padding-right: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 15px;
                padding: 0 5px;
                color: #2c3e50;
                font-weight: bold;
                font-size: 15px;
            }

            /* 输入控件通用样式 */
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 6px 10px;
                background: white;
                selection-background-color: #3498db;
                min-height: 20px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #3498db;
                background-color: #faffff;
            }
            QLineEdit:hover, QComboBox:hover, QSpinBox:hover {
                border: 1px solid #b4bccc;
            }

            /* 下拉框箭头 */
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 0px;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }

            /* 按钮样式 */
            QPushButton {
                background-color: #f5f7fa;
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                color: #606266;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #ecf5ff;
                color: #409eff;
                border-color: #c6e2ff;
            }
            QPushButton:pressed {
                background-color: #d9ecff;
            }

            /* 特殊按钮：保存/主要操作 */
            QPushButton#PrimaryButton {
                background-color: #27ae60;
                color: white;
                border: none;
            }
            QPushButton#PrimaryButton:hover {
                background-color: #2ecc71;
            }

            /* 特殊按钮：危险/删除 */
            QPushButton#DangerButton {
                background-color: #fff;
                color: #f56c6c;
                border: 1px solid #fbc4c4;
            }
            QPushButton#DangerButton:hover {
                background-color: #fef0f0;
                border-color: #f56c6c;
            }

            /* 标签文本 */
            QLabel {
                color: #606266;
            }

            /* 复选框 */
            QCheckBox {
                spacing: 8px;
                color: #606266;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)

    def setup_ui(self):
        """初始化用户界面"""
        self.setObjectName("SettingsPage")

        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 顶部标题栏
        header_layout = QHBoxLayout()
        title_label = QLabel("系统参数配置")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 选项卡控件
        self.tab_widget = QTabWidget()

        # 1. 系统设置
        system_tab = self.create_system_tab()
        self.tab_widget.addTab(system_tab, "系统显示")

        # 2. 网络设置
        network_tab = self.create_network_tab()
        self.tab_widget.addTab(network_tab, "网络通讯")

        # 3. 相机设置
        camera_tab = self.create_camera_tab()
        self.tab_widget.addTab(camera_tab, "视觉相机")

        # 4. 数据管理
        data_tab = self.create_data_tab()
        self.tab_widget.addTab(data_tab, "数据管理")

        # 5. 关于
        about_tab = self.create_about_tab()
        self.tab_widget.addTab(about_tab, "关于系统")

        layout.addWidget(self.tab_widget)

        # 底部操作栏
        button_widget = self.create_button_section()
        layout.addWidget(button_widget)

    def create_scrollable_widget(self, content_widget):
        """创建美化的可滚动区域"""
        content_widget.setObjectName("ScrollContents")
        scroll = QScrollArea()
        scroll.setWidget(content_widget)
        scroll.setWidgetResizable(True)
        # 移除默认边框，使用样式表控制
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        return scroll

    def _create_form_row(self, layout, label_text, widget, unit_text=None):
        """辅助函数：创建统一风格的表单行"""
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        label.setFixedWidth(140)  # 固定标签宽度，使布局整齐

        field_layout = QHBoxLayout()
        field_layout.addWidget(widget)
        if unit_text:
            unit_label = QLabel(unit_text)
            unit_label.setStyleSheet("color: #909399; margin-left: 5px;")
            field_layout.addWidget(unit_label)
        field_layout.addStretch()  # 让控件靠左对齐，不被拉伸过长

        # 如果widget是SpinBox/ComboBox，设置一个合理的固定宽度
        if isinstance(widget, (QSpinBox, QDoubleSpinBox, QComboBox)):
            widget.setMinimumWidth(180)
        elif isinstance(widget, QLineEdit):
            widget.setMinimumWidth(250)

        layout.addRow(label, field_layout)

    def create_system_tab(self):
        """系统设置 Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)

        # 界面显示设置
        display_group = QGroupBox("界面显示")
        display_layout = QFormLayout(display_group)
        display_layout.setVerticalSpacing(15)
        display_layout.setHorizontalSpacing(20)

        self.language_combo = QComboBox()
        self.language_combo.addItems(["简体中文 (zh-CN)", "English (en-US)"])
        self._create_form_row(display_layout, "系统语言:", self.language_combo)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        self._create_form_row(display_layout, "界面主题:", self.theme_combo)

        # 窗口尺寸
        size_layout = QHBoxLayout()
        self.window_width = QSpinBox()
        self.window_width.setRange(800, 3840)
        self.window_width.setFixedWidth(100)
        self.window_height = QSpinBox()
        self.window_height.setRange(600, 2160)
        self.window_height.setFixedWidth(100)

        size_layout.addWidget(self.window_width)
        size_layout.addWidget(QLabel(" x "))
        size_layout.addWidget(self.window_height)
        size_layout.addWidget(QLabel("像素"))
        size_layout.addStretch()

        label_size = QLabel("窗口尺寸:")
        label_size.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        label_size.setFixedWidth(140)
        display_layout.addRow(label_size, size_layout)

        layout.addWidget(display_group)

        # 性能与渲染
        perf_group = QGroupBox("性能与渲染")
        perf_layout = QFormLayout(perf_group)
        perf_layout.setVerticalSpacing(15)
        perf_layout.setHorizontalSpacing(20)

        self.refresh_rate_spin = QSpinBox()
        self.refresh_rate_spin.setRange(10, 1000)
        self._create_form_row(perf_layout, "UI刷新间隔:", self.refresh_rate_spin, "毫秒")

        self.max_data_points_spin = QSpinBox()
        self.max_data_points_spin.setRange(100, 10000)
        self._create_form_row(perf_layout, "图表最大点数:", self.max_data_points_spin, "个")

        self.hardware_accel_check = QCheckBox("启用硬件加速")
        self.hardware_accel_check.setToolTip("启用GPU加速以提高渲染性能")

        # 复选框单独处理
        cb_label = QLabel("图形加速:")
        cb_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        cb_label.setFixedWidth(140)
        perf_layout.addRow(cb_label, self.hardware_accel_check)

        self.image_quality_combo = QComboBox()
        self.image_quality_combo.addItems(["balanced", "high", "performance"])
        self._create_form_row(perf_layout, "图像渲染质量:", self.image_quality_combo)

        layout.addWidget(perf_group)
        layout.addStretch()
        return self.create_scrollable_widget(widget)

    def create_network_tab(self):
        """网络设置 Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)

        # OPC UA / 通讯设置
        opc_group = QGroupBox("OPC 通讯配置")
        opc_layout = QFormLayout(opc_group)
        opc_layout.setVerticalSpacing(15)

        # [新增] 启用开关
        self.opc_enabled_check = QCheckBox("启用 OPC UA 数据采集服务")
        self.opc_enabled_check.setStyleSheet("font-weight: bold; color: #2c3e50;")
        # 连接信号：当状态改变时，启用/禁用下方的输入框
        self.opc_enabled_check.toggled.connect(self.on_opc_enabled_toggled)

        opc_layout.addRow(QLabel("服务开关:"), self.opc_enabled_check)

        # URL 输入框
        self.opc_url_edit = QLineEdit()
        self.opc_url_edit.setPlaceholderText("http://...")
        self.opc_url_edit.setMinimumWidth(350)  # URL框宽一点
        self._create_form_row(opc_layout, "OPC服务器 URL:", self.opc_url_edit)

        self.api_endpoint_edit = QLineEdit()
        self.api_endpoint_edit.setMinimumWidth(350)
        self._create_form_row(opc_layout, "API 接口地址:", self.api_endpoint_edit)

        self.net_timeout_spin = QSpinBox()
        self.net_timeout_spin.setRange(1, 120)
        self._create_form_row(opc_layout, "请求超时时间:", self.net_timeout_spin, "秒")

        self.retry_count_spin = QSpinBox()
        self.retry_count_spin.setRange(0, 10)
        self._create_form_row(opc_layout, "失败重试次数:", self.retry_count_spin, "次")

        layout.addWidget(opc_group)

        # 数据更新频率
        interval_group = QGroupBox("数据采集频率")
        interval_layout = QFormLayout(interval_group)
        interval_layout.setVerticalSpacing(15)

        self.fast_tag_spin = QDoubleSpinBox()
        self.fast_tag_spin.setRange(0.1, 60.0)
        self.fast_tag_spin.setSingleStep(0.5)
        self._create_form_row(interval_layout, "快频数据 (液位/泡沫):", self.fast_tag_spin, "秒/次")

        self.slow_tag_spin = QDoubleSpinBox()
        self.slow_tag_spin.setRange(10.0, 3600.0)
        self.slow_tag_spin.setSingleStep(10.0)
        self._create_form_row(interval_layout, "慢频数据 (加药/化验):", self.slow_tag_spin, "秒/次")

        layout.addWidget(interval_group)
        layout.addStretch()
        return self.create_scrollable_widget(widget)

    def create_camera_tab(self):
        """相机设置 Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 顶部选择区域
        select_frame = QFrame()
        select_frame.setStyleSheet("""
            QFrame {
                background-color: #eef2f6;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        select_layout = QHBoxLayout(select_frame)

        select_label = QLabel("配置目标相机:")
        select_label.setStyleSheet("font-weight: bold; color: #34495e;")

        self.camera_select_combo = QComboBox()
        self.camera_select_combo.setMinimumWidth(250)
        self.camera_select_combo.currentIndexChanged.connect(self.on_camera_selection_changed)

        select_layout.addWidget(select_label)
        select_layout.addWidget(self.camera_select_combo)
        select_layout.addStretch()

        layout.addWidget(select_frame)

        # 相机详细参数
        self.camera_details_group = QGroupBox("详细参数配置")
        camera_layout = QFormLayout(self.camera_details_group)
        camera_layout.setVerticalSpacing(15)

        self.cam_enabled_check = QCheckBox("启用此相机")
        label_status = QLabel("相机状态:")
        label_status.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        label_status.setFixedWidth(140)
        camera_layout.addRow(label_status, self.cam_enabled_check)

        self.cam_name_edit = QLineEdit()
        self._create_form_row(camera_layout, "相机名称:", self.cam_name_edit)

        self.cam_rtsp_edit = QLineEdit()
        self.cam_rtsp_edit.setPlaceholderText("rtsp://admin:password@ip:port/...")
        self.cam_rtsp_edit.setMinimumWidth(350)
        self._create_form_row(camera_layout, "RTSP 流地址:", self.cam_rtsp_edit)

        # 分辨率与帧率
        self.cam_resolution_combo = QComboBox()
        self.cam_resolution_combo.addItems(["1920x1080", "1280x720", "640x480"])
        self._create_form_row(camera_layout, "分辨率:", self.cam_resolution_combo)

        self.cam_fps_spin = QSpinBox()
        self.cam_fps_spin.setRange(1, 60)
        self._create_form_row(camera_layout, "采集帧率:", self.cam_fps_spin, "FPS")

        self.cam_exposure_spin = QDoubleSpinBox()
        self.cam_exposure_spin.setRange(0.1, 1000.0)
        self._create_form_row(camera_layout, "曝光时间:", self.cam_exposure_spin, "ms")

        self.cam_gain_spin = QDoubleSpinBox()
        self.cam_gain_spin.setRange(0.0, 100.0)
        self._create_form_row(camera_layout, "数字增益:", self.cam_gain_spin, "dB")

        # 连接测试行
        test_layout = QHBoxLayout()
        test_layout.setContentsMargins(0, 10, 0, 0)

        self.test_rtsp_btn = QPushButton("测试视频流连接")
        self.test_rtsp_btn.setFixedWidth(140)
        self.test_rtsp_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.test_rtsp_btn.clicked.connect(self.on_test_rtsp_clicked)

        self.camera_status_label = QLabel("未测试")
        self.camera_status_label.setStyleSheet("color: #909399; margin-left: 10px;")

        test_layout.addWidget(self.test_rtsp_btn)
        test_layout.addWidget(self.camera_status_label)
        test_layout.addStretch()

        label_empty = QLabel("")  # 占位用
        label_empty.setFixedWidth(140)
        camera_layout.addRow(label_empty, test_layout)

        layout.addWidget(self.camera_details_group)
        layout.addStretch()

        self.current_camera_index = -1
        return self.create_scrollable_widget(widget)

    def create_data_tab(self):
        """数据管理 Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)

        # 存储设置
        save_group = QGroupBox("本地存储设置")
        save_layout = QFormLayout(save_group)
        save_layout.setVerticalSpacing(15)

        path_layout = QHBoxLayout()
        self.data_path_edit = QLineEdit()
        self.data_path_edit.setReadOnly(True)
        self.data_path_edit.setStyleSheet("background-color: #f5f7fa; color: #555;")
        path_layout.addWidget(self.data_path_edit)

        self.browse_path_btn = QPushButton("浏览...")
        self.browse_path_btn.setFixedWidth(80)
        self.browse_path_btn.clicked.connect(self.on_browse_data_path)
        path_layout.addWidget(self.browse_path_btn)

        label_path = QLabel("数据保存路径:")
        label_path.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        label_path.setFixedWidth(140)
        save_layout.addRow(label_path, path_layout)

        self.auto_save_spin = QSpinBox()
        self.auto_save_spin.setRange(1, 120)
        self._create_form_row(save_layout, "自动保存间隔:", self.auto_save_spin, "分钟")

        self.save_format_combo = QComboBox()
        self.save_format_combo.addItems(["CSV", "JSON", "Excel"])
        self._create_form_row(save_layout, "数据文件格式:", self.save_format_combo)

        self.save_images_check = QCheckBox("保存原始图像数据")
        label_img = QLabel("图像存储:")
        label_img.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        label_img.setFixedWidth(140)
        save_layout.addRow(label_img, self.save_images_check)

        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(50, 10000)
        self._create_form_row(save_layout, "内存缓存大小:", self.cache_size_spin, "MB")

        layout.addWidget(save_group)

        # 维护策略
        maint_group = QGroupBox("备份与维护策略")
        maint_layout = QFormLayout(maint_group)
        maint_layout.setVerticalSpacing(15)

        self.auto_backup_check = QCheckBox("启用自动备份")
        label_bk = QLabel("自动备份:")
        label_bk.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        label_bk.setFixedWidth(140)
        maint_layout.addRow(label_bk, self.auto_backup_check)

        path_layout2 = QHBoxLayout()
        self.backup_path_edit = QLineEdit()
        self.backup_path_edit.setReadOnly(True)
        self.backup_path_edit.setStyleSheet("background-color: #f5f7fa; color: #555;")
        path_layout2.addWidget(self.backup_path_edit)

        self.browse_backup_btn = QPushButton("浏览...")
        self.browse_backup_btn.setFixedWidth(80)
        self.browse_backup_btn.clicked.connect(self.on_browse_backup_path)
        path_layout2.addWidget(self.browse_backup_btn)

        label_bk_path = QLabel("备份目录:")
        label_bk_path.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        label_bk_path.setFixedWidth(140)
        maint_layout.addRow(label_bk_path, path_layout2)

        self.backup_freq_combo = QComboBox()
        self.backup_freq_combo.addItems(["daily", "weekly", "monthly"])
        self._create_form_row(maint_layout, "备份频率:", self.backup_freq_combo)

        self.auto_cleanup_check = QCheckBox("启用过期数据自动清理")
        label_cln = QLabel("自动清理:")
        label_cln.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        label_cln.setFixedWidth(140)
        maint_layout.addRow(label_cln, self.auto_cleanup_check)

        self.retention_days_spin = QSpinBox()
        self.retention_days_spin.setRange(1, 3650)
        self._create_form_row(maint_layout, "数据保留期限:", self.retention_days_spin, "天")

        # 立即清理按钮
        cleanup_layout = QHBoxLayout()
        self.cleanup_btn = QPushButton("立即执行清理")
        self.cleanup_btn.setObjectName("DangerButton")  # 使用红色样式
        self.cleanup_btn.setFixedWidth(120)
        self.cleanup_btn.clicked.connect(self.on_cleanup_clicked)
        cleanup_layout.addWidget(self.cleanup_btn)
        cleanup_layout.addStretch()

        label_act = QLabel("手动操作:")
        label_act.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        label_act.setFixedWidth(140)
        maint_layout.addRow(label_act, cleanup_layout)

        layout.addWidget(maint_group)
        layout.addStretch()
        return self.create_scrollable_widget(widget)

    def create_about_tab(self):
        """关于页面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        # Logo或图标区域（可选）
        logo_label = QLabel("🔬")
        logo_label.setStyleSheet("font-size: 64px;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

        title = QLabel("铅浮选过程工况智能监测与控制系统")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin-top: 10px;")
        layout.addWidget(title)

        ver_label = QLabel("Version 2.1.0")
        ver_label.setStyleSheet("color: #7f8c8d; font-size: 14px;")
        layout.addWidget(ver_label)

        layout.addSpacing(20)

        copy_label = QLabel("Copyright © 2024 Intelligent Monitoring Team\nAll Rights Reserved.")
        copy_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copy_label.setStyleSheet("color: #95a5a6; line-height: 150%;")
        layout.addWidget(copy_label)

        layout.addSpacing(30)

        self.update_btn = QPushButton("检查系统更新")
        self.update_btn.setFixedSize(140, 40)
        self.update_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white; border-radius: 20px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        self.update_btn.clicked.connect(lambda: QMessageBox.information(self, "更新检查", "当前已是最新版本 (v2.1.0)"))
        layout.addWidget(self.update_btn)

        return widget

    def create_button_section(self):
        """底部操作按钮区域"""
        widget = QWidget()
        widget.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(15)

        self.cancel_btn = QPushButton("放弃修改")
        self.cancel_btn.setFixedSize(120, 40)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.save_btn = QPushButton("保存所有配置")
        self.save_btn.setObjectName("PrimaryButton")
        self.save_btn.setFixedSize(150, 40)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # 添加阴影效果
        # graphics_effect = QGraphicsDropShadowEffect(...) # PySide6 简化处理，暂不添加复杂特效

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
        # 刷新配置数据
        self.config_manager = ConfigManager()
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
        net = self.config_manager.system_config.network

        # 先设置开关状态 (这会触发 toggled 信号，自动更新输入框的 enabled 状态)
        self.opc_enabled_check.setChecked(net.opc_enabled)
        # 也可以手动调用一次以确保状态正确
        self.on_opc_enabled_toggled(net.opc_enabled)

        self.opc_url_edit.setText(net.opc_server_url)
        self.api_endpoint_edit.setText(net.api_endpoint)
        self.net_timeout_spin.setValue(net.timeout)
        self.retry_count_spin.setValue(net.retry_count)
        self.fast_tag_spin.setValue(net.fast_tag_interval)
        self.slow_tag_spin.setValue(net.slow_tag_interval)

        # 3. Camera Config
        self.camera_select_combo.blockSignals(True)
        self.camera_select_combo.clear()
        for cam in sys_config.cameras:
            self.camera_select_combo.addItem(f"[{cam.camera_index}] {cam.name}", cam.camera_index)
        self.camera_select_combo.blockSignals(False)

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
        """相机下拉框切换"""
        if index < 0: return

        # 切换前保存当前内存中的临时数据（优化体验）
        if self.current_camera_index >= 0:
            self.save_current_camera_to_memory()

        self.load_camera_details(index)

    # [新增] 处理OPC开关切换的槽函数
    def on_opc_enabled_toggled(self, checked):
        """当OPC启用状态改变时，控制相关输入框的可用性"""
        self.opc_url_edit.setEnabled(checked)
        self.api_endpoint_edit.setEnabled(checked)
        self.net_timeout_spin.setEnabled(checked)
        self.retry_count_spin.setEnabled(checked)
        # 频率设置通常也依赖于OPC服务开启，根据需求也可以禁用
        self.fast_tag_spin.setEnabled(checked)
        self.slow_tag_spin.setEnabled(checked)

    def load_camera_details(self, combo_index):
        """加载指定相机的详情"""
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
        self.camera_status_label.setStyleSheet("color: #909399; margin-left: 10px;")

    def save_current_camera_to_memory(self):
        """将当前UI上的相机参数写回内存对象"""
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

            self.config_manager.update_camera_config(camera)

    def on_save_clicked(self):
        """保存按钮逻辑"""
        try:
            # 1. 保存当前相机页面的数据
            self.save_current_camera_to_memory()

            # 2. UI Config
            ui_config = self.config_manager.get_ui_config()
            ui_config.language = self.language_combo.currentText()
            ui_config.theme = self.theme_combo.currentText()
            ui_config.window_size = (self.window_width.value(), self.window_height.value())
            ui_config.refresh_rate = self.refresh_rate_spin.value()
            ui_config.max_data_points = self.max_data_points_spin.value()
            ui_config.hardware_acceleration = self.hardware_accel_check.isChecked()
            ui_config.image_quality = self.image_quality_combo.currentText()
            self.config_manager.update_ui_config(ui_config)

            # 3. Network Config
            net_config = self.config_manager.get_network_config()
            # [新增] 保存启用状态
            net_config.opc_enabled = self.opc_enabled_check.isChecked()

            net_config.opc_server_url = self.opc_url_edit.text()
            net_config.api_endpoint = self.api_endpoint_edit.text()
            net_config.timeout = self.net_timeout_spin.value()
            net_config.retry_count = self.retry_count_spin.value()
            net_config.fast_tag_interval = self.fast_tag_spin.value()
            net_config.slow_tag_interval = self.slow_tag_spin.value()
            self.config_manager.update_network_config(net_config)

            # 4. Data Config
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

            # 5. 持久化
            self.config_manager.save_config()

            QMessageBox.information(self, "保存成功", "系统配置已成功保存并生效！")
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

    def on_cleanup_clicked(self):
        reply = QMessageBox.warning(self, "确认清理",
                                    "确定要立即清理过期数据吗？\n此操作不可恢复！",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # 模拟清理
            QTimer.singleShot(1000, lambda: QMessageBox.information(self, "完成", "过期数据清理完毕。"))

    def on_test_rtsp_clicked(self):
        url = self.cam_rtsp_edit.text()
        if not url.startswith("rtsp://"):
            QMessageBox.warning(self, "格式错误", "RTSP地址必须以 rtsp:// 开头")
            return

        self.camera_status_label.setText("正在连接...")
        self.camera_status_label.setStyleSheet("color: #e67e22; margin-left: 10px; font-weight: bold;")

        # 模拟测试回调
        QTimer.singleShot(1500, lambda: self.finish_test(True))

    def finish_test(self, success):
        if success:
            self.camera_status_label.setText("连接正常")
            self.camera_status_label.setStyleSheet("color: #27ae60; margin-left: 10px; font-weight: bold;")
        else:
            self.camera_status_label.setText("连接失败")
            self.camera_status_label.setStyleSheet("color: #c0392b; margin-left: 10px; font-weight: bold;")
