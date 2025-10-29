import numpy as np
from PySide6.QtWidgets import (QMainWindow, QWidget, QLabel, QPushButton,
                               QVBoxLayout, QHBoxLayout, QGridLayout,
                               QTabWidget, QGroupBox, QComboBox, QSpinBox,
                               QDoubleSpinBox, QTableWidget, QStatusBar, QTextEdit,
                               QScrollArea, QTableWidgetItem, QProgressBar)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPixmap, QImage, QIcon, QKeyEvent
import pyqtgraph as pg
import cv2
from datetime import datetime
# 自定义模块，存放路径./utils
from system_logger import SystemLogger
from process_data import capture_frame_simulate


class FoamMonitoringSystem(QMainWindow):

    # 1.初始化与核心设置方法
    def __init__(self):
        super().__init__()
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

        # 3. 子图表组件（备用/扩展）
        self.bubble_size_plot = None
        self.bubble_size_curve = None
        self.flow_velocity_plot = None
        self.flow_velocity_curve = None
        self.texture_plot = None
        self.texture_curve = None

        # ==================== 数据管理变量 ====================
        # 1. 实时数据存储
        self.realtime_table = None
        self.history_table = None  # 历史数据表格

        # 2. 日志文本管理
        self.log_texts = {}  # 各选项卡日志文本框

        # ==================== 监控模块变量 ====================
        # 1. 视频监控
        self.video_labels = []  # 四个相机预览标签

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
        self.setGeometry(0, 0, 1600, 900)
        self.setWindowIcon(QIcon("src/icon.png"))

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)

        # 左侧四个相机预览区域
        self.setup_camera_previews(main_layout)

        # 右侧控制面板区域
        self.setup_control_panel(main_layout)

        # 状态栏
        self.setup_status_bar()

        # 启动定时器
        self.setup_timers()

        # 加载样式表
        # self.load_stylesheet()

        # 设置焦点策略，确保窗口能接收键盘事件
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

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
            with open("styles/diy.qss", "r", encoding="utf-8") as f:
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

    def setup_control_panel(self, main_layout):
        """设置右侧控制面板"""
        right_widget = QTabWidget()
        right_widget.setMinimumWidth(500)  # 设置最小宽度

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
        widget = QGroupBox("特征参数趋势")
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
        plot = self.graphics_widget.ci.addPlot(title="实时特征参数")
        plot.showGrid(x=True, y=True, alpha=0.3)
        plot.setLabel('left', '特征值')
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

    def setup_feature_charts(self):
        """特征参数图表 - 返回图表部件"""
        # 创建图表区域
        graphics_widget = pg.GraphicsLayoutWidget()
        graphics_widget.setMaximumHeight(250)  # 限制图表高度

        # 气泡大小分布图
        self.bubble_size_plot = graphics_widget.ci.addPlot(title="气泡大小分布")
        self.bubble_size_curve = self.bubble_size_plot.plot(pen='y')
        self.bubble_size_plot.setMaximumHeight(80)

        # 泡沫流速趋势图
        self.flow_velocity_plot = graphics_widget.ci.addPlot(title="泡沫流速趋势")
        self.flow_velocity_curve = self.flow_velocity_plot.plot(pen='b')
        self.flow_velocity_plot.setMaximumHeight(80)

        # 纹理特征图
        self.texture_plot = graphics_widget.ci.addPlot(title="纹理特征")
        self.texture_curve = self.texture_plot.plot(pen='g')
        self.texture_plot.setMaximumHeight(80)

        return graphics_widget

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

        clear_btn.clicked.connect(lambda: self.clear_logs(category, log_text))
        export_btn.clicked.connect(lambda: self.export_logs(category))

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

    def clear_logs(self, category, log_text):
        """清空日志"""
        self.logger.clear_logs()
        self.update_log_display(log_text)

    def export_logs(self, category):
        """导出日志到文件"""
        try:
            filename = f"logs/{category}_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
                # 模拟从不同泡沫相机获取视频帧
                ret, frame = capture_frame_simulate(i)  # if i != 0 else capture_frame_real(i)
                if ret:
                    # 转换为Qt图像格式
                    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb_image.shape
                    bytes_per_line = ch * w
                    qt_image = QImage(rgb_image.data, w, h, bytes_per_line,
                                      QImage.Format.Format_RGB888)

                    # 获取标签实际大小
                    label_width = foam_info['video_label'].width()
                    label_height = foam_info['video_label'].height()

                    # 缩放图像以适应标签大小
                    scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                        label_width,
                        label_height,
                        Qt.AspectRatioMode.KeepAspectRatio
                    )

                    # 设置标签的固定大小
                    foam_info['video_label'].setFixedSize(label_width, label_height)

                    # 设置标签的内容
                    foam_info['video_label'].setPixmap(scaled_pixmap)
                    foam_info['status_label'].setText("正常")
                    self.logger.add_log(f"相机 {i} 帧捕获成功", "INFO")
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
            process_data = self.get_process_data()

            # 更新图表
            self.update_charts(foam_features)

            # 更新预测结果
            self.update_predictions(process_data)

            # 更新控制参数显示
            self.update_control_display(process_data)

            self.logger.add_log("显示数据更新成功", "INFO")
        except Exception as e:
            self.logger.add_log(f"更新显示数据时出错: {e}", "ERROR")

    def update_status(self):
        """更新状态信息"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.time_label.setText(current_time)
            self.logger.add_log("状态信息更新成功", "INFO")
        except Exception as e:
            self.logger.add_log(f"更新状态信息时出错: {e}", "ERROR")

    def update_charts(self, foam_features):
        """更新图表显示 - 修复版本"""
        try:
            # 检查曲线对象是否已初始化
            if (self.bubble_curve is None or
                    self.flow_curve is None or
                    self.texture_curve is None):
                self.logger.add_log(f"图表曲线未初始化，跳过更新", "ERROR")
                return

            # 模拟数据更新
            x_data = np.linspace(0, 10, 100)

            # 气泡大小分布
            bubble_size = foam_features.get('bubble_size', 5)
            y_bubble = np.sin(x_data + bubble_size * 0.1)

            # 泡沫流速
            flow_velocity = foam_features.get('flow_velocity', [0, 0])[0]
            y_flow = np.cos(x_data + flow_velocity * 10)

            # 纹理特征
            texture_feature = foam_features.get('texture_feature', 0.5)
            y_texture = np.sin(x_data * 2) * texture_feature

            # 更新曲线数据
            self.bubble_curve.setData(x_data, y_bubble)
            self.flow_curve.setData(x_data, y_flow)
            self.texture_curve.setData(x_data, y_texture)

        except Exception as e:
            self.logger.add_log(f"更新图表时出错: {e}", "ERROR")

    def update_predictions(self, process_data):
        """更新预测结果显示"""
        try:
            grade = process_data.get('grade_prediction', 0)
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
                    group_box.setTitle("特征参数趋势 ▲")
                else:
                    group_box.setTitle("特征参数趋势 ▼")

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

    # 8. 图表相关方法
    def setup_chart_curves(self):
        """初始化图表曲线对象"""
        try:
            # 创建主图表
            self.main_plot = self.graphics_widget.ci.addPlot(title="实时特征参数")
            self.main_plot.showGrid(x=True, y=True, alpha=0.3)

            # 初始化三条曲线
            self.bubble_curve = self.main_plot.plot(
                pen=pg.mkPen(color='y', width=2),
                name="气泡大小"
            )
            self.flow_curve = self.main_plot.plot(
                pen=pg.mkPen(color='b', width=2),
                name="流速"
            )
            self.texture_curve = self.main_plot.plot(
                pen=pg.mkPen(color='g', width=2),
                name="纹理"
            )

            # 添加图例
            self.main_plot.addLegend()

            # 设置Y轴范围
            self.main_plot.setYRange(-1.5, 1.5)

        except Exception as e:
            self.logger.add_log(f"初始化图表曲线时出错: {e}", "ERROR")
            # 创建备用曲线对象
            self.bubble_curve = None
            self.flow_curve = None
            self.texture_curve = None
