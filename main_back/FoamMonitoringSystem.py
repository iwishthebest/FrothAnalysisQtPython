import numpy as np
from PySide6.QtWidgets import (QMainWindow, QWidget, QLabel, QPushButton,
                               QVBoxLayout, QHBoxLayout, QGridLayout,
                               QTabWidget, QGroupBox, QComboBox, QSpinBox,
                               QDoubleSpinBox, QTableWidget, QStatusBar, QTextEdit,
                               QScrollArea, QTableWidgetItem, QProgressBar, QStackedWidget)
from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QFont, QPixmap, QImage, QIcon, QKeyEvent, QPainter, QPen, QColor, QBrush
import pyqtgraph as pg
import cv2
from datetime import datetime

from RTSPStreamReader import RTSPStreamReader
# 自定义模块，存放路径./utils
from system_logger import SystemLogger
from process_data import capture_frame_simulate, get_process_data


class FoamMonitoringSystem(QMainWindow):

    # 1.初始化与核心设置方法
    def __init__(self):
        super().__init__()

        self.debugUI = True

        # ==================== 核心组件变量 ====================
        # 日志管理器
        self.logger = SystemLogger()

        # ==================== 界面组件变量 ====================
        # 1. 主界面布局组件
        self.graphics_widget = None
        self.charts_container = None
        self.main_plot = None
        self.realtime_table = None

        # 2. 图表曲线对象
        self.flow_curve = None
        self.bubble_curve = None
        self.texture_curve = None
        self.grade_curve = None

        # ==================== 数据管理变量 ====================
        # 1. 实时数据存储
        self.realtime_table = None
        self.history_table = None  # 历史数据表格

        # 2. 日志文本管理
        self.log_texts = {}  # 各选项卡日志文本框

        # ==================== 监控模块变量 ====================
        # 1. 视频监控
        self.video_labels = []  # 四个相机预览标签
        # RTSP流读取器列表
        self.rtsp_readers = []

        # 2. 工况状态显示
        self.condition_indicator = None
        self.condition_label = None
        self.grade_label = None
        self.recovery_label = None

        self.value_label = None
        self.title_label = None
        self.unit_label = None

        # ==================== 控制模块变量 ====================
        # 1. 液位控制
        self.level_setpoint = None
        self.current_level_label = None

        # 2. 加药量控制
        self.dosing_setpoint = None
        self.current_dosing_label = None
        self.reagent_combo = None

        # 3. 控制模式
        self.auto_mode_btn = None
        self.manual_mode_btn = None

        # ==================== 系统状态变量 ====================
        # 状态栏组件
        self.status_label = None
        self.time_label = None
        self.connection_label = None

        # ==================== 定时器变量 ====================
        self.data_timer = None  # 数据更新定时器
        self.status_timer = None  # 状态更新定时器
        self.video_timer = None  # 视频更新定时器
        self.logger_timer = None  # 日志更新定时器

        # ==================== 系统设置变量 ====================
        self.resolution_combo = None  # 分辨率设置
        self.save_interval = None  # 保存间隔

        # Window
        self.setWindowTitle("铅浮选过程工况智能监测与控制系统")
        self.setGeometry(0, 0, 1920, 1000)
        self.setWindowIcon(QIcon("../resources/icons/icon.png"))

        # 添加堆叠窗口管理左侧界面
        self.left_stack = QStackedWidget()

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)

        # 左侧堆叠窗口
        main_layout.addWidget(self.left_stack, 70)

        # 创建两个左侧界面
        self.setup_video_preview_page()  # 视频预览界面
        self.setup_control_interface()  # 控制参数界面

        # 左侧四个相机预览区域
        # self.setup_camera_previews(main_layout)
        # self.init_camera_reader()

        # 右侧控制面板区域
        self.setup_control_panel(main_layout)

        # 状态栏
        self.setup_status_bar()

        if not self.debugUI:
            # 相机初始化
            self.init_camera_reader()

            # 启动定时器
            self.setup_timers()

        # 加载样式表
        # self.load_stylesheet()

        # 设置焦点策略，确保窗口能接收键盘事件
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def setup_video_preview_page(self):
        """创建视频预览界面"""
        self.video_page = QWidget()
        video_layout = QVBoxLayout(self.video_page)

        # 将原有的相机预览设置移到这里
        grid_layout = QGridLayout()

        foam_positions = [
            ("铅快粗泡沫", 0, 0),
            ("铅精一泡沫", 0, 1),
            ("铅精二泡沫", 1, 0),
            ("铅精三泡沫", 1, 1)
        ]

        for foam_name, row, col in foam_positions:
            foam_group = QGroupBox(foam_name)
            foam_group_layout = QVBoxLayout(foam_group)

            video_label = QLabel()
            video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            video_label.setProperty("videoLabel", "true")

            status_label = QLabel("相机连接中...")
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            video_label.setLayout(QVBoxLayout())
            video_label.layout().addWidget(status_label)
            foam_group_layout.addWidget(video_label)
            foam_group_layout.setStretchFactor(video_label, 10)

            self.video_labels.append({
                'video_label': video_label,
                'status_label': status_label,
                'foam_name': foam_name
            })

            grid_layout.addWidget(foam_group, row, col)

        video_layout.addLayout(grid_layout)
        self.left_stack.addWidget(self.video_page)

    def setup_control_interface(self):
        """创建控制参数专用界面"""
        self.control_page = QWidget()
        control_layout = QVBoxLayout(self.control_page)
        control_layout.setSpacing(10)  # 设置适当的间距
        control_layout.setContentsMargins(10, 10, 10, 10)  # 设置边距

        control_layout.addStretch()

        # 控制参数标题
        title_label = QLabel("浮选过程控制参数")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        control_layout.addWidget(title_label)
        control_layout.addStretch()

        # 创建浮选槽串联可视化控件
        tanks_widget = self.create_flotation_tanks_visualization()
        control_layout.addWidget(tanks_widget)
        control_layout.addStretch()

        # 创建控制参数区域
        control_params_widget = self.create_control_parameters_panel()
        control_layout.addWidget(control_params_widget)

        # 添加弹性空间，使内容在顶部集中
        control_layout.addStretch()

        self.left_stack.addWidget(self.control_page)

    def create_flotation_tanks_visualization(self):
        """创建浮选槽串联可视化控件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 创建浮选槽容器
        tanks_container = QWidget()
        tanks_layout = QHBoxLayout(tanks_container)
        tanks_layout.setSpacing(0)  # 槽之间无间距

        # 定义四个浮选槽的信息
        tank_configs = [
            {"name": "铅快粗槽", "type": "粗选", "color": "#3498db"},
            {"name": "铅精一槽", "type": "精选一", "color": "#2ecc71"},
            {"name": "铅精二槽", "type": "精选二", "color": "#e74c3c"},
            {"name": "铅精三槽", "type": "精选三", "color": "#9b59b6"}
        ]

        # 创建四个浮选槽
        self.tank_widgets = []
        for i, config in enumerate(tank_configs):
            tank_widget = self.create_single_tank_widget(config, i)
            self.tank_widgets.append(tank_widget)
            tanks_layout.addWidget(tank_widget)

            # 如果不是最后一个槽，添加流向箭头
            if i < len(tank_configs) - 1:
                arrow_widget = self.create_flow_arrow()
                tanks_layout.addWidget(arrow_widget)

        layout.addWidget(tanks_container)
        return widget

    def create_single_tank_widget(self, config, tank_id):
        """创建单个浮选槽可视化控件"""
        widget = QWidget()
        widget.setMinimumWidth(180)
        widget.setMaximumWidth(220)
        widget.setMinimumHeight(200)

        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        # 槽名称
        name_label = QLabel(config["name"])
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {config['color']};")
        layout.addWidget(name_label)

        # 槽类型
        type_label = QLabel(config["type"])
        type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        type_label.setFont(QFont("Microsoft YaHei", 10))
        type_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(type_label)

        # 浮选槽图形
        tank_graphic = TankGraphicWidget(config["color"], tank_id)
        layout.addWidget(tank_graphic)

        # 关键参数显示
        params_widget = self.create_tank_parameters_display(tank_id)
        layout.addWidget(params_widget)

        return widget

    def create_tank_parameters_display(self, tank_id):
        """创建浮选槽参数显示区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(4)

        # 液位显示
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("液位:"))
        level_label = QLabel("-- m")
        level_label.setObjectName(f"tank_{tank_id}_level")
        level_label.setStyleSheet("font-weight: bold;")
        level_layout.addWidget(level_label)
        level_layout.addStretch()
        layout.addLayout(level_layout)

        # 加药量显示
        dosing_layout = QHBoxLayout()
        dosing_layout.addWidget(QLabel("加药:"))
        dosing_label = QLabel("-- ml/min")
        dosing_label.setObjectName(f"tank_{tank_id}_dosing")
        dosing_label.setStyleSheet("font-weight: bold;")
        dosing_layout.addWidget(dosing_label)
        dosing_layout.addStretch()
        layout.addLayout(dosing_layout)

        # 状态指示
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("状态:"))
        status_indicator = QLabel("●")
        status_indicator.setObjectName(f"tank_{tank_id}_status")
        status_indicator.setStyleSheet("color: green; font-weight: bold;")
        status_layout.addWidget(status_indicator)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        return widget

    def create_flow_arrow(self):
        """创建流向箭头"""
        widget = QWidget()
        widget.setFixedWidth(40)

        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 使用Unicode箭头字符
        arrow_label = QLabel("➡")
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow_label.setFont(QFont("Arial", 24))
        arrow_label.setStyleSheet("color: #95a5a6;")
        layout.addWidget(arrow_label)

        # 添加流动动画效果
        self.add_flow_animation(arrow_label)

        return widget

    def add_flow_animation(self, arrow_label):
        """为箭头添加流动动画效果"""
        try:
            from PySide6.QtCore import QPropertyAnimation, QEasingCurve
            from PySide6.QtGui import QFont

            # 创建字体大小动画
            self.animation = QPropertyAnimation(arrow_label, b"font")
            self.animation.setDuration(1000)
            self.animation.setLoopCount(-1)  # 无限循环

            # 创建字体对象
            font = QFont("Arial", 20)
            big_font = QFont("Arial", 28)

            self.animation.setStartValue(font)
            self.animation.setEndValue(big_font)
            self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
            self.animation.start()

        except Exception as e:
            self.logger.add_log(f"创建流动动画时出错: {e}", "WARNING")

    def create_control_parameters_panel(self):
        """创建控制参数面板"""
        widget = QGroupBox("浮选槽控制参数")
        layout = QHBoxLayout(widget)

        # 创建四个浮选槽的控制面板
        for i in range(4):
            control_panel = self.create_single_tank_control_panel(i)
            layout.addWidget(control_panel)

        return widget

    def create_single_tank_control_panel(self, tank_id):
        """创建单个浮选槽控制面板"""
        widget = QGroupBox(f"槽 {tank_id + 1}")
        layout = QVBoxLayout(widget)

        # 液位控制
        level_group = QGroupBox("液位控制")
        level_layout = QVBoxLayout(level_group)

        level_set_layout = QHBoxLayout()
        level_set_layout.addWidget(QLabel("设定:"))
        level_spinbox = QDoubleSpinBox()
        level_spinbox.setRange(0.5, 2.5)
        level_spinbox.setValue(1.2 + tank_id * 0.1)
        level_spinbox.setSuffix(" m")
        level_spinbox.valueChanged.connect(
            lambda value, tid=tank_id: self.on_tank_level_changed(tid, value)
        )
        level_set_layout.addWidget(level_spinbox)
        level_layout.addLayout(level_set_layout)

        widget.setMaximumWidth(200)
        layout.addWidget(level_group)

        # 加药量控制
        dosing_group = QGroupBox("加药控制")
        dosing_layout = QVBoxLayout(dosing_group)

        reagent_layout = QHBoxLayout()
        reagent_layout.addWidget(QLabel("药剂:"))
        reagent_combo = QComboBox()
        reagent_combo.addItems(["捕收剂", "起泡剂", "抑制剂"])
        reagent_combo.currentTextChanged.connect(
            lambda text, tid=tank_id: self.on_reagent_changed(tid, text)
        )
        reagent_layout.addWidget(reagent_combo)
        dosing_layout.addLayout(reagent_layout)

        dosing_set_layout = QHBoxLayout()
        dosing_set_layout.addWidget(QLabel("流量:"))
        dosing_spinbox = QDoubleSpinBox()
        dosing_spinbox.setRange(0, 200)
        dosing_spinbox.setValue(50 + tank_id * 10)
        dosing_spinbox.setSuffix(" ml/min")
        dosing_spinbox.valueChanged.connect(
            lambda value, tid=tank_id: self.on_dosing_changed(tid, value)
        )
        dosing_set_layout.addWidget(dosing_spinbox)
        dosing_layout.addLayout(dosing_set_layout)

        layout.addWidget(dosing_group)

        return widget

    def on_tank_level_changed(self, tank_id, value):
        """浮选槽液位设定值改变"""
        self.logger.add_log(f"浮选槽{tank_id + 1}液位设定为: {value} m", "INFO")
        # 更新可视化显示
        level_label = self.findChild(QLabel, f"tank_{tank_id}_level")
        if level_label:
            level_label.setText(f"{value:.1f} m")

    def on_dosing_changed(self, tank_id, value):
        """浮选槽加药量设定值改变"""
        self.logger.add_log(f"浮选槽{tank_id + 1}加药量设定为: {value} ml/min", "INFO")
        # 更新可视化显示
        dosing_label = self.findChild(QLabel, f"tank_{tank_id}_dosing")
        if dosing_label:
            dosing_label.setText(f"{value:.0f} ml/min")

    def on_reagent_changed(self, tank_id, reagent_type):
        """浮选槽药剂类型改变"""
        self.logger.add_log(f"浮选槽{tank_id + 1}药剂类型改为: {reagent_type}", "INFO")


    def create_flotation_tank_control(self, tank_name, description, tank_id):
        """创建单个浮选槽控制组"""
        group_box = QGroupBox(tank_name)
        group_box.setProperty("flotationTank", f"tank_{tank_id}")
        layout = QVBoxLayout(group_box)

        # 描述标签
        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(desc_label)

        # 液位控制区域
        level_group = QGroupBox("液位控制")
        level_layout = QGridLayout(level_group)

        # 设定值
        level_layout.addWidget(QLabel("设定值:"), 0, 0)
        level_spinbox = QDoubleSpinBox()
        level_spinbox.setRange(0.5, 2.5)
        level_spinbox.setValue(1.2 + tank_id * 0.1)  # 不同槽位不同默认值
        level_spinbox.setSuffix(" m")
        level_spinbox.valueChanged.connect(
            lambda value, tid=tank_id: self.on_tank_level_changed(tid, value)
        )
        level_layout.addWidget(level_spinbox, 0, 1)

        # 当前值显示
        current_level_label = QLabel("当前: -- m")
        current_level_label.setObjectName(f"tank_{tank_id}_current_level")
        level_layout.addWidget(current_level_label, 0, 2)

        # PID参数
        level_layout.addWidget(QLabel("PID参数:"), 1, 0)
        for j, (param, default) in enumerate([("Kp", 1.0), ("Ki", 0.1), ("Kd", 0.01)]):
            level_layout.addWidget(QLabel(f"{param}:"), 1, j * 2 + 1)
            pid_spinbox = QDoubleSpinBox()
            pid_spinbox.setRange(0, 10)
            pid_spinbox.setValue(default)
            pid_spinbox.setDecimals(3)
            setattr(self, f"tank_{tank_id}_pid_{param.lower()}", pid_spinbox)
            level_layout.addWidget(pid_spinbox, 1, j * 2 + 2)

        layout.addWidget(level_group)

        # 加药量控制区域
        dosing_group = QGroupBox("加药量控制")
        dosing_layout = QGridLayout(dosing_group)

        # 药剂类型选择
        dosing_layout.addWidget(QLabel("药剂类型:"), 0, 0)
        reagent_combo = QComboBox()
        reagent_combo.addItems(["捕收剂", "起泡剂", "抑制剂"])
        reagent_combo.currentTextChanged.connect(
            lambda text, tid=tank_id: self.on_reagent_changed(tid, text)
        )
        dosing_layout.addWidget(reagent_combo, 0, 1)

        # 加药量设定
        dosing_layout.addWidget(QLabel("加药量:"), 1, 0)
        dosing_spinbox = QDoubleSpinBox()
        dosing_spinbox.setRange(0, 200)
        dosing_spinbox.setValue(50 + tank_id * 10)
        dosing_spinbox.setSuffix(" ml/min")
        dosing_spinbox.valueChanged.connect(
            lambda value, tid=tank_id: self.on_dosing_changed(tid, value)
        )
        dosing_layout.addWidget(dosing_spinbox, 1, 1)

        # 当前加药量显示
        current_dosing_label = QLabel("当前: -- ml/min")
        current_dosing_label.setObjectName(f"tank_{tank_id}_current_dosing")
        dosing_layout.addWidget(current_dosing_label, 1, 2)

        layout.addWidget(dosing_group)

        # 状态指示区域
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)

        # 运行状态指示灯
        status_indicator = QLabel()
        status_indicator.setFixedSize(12, 12)
        status_indicator.setStyleSheet("background-color: green; border-radius: 6px;")
        status_indicator.setObjectName(f"tank_{tank_id}_status")
        status_layout.addWidget(status_indicator)

        # 状态文本
        status_text = QLabel("运行正常")
        status_text.setObjectName(f"tank_{tank_id}_status_text")
        status_layout.addWidget(status_text)
        status_layout.addStretch()

        # 泡沫质量指示
        foam_quality = QLabel("泡沫质量: 良好")
        foam_quality.setObjectName(f"tank_{tank_id}_foam_quality")
        status_layout.addWidget(foam_quality)

        layout.addWidget(status_widget)

        return group_box


    def init_camera_reader(self):
        # 初始化RTSP流读取器
        for i, foam_info in enumerate(self.video_labels):
            if i != 0:
                continue
            rtsp_url = f"rtsp://admin:fkqxk010@192.168.1.{101 + i}:554/Streaming/Channels/101?tcp"
            reader = RTSPStreamReader(rtsp_url)
            if reader.start():
                self.rtsp_readers.append(reader)
            else:
                self.logger.add_log(f"无法启动RTSP流读取器 {i}", "ERROR")

    def keyPressEvent(self, event: QKeyEvent):
        """重写键盘按下事件处理"""
        if event.key() == Qt.Key.Key_F5:
            # 按下F5键时重载QSS
            self.reload_qss()
            event.accept()  # 标记事件已处理
        else:
            super().keyPressEvent(event)  # 其他按键按默认方式处理

    def load_stylesheet(self):
        """加载样式表"""
        try:
            with open("../resources/styles/diy.qss", "r", encoding="utf-8") as f:
                stylesheet = f.read()
                self.setStyleSheet(stylesheet)
        except FileNotFoundError:
            # 如果文件不存在，使用内置的样式字符串
            tech_stylesheet = """
            /* 这里放置上面的样式表内容 */
            """
            self.setStyleSheet(tech_stylesheet)

    def reload_qss(self):
        """重载QSS样式表"""
        self.load_stylesheet()
        # self.status_label.setText("样式已重载 (F5)")
        self.logger.add_log("reload qss", "INFO")

    def setup_timers(self):
        """设置定时器"""
        # 数据更新定时器
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self.update_display_data)
        self.data_timer.start(100)  # 10Hz更新

        # 视频更新定时器
        self.video_timer = QTimer()
        self.video_timer.timeout.connect(self.update_video_display)
        self.video_timer.start(33)  # 30fps

        # 状态更新定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # 1Hz

        # 统一日志更新定时器
        self.logger_timer = QTimer()
        self.logger_timer.timeout.connect(self.update_all_logs)
        self.logger_timer.start(1000)  # 1秒更新一次

    # 2. 界面布局设置方法
    def setup_camera_previews(self, main_layout):
        """设置四台相机预览界面"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # 创建网格布局放置四个相机预览
        grid_layout = QGridLayout()

        # 铅浮选过程关键泡沫位置
        foam_positions = [
            ("铅快粗泡沫", 0, 0),  # 粗选阶段，泡沫较大
            ("铅精一泡沫", 0, 1),  # 第一次精选
            ("铅精二泡沫", 1, 0),  # 第二次精选
            ("铅精三泡沫", 1, 1)  # 第三次精选
        ]

        # 创建四个相机预览标签
        for foam_name, row, col in foam_positions:
            # 创建泡沫监控组框
            foam_group = QGroupBox(foam_name)
            foam_group_layout = QVBoxLayout(foam_group)

            # 创建视频显示标签
            video_label = QLabel()
            video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # 设置属性以便 QSS 选择器识别
            video_label.setProperty("videoLabel", "true")

            # 添加状态标签
            status_label = QLabel("相机连接中...")
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # 将 status_label 设置为 video_label 的子部件
            video_label.setLayout(QVBoxLayout())
            video_label.layout().addWidget(status_label)

            # 将 video_label 添加到 foam_group_layout 中
            foam_group_layout.addWidget(video_label)
            # 设置布局的伸缩因子
            foam_group_layout.setStretchFactor(video_label, 10)  # 视频标签占据100%的高度

            # 存储视频标签和状态标签的引用
            self.video_labels.append({
                'video_label': video_label,
                'status_label': status_label,
                'foam_name': foam_name
            })

            grid_layout.addWidget(foam_group, row, col)

        left_layout.addLayout(grid_layout)
        main_layout.addWidget(left_widget, 70)  # 70%宽度

    def on_tab_changed(self, index):
        """处理选项卡切换事件"""
        tab_titles = ["实时监测", "控制参数", "历史数据", "系统设置"]
        current_tab = tab_titles[index] if index < len(tab_titles) else "未知"

        if current_tab == "控制参数":
            # 切换到控制参数界面
            self.left_stack.setCurrentWidget(self.control_page)
            self.logger.add_log("切换到控制参数界面", "INFO")
        else:
            # 切换回视频预览界面
            self.left_stack.setCurrentWidget(self.video_page)
            self.logger.add_log("切换到视频预览界面", "INFO")

    def setup_control_panel(self, main_layout):
        """设置右侧控制面板"""
        right_widget = QTabWidget()
        right_widget.setMinimumWidth(500)  # 设置最小宽度

        # 连接选项卡切换信号
        right_widget.currentChanged.connect(self.on_tab_changed)

        # 选项卡1: 实时监测
        self.setup_monitoring_tab(right_widget)

        # 选项卡2: 控制参数
        self.setup_control_tab(right_widget)

        # 选项卡3: 历史数据
        self.setup_history_tab(right_widget)

        # 选项卡4: 系统设置
        self.setup_settings_tab(right_widget)

        main_layout.addWidget(right_widget, 30)  # 30%宽度

    def setup_monitoring_tab(self, tab_widget):
        """实时监测选项卡 - 优化布局版本"""
        monitor_tab = QWidget()
        main_layout = QVBoxLayout(monitor_tab)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 12, 12, 12)  # 设置边距

        # 创建滚动区域容器
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(10)  # 减少内部间距
        scroll_layout.setContentsMargins(8, 8, 8, 8)

        # 1. 工况状态区域 - 优化布局
        condition_widget = self.create_condition_section()
        scroll_layout.addWidget(condition_widget)

        # 2. 关键指标预测 - 优化布局
        prediction_widget = self.create_prediction_section()
        scroll_layout.addWidget(prediction_widget)

        # 3. 特征参数图表 - 优化布局
        charts_widget = self.create_charts_section()
        scroll_layout.addWidget(charts_widget)

        # 4. 实时数据表格 - 优化布局
        data_widget = self.create_realtime_data_section()
        scroll_layout.addWidget(data_widget)

        scroll_layout.addStretch()

        # 滚动区域设置
        scroll_area = QScrollArea()
        scroll_area.setWidget(scroll_content)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(600)  # 调整高度
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)  # 去除边框

        main_layout.addWidget(scroll_area)

        # 5. 日志显示区域 - 优化布局
        self.setup_log_display(main_layout, 'monitoring', 180)

        tab_widget.addTab(monitor_tab, "实时监测")

    def setup_control_tab(self, tab_widget):
        """控制参数选项卡 - 优化布局"""
        control_tab = QWidget()
        main_layout = QVBoxLayout(control_tab)

        # 创建滚动区域
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # 液位控制组 - 紧凑布局
        level_group = QGroupBox("液位智能控制")
        level_layout = QVBoxLayout(level_group)
        self.setup_level_control(level_layout)
        level_group.setMaximumHeight(120)
        scroll_layout.addWidget(level_group)

        # 加药量控制组 - 紧凑布局
        dosing_group = QGroupBox("加药量自动控制")
        dosing_layout = QVBoxLayout(dosing_group)
        self.setup_dosing_control(dosing_layout)
        dosing_group.setMaximumHeight(120)
        scroll_layout.addWidget(dosing_group)

        # 控制模式选择 - 紧凑布局
        mode_widget = QWidget()
        mode_layout = QHBoxLayout(mode_widget)
        self.setup_control_mode(mode_layout)
        mode_widget.setMaximumHeight(60)
        scroll_layout.addWidget(mode_widget)

        scroll_layout.addStretch()

        # 滚动区域
        from PySide6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(300)

        main_layout.addWidget(scroll_area)

        # 添加日志显示区域
        self.setup_log_display(main_layout, 'control', 180)

        tab_widget.addTab(control_tab, "控制参数")

    def setup_history_tab(self, tab_widget):
        """历史数据选项卡 - 优化布局"""
        try:
            history_tab = QWidget()
            main_layout = QVBoxLayout(history_tab)

            # 历史数据表格 - 占据主要空间
            table_widget = QWidget()
            table_layout = QVBoxLayout(table_widget)

            self.history_table = QTableWidget()
            self.history_table.setColumnCount(5)
            self.history_table.setHorizontalHeaderLabels([
                "时间", "工况", "铅品位%", "回收率%", "液位(m)"
            ])
            # 设置表格属性
            self.history_table.setAlternatingRowColors(True)
            self.history_table.setSelectionBehavior(
                QTableWidget.SelectionBehavior.SelectRows)
            self.history_table.setMaximumHeight(400)

            table_layout.addWidget(self.history_table)
            main_layout.addWidget(table_widget)

            # 添加日志显示区域
            self.setup_log_display(main_layout, 'history', 180)

            tab_widget.addTab(history_tab, "历史数据")
        except Exception as e:
            self.logger.add_log(f"设置历史数据选项卡时出错: {e}", "WARNING")

    def setup_settings_tab(self, tab_widget):
        """系统设置选项卡 - 优化布局"""
        try:
            settings_tab = QWidget()
            main_layout = QVBoxLayout(settings_tab)

            # 系统设置组 - 紧凑布局
            settings_group = QGroupBox("系统设置")
            settings_layout = QVBoxLayout(settings_group)
            settings_group.setMaximumHeight(150)

            # 相机设置
            camera_layout = QHBoxLayout()
            camera_layout.addWidget(QLabel("相机分辨率:"))
            self.resolution_combo = QComboBox()
            self.resolution_combo.addItems(
                ["640x480", "1280x720", "1920x1080"])
            camera_layout.addWidget(self.resolution_combo)
            camera_layout.addStretch()
            settings_layout.addLayout(camera_layout)

            # 数据保存设置
            save_layout = QHBoxLayout()
            save_layout.addWidget(QLabel("数据保存间隔:"))
            self.save_interval = QSpinBox()
            self.save_interval.setRange(1, 60)
            self.save_interval.setValue(10)
            self.save_interval.setSuffix(" 分钟")
            save_layout.addWidget(self.save_interval)
            save_layout.addStretch()
            settings_layout.addLayout(save_layout)

            main_layout.addWidget(settings_group)
            main_layout.addStretch()  # 添加弹性空间

            # 添加日志显示区域
            self.setup_log_display(main_layout, 'settings', 180)

            tab_widget.addTab(settings_tab, "系统设置")
        except Exception as e:
            self.logger.add_log(f"设置系统设置选项卡时出错: {e}", "ERROR")

    def setup_status_bar(self):
        """设置状态栏"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        # 系统状态标签
        self.status_label = QLabel("系统就绪")
        status_bar.addWidget(self.status_label)

        # 时间显示
        self.time_label = QLabel()
        status_bar.addPermanentWidget(self.time_label)

        # 连接状态
        self.connection_label = QLabel("PLC: 已连接 | 泡沫相机: 4/4 已连接")
        status_bar.addPermanentWidget(self.connection_label)

    # 3. 界面组件创建方法
    def create_condition_section(self):
        """创建工况状态区域 - 优化版本"""
        widget = QGroupBox("工况状态监控")
        widget.setMaximumHeight(90)  # 限制高度
        layout = QHBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 12, 16, 12)

        # 指示灯 - 优化样式
        self.condition_indicator = QLabel()
        self.condition_indicator.setFixedSize(30, 30)
        self.condition_indicator.setStyleSheet("background-color: green; border-radius: 5px;")
        self.condition_indicator.setProperty("conditionIndicator", "true")

        # 状态信息区域
        status_widget = QWidget()
        status_layout = QVBoxLayout(status_widget)
        status_layout.setSpacing(8)
        status_layout.setContentsMargins(0, 0, 0, 0)

        self.condition_label = QLabel("正常工况")
        self.condition_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        self.condition_label.setStyleSheet("color: #2c3e50;")

        # 指标显示
        indicators_widget = QWidget()
        indicators_layout = QHBoxLayout(indicators_widget)
        indicators_layout.setSpacing(24)
        indicators_layout.setContentsMargins(0, 0, 0, 0)

        self.grade_label = QLabel("铅品位: --%")
        self.recovery_label = QLabel("回收率: --%")

        # 设置指标样式
        for label in [self.grade_label, self.recovery_label]:
            label.setFont(QFont("Microsoft YaHei", 12))
            label.setStyleSheet("color: #34495e;")

        indicators_layout.addWidget(self.grade_label)
        indicators_layout.addWidget(self.recovery_label)
        indicators_layout.addStretch()

        status_layout.addWidget(self.condition_label)
        status_layout.addWidget(indicators_widget)

        layout.addWidget(self.condition_indicator)
        layout.addSpacing(16)  # 添加间距
        layout.addWidget(status_widget)
        layout.addStretch()

        return widget

    def create_prediction_section(self):
        """创建关键指标预测区域 - 优化版本"""
        widget = QGroupBox("关键指标预测")
        widget.setMaximumHeight(100)
        layout = QHBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(16, 12, 16, 12)

        # 创建两个预测项
        grade_item = self.create_prediction_item(
            "铅品位预测", "grade", "%", "#e74c3c")
        recovery_item = self.create_prediction_item(
            "回收率预测", "recovery", "%", "#3498db")

        layout.addWidget(grade_item)
        layout.addWidget(recovery_item)
        layout.addStretch()

        return widget

    def create_charts_section(self):
        """创建图表区域 - 优化版本"""
        widget = QGroupBox("精矿实时品位")
        widget.setCheckable(True)
        widget.setChecked(False)
        widget.toggled.connect(
            lambda checked: self.on_charts_toggled(checked, widget))

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 12, 16, 12)

        # 图表容器
        self.charts_container = QWidget()
        charts_layout = QVBoxLayout(self.charts_container)
        charts_layout.setContentsMargins(4, 4, 4, 4)

        self.graphics_widget = pg.GraphicsLayoutWidget()
        self.graphics_widget.setMaximumHeight(200)
        self.graphics_widget.setMinimumHeight(150)

        # 创建图表
        plot = self.graphics_widget.ci.addPlot(title="实时品位值")
        plot.showGrid(x=True, y=True, alpha=0.3)
        plot.setLabel('left', '品位值')
        plot.setLabel('bottom', '时间', 's')

        # 设置颜色主题
        plot.getAxis('left').setPen(pg.mkPen(color='#2c3e50', width=1))
        plot.getAxis('bottom').setPen(pg.mkPen(color='#2c3e50', width=1))

        # 初始化曲线
        self.bubble_curve = plot.plot(
            pen=pg.mkPen(color='#e67e22', width=2),
            name="气泡大小"
        )
        self.flow_curve = plot.plot(
            pen=pg.mkPen(color='#3498db', width=2),
            name="流速"
        )
        self.texture_curve = plot.plot(
            pen=pg.mkPen(color='#27ae60', width=2),
            name="纹理"
        )
        self.grade_curve = plot.plot(
            pen=pg.mkPen(color='r', width=2),
            name="品位"
        )

        plot.addLegend(offset=(-10, 10))
        charts_layout.addWidget(self.graphics_widget)

        layout.addWidget(self.charts_container)
        self.charts_container.setVisible(False)

        return widget

    def create_realtime_data_section(self):
        """创建实时数据表格 - 优化版本"""
        widget = QGroupBox("实时数据")
        widget.setMaximumHeight(200)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 16, 12, 16)

        # 创建紧凑型表格
        table = QTableWidget(6, 3)
        table.setHorizontalHeaderLabels(["参数", "数值", "单位"])
        table.setVerticalHeaderLabels([
            "泡沫厚度", "气泡尺寸", "流速", "纹理", "稳定性", "浓度"
        ])

        # 优化表格样式
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setStretchLastSection(True)
        table.setMaximumHeight(160)
        table.setMinimumHeight(140)

        # 设置列宽
        table.setColumnWidth(0, 120)
        table.setColumnWidth(1, 100)

        layout.addWidget(table)
        self.realtime_table = table

        return widget

    def setup_prediction_display(self, layout):
        """预测结果显示 - 紧凑布局"""
        prediction_group = QGroupBox("关键指标预测")
        prediction_layout = QHBoxLayout(prediction_group)
        prediction_group.setMaximumHeight(70)  # 限制高度

        # 品位预测
        self.grade_label = QLabel("铅品位: --%")
        self.grade_label.setFont(QFont("Arial", 12))

        # 回收率预测
        self.recovery_label = QLabel("回收率: --%")
        self.recovery_label.setFont(QFont("Arial", 12))

        prediction_layout.addWidget(self.grade_label)
        prediction_layout.addWidget(self.recovery_label)
        prediction_layout.addStretch()

        layout.addWidget(prediction_group)

    def setup_level_control(self, layout):
        """液位控制设置"""
        # 液位设定值
        level_setting_layout = QHBoxLayout()
        level_setting_layout.addWidget(QLabel("液位设定:"))
        self.level_setpoint = QDoubleSpinBox()
        self.level_setpoint.setRange(0.5, 2.5)
        self.level_setpoint.setValue(1.2)
        self.level_setpoint.setSuffix(" m")
        level_setting_layout.addWidget(self.level_setpoint)

        # 当前液位显示
        self.current_level_label = QLabel("当前: -- m")
        level_setting_layout.addWidget(self.current_level_label)
        layout.addLayout(level_setting_layout)

        # PID参数
        pid_layout = QHBoxLayout()
        for param, default in [("Kp", 1.0), ("Ki", 0.1), ("Kd", 0.01)]:
            pid_layout.addWidget(QLabel(f"{param}:"))
            spinbox = QDoubleSpinBox()
            spinbox.setRange(0, 10)
            spinbox.setValue(default)
            setattr(self, f"pid_{param.lower()}", spinbox)
            pid_layout.addWidget(spinbox)

        layout.addLayout(pid_layout)

    def setup_dosing_control(self, layout):
        """加药量控制设置"""
        # 药剂类型选择
        reagent_layout = QHBoxLayout()
        reagent_layout.addWidget(QLabel("药剂类型:"))
        self.reagent_combo = QComboBox()
        self.reagent_combo.addItems(["捕收剂", "起泡剂", "抑制剂"])
        reagent_layout.addWidget(self.reagent_combo)
        layout.addLayout(reagent_layout)

        # 加药量控制
        dosing_layout = QHBoxLayout()
        dosing_layout.addWidget(QLabel("加药量设定:"))
        self.dosing_setpoint = QDoubleSpinBox()
        self.dosing_setpoint.setRange(0, 100)
        self.dosing_setpoint.setValue(50)
        self.dosing_setpoint.setSuffix(" ml/min")
        dosing_layout.addWidget(self.dosing_setpoint)

        self.current_dosing_label = QLabel("当前: -- ml/min")
        dosing_layout.addWidget(self.current_dosing_label)
        layout.addLayout(dosing_layout)

    def setup_control_mode(self, layout):
        """控制模式选择"""
        try:
            mode_layout = QHBoxLayout()
            mode_layout.addWidget(QLabel("控制模式:"))

            self.auto_mode_btn = QPushButton("自动")
            self.manual_mode_btn = QPushButton("手动")

            # 设置为可切换按钮
            self.auto_mode_btn.setCheckable(True)
            self.manual_mode_btn.setCheckable(True)
            self.auto_mode_btn.setChecked(True)

            # 连接信号
            self.auto_mode_btn.clicked.connect(self.on_auto_mode_selected)
            self.manual_mode_btn.clicked.connect(self.on_manual_mode_selected)

            mode_layout.addWidget(self.auto_mode_btn)
            mode_layout.addWidget(self.manual_mode_btn)
            layout.addLayout(mode_layout)

        except Exception as e:
            self.logger.add_log(f"选择自动模式时出错: {e}", "ERROR")

    def create_prediction_item(self, title, key, unit, color):
        """创建单个预测项 - 优化版本"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 4, 8, 4)

        # 标题区域
        title_layout = QHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Microsoft YaHei", 9))
        self.title_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        # 数值显示
        value_layout = QHBoxLayout()
        self.value_label = QLabel("--")
        self.value_label.setObjectName(f"{key}_value")
        self.value_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        self.value_label.setStyleSheet(f"color: {color};")

        self.unit_label = QLabel(unit)
        self.unit_label.setFont(QFont("Microsoft YaHei", 10))
        self.unit_label.setStyleSheet("color: #7f8c8d;")

        value_layout.addWidget(self.value_label)
        value_layout.addWidget(self.unit_label)
        value_layout.addStretch()

        # 进度条
        progress = QProgressBar()
        progress.setObjectName(f"{key}_progress")
        progress.setRange(0, 100)
        progress.setTextVisible(False)
        progress.setFixedHeight(6)
        progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: #ecf0f1;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 2px;
            }}
        """)

        layout.addLayout(title_layout)
        layout.addLayout(value_layout)
        layout.addWidget(progress)

        return widget

    # 4. 日志管理方法
    def setup_log_display(self, layout, category, max_height=180):
        """设置统一尺寸的日志显示区域"""
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout(log_group)
        log_layout.setSpacing(6)
        log_layout.setContentsMargins(8, 10, 8, 8)

        # 设置固定高度
        log_group.setFixedHeight(max_height)

        # 日志文本框
        log_text = QTextEdit()
        log_text.setReadOnly(True)
        log_text.setFixedHeight(120)

        # 按钮区域
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)

        clear_btn = QPushButton("清空日志")
        export_btn = QPushButton("导出日志")

        # 设置按钮样式
        for btn in [clear_btn, export_btn]:
            btn.setFixedHeight(25)
            btn.setFixedWidth(80)

        clear_btn.clicked.connect(lambda: self.clear_logs(category))
        export_btn.clicked.connect(lambda: self.export_logs())

        button_layout.addWidget(clear_btn)
        button_layout.addWidget(export_btn)
        button_layout.addStretch()

        log_layout.addWidget(log_text)
        log_layout.addWidget(button_widget)

        layout.addWidget(log_group)

        # 存储到字典中
        self.log_texts[category] = log_text
        return log_text

    def update_log_display(self, log_text):
        """更新日志显示"""
        logs = self.logger.get_logs()
        log_text.setPlainText("\n".join(logs))
        # 滚动到底部
        log_text.verticalScrollBar().setValue(
            log_text.verticalScrollBar().maximum()
        )

    def update_all_logs(self):
        """统一更新所有选项卡的日志显示"""
        try:
            for category, log_text in self.log_texts.items():
                if log_text is not None:
                    self.update_log_display(log_text)
        except Exception as e:
            self.logger.add_log(f"更新日志显示时出错: {e}", "ERROR")

    def clear_logs(self, log_text):
        """清空日志"""
        self.logger.clear_logs()
        self.update_log_display(log_text)

    def export_logs(self):
        """导出日志到文件"""
        try:
            filename = f"logs/log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            logs = self.logger.get_logs()
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("\n".join(logs))
            self.logger.add_log(f"日志已导出到 {filename}", "INFO")
        except Exception as e:
            self.logger.add_log(f"导出日志失败: {str(e)}", "ERROR")

    # 5. 数据更新与显示方法
    def update_video_display(self):
        """更新四台泡沫相机预览显示"""
        for i, foam_info in enumerate(self.video_labels):

            try:
                if i != 0:
                    frame = capture_frame_simulate(i)
                else:
                    # 从RTSPStreamReader获取最新帧
                    frame = self.rtsp_readers[i].get_frame(timeout=2)
                if frame is not None:
                    # 转换为Qt图像格式
                    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb_image.shape
                    bytes_per_line = ch * w
                    qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

                    # 获取标签实际大小
                    label_width = foam_info['video_label'].width()
                    label_height = foam_info['video_label'].height()

                    # 缩放图像以适应标签大小
                    scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                        label_width,
                        label_height,
                        Qt.AspectRatioMode.KeepAspectRatio
                    )

                    # 设置标签的内容
                    foam_info['video_label'].setPixmap(scaled_pixmap)
                    foam_info['status_label'].setText("正常")
                else:
                    foam_info['status_label'].setText("无信号")
                    self.logger.add_log(f"相机 {i} 无信号", "WARNING")

            except Exception as e:
                foam_info['status_label'].setText("错误")
                self.logger.add_log(f"更新泡沫相机 {i} 显示时出错: {e}", "ERROR")

    def update_display_data(self):
        """更新显示数据"""
        try:
            # 模拟数据更新 - 实际应用中从模型和传感器获取
            foam_features = self.get_foam_features()
            process_data = get_process_data()

            # 更新图表
            self.update_charts(process_data)

            # 更新预测结果
            self.update_predictions(process_data)

            # 更新控制参数显示
            self.update_control_display(process_data)

            # self.logger.add_log("显示数据更新成功", "INFO")
        except Exception as e:
            self.logger.add_log(f"更新显示数据时出错: {e}", "ERROR")

    def update_status(self):
        """更新状态信息"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.time_label.setText(current_time)
            # self.logger.add_log("状态信息更新成功", "INFO")
        except Exception as e:
            self.logger.add_log(f"更新状态信息时出错: {e}", "ERROR")

    def update_charts(self, process_data):
        """更新图表显示 - 修复版本"""
        try:
            # 检查曲线对象是否已初始化
            if self.grade_curve is None:
                self.logger.add_log(f"图表曲线未初始化，跳过更新", "ERROR")
                return

            # 提取品位数据
            grade_pb = process_data.get('KYFX.kyfx_gqxk_grade_Pb')

            # 更新时间轴数据（使用当前时间戳，并转换为分钟）
            current_time = datetime.now()
            if not hasattr(self, 'start_time'):
                self.start_time = current_time  # 设置起始时间为第一次调用的时间
            elapsed_minutes = (current_time - self.start_time).total_seconds() / 60.0

            if not hasattr(self, 'x_data'):
                self.x_data = [elapsed_minutes]
            else:
                self.x_data.append(elapsed_minutes)

            # 更新品位值
            if not hasattr(self, 'y_data_pb'):
                self.y_data_pb = [grade_pb]
            else:
                self.y_data_pb.append(grade_pb)

            # 限制数据长度以防止内存溢出
            max_data_points = 100
            if len(self.x_data) > max_data_points:
                self.x_data = self.x_data[-max_data_points:]
                self.y_data_pb = self.y_data_pb[-max_data_points:]

            # 更新曲线数据
            self.grade_curve.setData(self.x_data, self.y_data_pb)

        except Exception as e:
            self.logger.add_log(f"更新图表时出错: {e}", "ERROR")

    def update_predictions(self, process_data):
        """更新预测结果显示"""
        try:
            grade = process_data.get('KYFX.kyfx_gqxk_grade_Pb', 0)
            recovery = process_data.get('recovery_prediction', 0)

            self.grade_label.setText(f"铅品位: {grade:.1f}%")
            self.recovery_label.setText(f"回收率: {recovery:.1f}%")

        except Exception as e:
            self.logger.add_log(f"更新预测显示时出错: {e}", "ERROR")

    def update_control_display(self, process_data):
        """更新控制参数显示"""
        try:
            current_level = process_data.get('current_level', 0)
            current_dosing = process_data.get('current_dosing', 0)

            self.current_level_label.setText(f"当前: {current_level:.2f} m")
            self.current_dosing_label.setText(f"当前: {current_dosing:.1f} ml/min")

        except Exception as e:
            self.logger.add_log(f"更新控制显示时出错: {e}", "ERROR")

    def update_realtime_table(self, foam_features):
        """更新实时数据表格"""
        data_mapping = [
            ("厚度", foam_features.get('foam_thickness', 0), "cm"),
            ("尺寸", foam_features.get('bubble_size', 0), "mm"),
            ("流速", foam_features.get('flow_velocity', [0, 0])[0], "cm/s"),
            ("纹理", foam_features.get('texture_feature', 0), ""),
            ("稳定性", foam_features.get('stability', 0), "%"),
            ("浓度", foam_features.get('concentration', 0), "g/L")
        ]

        for row, (_, value, unit) in enumerate(data_mapping):
            self.realtime_table.setItem(
                row, 1, QTableWidgetItem(f"{value:.2f}"))
            self.realtime_table.setItem(row, 2, QTableWidgetItem(unit))

    def update_prediction_display(self, process_data):
        """更新预测显示（优化版）"""
        grade = process_data.get('grade_prediction', 0)
        recovery = process_data.get('recovery_prediction', 0)

        # 更新数值显示
        grade_label = self.findChild(QLabel, "grade_prediction_value")
        recovery_label = self.findChild(QLabel, "recovery_prediction_value")

        if grade_label:
            grade_label.setText(f"{grade:.1f}")
        if recovery_label:
            recovery_label.setText(f"{recovery:.1f}")

        # 更新进度条
        grade_progress = self.findChild(
            QProgressBar, "grade_prediction_progress")
        recovery_progress = self.findChild(
            QProgressBar, "recovery_prediction_progress")

        if grade_progress:
            grade_progress.setValue(int(grade))
        if recovery_progress:
            recovery_progress.setValue(int(recovery))

    # 6. 事件处理方法
    def on_charts_toggled(self, checked, group_box=None):
        """图表区域折叠/展开事件 - 完整修复版本"""
        try:
            # 确保有正确的group_box引用
            if group_box is None:
                group_box = self.sender()

            if group_box and hasattr(self, 'charts_container'):
                self.charts_container.setVisible(checked)

                # 更新标题
                if checked:
                    group_box.setTitle("精矿实时品位 ▲")
                else:
                    group_box.setTitle("精矿实时品位 ▼")

        except Exception as e:
            self.logger.add_log(f"切换图表显示时出错: {e}", "ERROR")

    def on_auto_mode_selected(self):
        """自动模式选择"""
        try:
            if self.auto_mode_btn.isChecked():
                self.manual_mode_btn.setChecked(False)
                self.status_label.setText("控制模式: 自动")
        except Exception as e:
            self.logger.add_log(f"选择自动模式时出错: {e}", "ERROR")

    def on_manual_mode_selected(self):
        """手动模式选择"""
        try:
            if self.manual_mode_btn.isChecked():
                self.auto_mode_btn.setChecked(False)
                self.status_label.setText("控制模式: 手动")
        except Exception as e:
            self.logger.add_log(f"选择手动模式时出错: {e}", "ERROR")

    # 7. 数据获取方法（静态方法）
    @staticmethod
    def get_foam_features():
        """模拟获取泡沫特征数据"""
        return {
            'bubble_size': np.random.uniform(5, 15),
            'flow_velocity': [np.random.uniform(-0.1, 0.1), np.random.uniform(-0.1, 0.1)],
            'texture_feature': np.random.uniform(0, 1)
        }

    @staticmethod
    def get_process_data():
        """模拟获取工艺过程数据"""
        grade_pb = -1
        grade_zn = -1
        return {
            'current_level': np.random.uniform(1.1, 1.3),
            'current_dosing': np.random.uniform(45, 55),
            'grade_prediction': grade_pb,
            'recovery_prediction': grade_zn
        }

# 自定义浮选槽图形控件
class TankGraphicWidget(QWidget):
    def __init__(self, color, tank_id):
        super().__init__()
        self.color = color
        self.tank_id = tank_id
        self.setMinimumSize(120, 100)
        self.setMaximumSize(150, 120)

        # 模拟液位高度 (0.0 - 1.0)
        self.water_level = 0.6

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制浮选槽外框
        rect = self.rect().adjusted(10, 10, -10, -10)
        painter.setPen(QPen(QColor(self.color), 3))
        painter.setBrush(QBrush(QColor(240, 240, 240)))
        painter.drawRoundedRect(rect, 10, 10)

        # 绘制液位
        water_height = int(rect.height() * self.water_level)
        water_rect = QRect(rect.left(), rect.bottom() - water_height,
                           rect.width(), water_height)

        water_color = QColor(self.color)
        water_color.setAlpha(128)
        painter.setBrush(QBrush(water_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(water_rect, 8, 8)

        # 绘制泡沫层
        foam_height = max(10, water_height // 5)
        foam_rect = QRect(rect.left(), water_rect.top() - foam_height,
                          rect.width(), foam_height)

        foam_color = QColor(255, 255, 255, 180)
        painter.setBrush(QBrush(foam_color))
        painter.drawRoundedRect(foam_rect, 5, 5)

        # 绘制液位刻度
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        for i in range(0, 101, 20):
            y_pos = rect.bottom() - int(rect.height() * i / 100)
            painter.drawLine(rect.left() - 5, y_pos, rect.left(), y_pos)

        painter.end()
