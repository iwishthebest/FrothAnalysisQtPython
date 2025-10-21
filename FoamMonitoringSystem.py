import numpy as np
from PySide6.QtWidgets import (QMainWindow, QWidget, QLabel, QPushButton,
                               QVBoxLayout, QHBoxLayout, QGridLayout,
                               QTabWidget, QGroupBox, QComboBox, QSpinBox,
                               QDoubleSpinBox, QTableWidget, QStatusBar, QTextEdit)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPixmap, QImage, QIcon
import pyqtgraph as pg
import cv2
from datetime import datetime
from utils.system_logger import SystemLogger
from utils.capture_frame import capture_frame


class FoamMonitoringSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        # 添加日志管理器
        self.logger = SystemLogger()
        self.log_text_edit = None

        # 视频监控相关变量
        self.video_labels = []  # 存储四个相机预览标签
        self.video_timer = None

        # 图表显示相关变量
        self.bubble_size_plot = None
        self.bubble_size_curve = None
        self.flow_velocity_plot = None
        self.flow_velocity_curve = None
        self.texture_plot = None
        self.texture_curve = None

        # 控制参数相关变量
        self.level_setpoint = None
        self.current_level_label = None
        self.dosing_setpoint = None
        self.current_dosing_label = None
        self.reagent_combo = None
        self.auto_mode_btn = None
        self.manual_mode_btn = None

        # 状态显示相关变量
        self.condition_indicator = None
        self.condition_label = None
        self.grade_label = None
        self.recovery_label = None
        self.status_label = None
        self.time_label = None
        self.connection_label = None

        # 定时器相关变量
        self.data_timer = None
        self.status_timer = None

        # 历史数据相关变量
        self.history_table = None

        # 系统设置相关变量
        self.resolution_combo = None
        self.save_interval = None

        # Window
        self.setWindowTitle("铅浮选过程工况智能监测与控制系统")
        self.setGeometry(50, 50, 1600, 900)
        self.setWindowIcon(QIcon("src/icon.png"))

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)

        # 左侧四相机预览区域
        self.setup_camera_previews(main_layout)

        # 右侧控制面板区域
        self.setup_control_panel(main_layout)

        # 状态栏
        self.setup_status_bar()

        # 启动定时器
        self.setup_timers()

        # 加载样式表
        self.load_stylesheet()

    def load_stylesheet(self):
        """加载科技风样式表"""
        try:
            with open("styles/tech_style.qss", "r", encoding="utf-8") as f:
                stylesheet = f.read()
                self.setStyleSheet(stylesheet)
        except FileNotFoundError:
            # 如果文件不存在，使用内置的样式字符串
            tech_stylesheet = """
            /* 这里放置上面的样式表内容 */
            """
            self.setStyleSheet(tech_stylesheet)

    def setup_log_display(self, layout, category):
        """设置日志显示区域"""
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout(log_group)

        # 日志显示文本框
        log_text = QTextEdit()
        log_text.setReadOnly(True)
        log_text.setMaximumHeight(200)

        # 日志控制按钮
        button_layout = QHBoxLayout()
        clear_btn = QPushButton("清空日志")
        export_btn = QPushButton("导出日志")

        clear_btn.clicked.connect(lambda: self.clear_logs(category, log_text))
        export_btn.clicked.connect(lambda: self.export_logs(category))

        button_layout.addWidget(clear_btn)
        button_layout.addWidget(export_btn)

        log_layout.addWidget(log_text)
        log_layout.addLayout(button_layout)

        layout.addWidget(log_group)

        # 返回文本框引用用于更新
        return log_text

    def update_log_display(self, log_text, category):
        """更新日志显示"""
        logs = self.logger.get_logs(category)
        log_text.setPlainText("\n".join(logs))
        # 滚动到底部
        log_text.verticalScrollBar().setValue(
            log_text.verticalScrollBar().maximum()
        )

    def clear_logs(self, category, log_text):
        """清空日志"""
        self.logger.clear_logs(category)
        self.update_log_display(log_text, category)

    def export_logs(self, category):
        """导出日志到文件"""
        try:
            filename = f"logs/{category}_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            logs = self.logger.get_logs(category)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("\n".join(logs))
            self.logger.add_log(category, f"日志已导出到 {filename}")
        except Exception as e:
            self.logger.add_log(category, f"导出日志失败: {str(e)}", "ERROR")

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
            video_label.setFixedSize(300, 225)  # 调整尺寸以适应四宫格布局
            video_label.setStyleSheet("border: 2px solid gray; background-color: black;")
            video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # 设置属性以便 QSS 选择器识别
            video_label.setProperty("videoLabel", "true")

            # 添加状态标签
            status_label = QLabel("相机连接中...")
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            foam_group_layout.addWidget(video_label)
            foam_group_layout.addWidget(status_label)

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
        """实时监测选项卡"""
        monitor_tab = QWidget()
        layout = QVBoxLayout(monitor_tab)

        # 工况状态显示
        self.setup_condition_monitoring(layout)

        # 特征参数图表
        self.setup_feature_charts(layout)

        # 预测结果显示
        self.setup_prediction_display(layout)

        # +++ 新增：添加日志显示区域 +++
        self.setup_log_display(layout, category=monitor_tab.objectName())

        tab_widget.addTab(monitor_tab, "实时监测")

    def setup_control_tab(self, tab_widget):
        """控制参数选项卡"""
        control_tab = QWidget()
        layout = QVBoxLayout(control_tab)

        # 液位控制组
        level_group = QGroupBox("液位智能控制")
        level_layout = QVBoxLayout(level_group)

        # 液位控制参数
        self.setup_level_control(level_layout)
        layout.addWidget(level_group)

        # 加药量控制组
        dosing_group = QGroupBox("加药量自动控制")
        dosing_layout = QVBoxLayout(dosing_group)
        self.setup_dosing_control(dosing_layout)
        layout.addWidget(dosing_group)

        # 控制模式选择
        self.setup_control_mode(layout)

        tab_widget.addTab(control_tab, "控制参数")

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

    def setup_condition_monitoring(self, layout):
        """工况状态监控"""
        condition_group = QGroupBox("工况状态")
        condition_layout = QHBoxLayout(condition_group)

        # 工况指示灯
        self.condition_indicator = QLabel()
        self.condition_indicator.setFixedSize(100, 100)
        self.condition_indicator.setStyleSheet(
            "background-color: green; border-radius: 50px;")
        self.condition_indicator.setProperty("conditionIndicator", "true")

        # 工况描述
        self.condition_label = QLabel("正常工况")
        self.condition_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))

        condition_layout.addWidget(self.condition_indicator)
        condition_layout.addWidget(self.condition_label)
        layout.addWidget(condition_group)

    def setup_feature_charts(self, layout):
        """特征参数图表"""
        # 创建图表区域
        graphics_widget = pg.GraphicsLayoutWidget()

        # 气泡大小分布图
        self.bubble_size_plot = graphics_widget.ci.addPlot(title="气泡大小分布")
        self.bubble_size_curve = self.bubble_size_plot.plot(pen='y')

        # 泡沫流速趋势图
        self.flow_velocity_plot = graphics_widget.ci.addPlot(title="泡沫流速趋势")
        self.flow_velocity_curve = self.flow_velocity_plot.plot(pen='b')

        graphics_widget.ci.nextRow()

        # 纹理特征图
        self.texture_plot = graphics_widget.ci.addPlot(title="纹理特征")
        self.texture_curve = self.texture_plot.plot(pen='g')

        layout.addWidget(graphics_widget)

    def setup_prediction_display(self, layout):
        """预测结果显示"""
        prediction_group = QGroupBox("关键指标预测")
        prediction_layout = QHBoxLayout(prediction_group)

        # 品位预测
        self.grade_label = QLabel("铅品位: --%")
        self.grade_label.setFont(QFont("Arial", 14))

        # 回收率预测
        self.recovery_label = QLabel("回收率: --%")
        self.recovery_label.setFont(QFont("Arial", 14))

        prediction_layout.addWidget(self.grade_label)
        prediction_layout.addWidget(self.recovery_label)
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

    def setup_history_tab(self, tab_widget):
        """历史数据选项卡"""
        try:
            history_tab = QWidget()
            layout = QVBoxLayout(history_tab)

            # 历史数据表格
            self.history_table = QTableWidget()
            self.history_table.setColumnCount(5)
            self.history_table.setHorizontalHeaderLabels([
                "时间", "工况", "铅品位%", "回收率%", "液位(m)"
            ])
            layout.addWidget(self.history_table)

            tab_widget.addTab(history_tab, "历史数据")
        except Exception as e:
            print(f"设置历史数据选项卡时出错: {e}")

    def setup_settings_tab(self, tab_widget):
        """系统设置选项卡"""
        try:
            settings_tab = QWidget()
            layout = QVBoxLayout(settings_tab)

            # 系统设置组
            settings_group = QGroupBox("系统设置")
            settings_layout = QVBoxLayout(settings_group)

            # 相机设置
            camera_layout = QHBoxLayout()
            camera_layout.addWidget(QLabel("相机分辨率:"))
            self.resolution_combo = QComboBox()
            self.resolution_combo.addItems(["640x480", "1280x720", "1920x1080"])
            camera_layout.addWidget(self.resolution_combo)
            settings_layout.addLayout(camera_layout)

            # 数据保存设置
            save_layout = QHBoxLayout()
            save_layout.addWidget(QLabel("数据保存间隔:"))
            self.save_interval = QSpinBox()
            self.save_interval.setRange(1, 60)
            self.save_interval.setValue(10)
            self.save_interval.setSuffix(" 分钟")
            save_layout.addWidget(self.save_interval)
            settings_layout.addLayout(save_layout)

            layout.addWidget(settings_group)
            tab_widget.addTab(settings_tab, "系统设置")
        except Exception as e:
            print(f"设置系统设置选项卡时出错: {e}")

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
            print(f"设置控制模式时出错: {e}")

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
        return {
            'current_level': np.random.uniform(1.1, 1.3),
            'current_dosing': np.random.uniform(45, 55),
            'grade_prediction': np.random.uniform(85, 95),
            'recovery_prediction': np.random.uniform(88, 92)
        }

    def update_video_display(self):
        """更新四台泡沫相机预览显示"""
        for i, foam_info in enumerate(self.video_labels):
            try:
                # 模拟从不同泡沫相机获取视频帧
                ret, frame = capture_frame(i)
                if ret:
                    # 转换为Qt图像格式
                    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb_image.shape
                    bytes_per_line = ch * w
                    qt_image = QImage(rgb_image.data, w, h, bytes_per_line,
                                      QImage.Format.Format_RGB888)

                    # 缩放图像以适应标签大小
                    scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                        foam_info['video_label'].width(),
                        foam_info['video_label'].height(),
                        Qt.AspectRatioMode.KeepAspectRatio
                    )
                    foam_info['video_label'].setPixmap(scaled_pixmap)
                    foam_info['status_label'].setText("正常")
                else:
                    foam_info['status_label'].setText("无信号")

            except Exception as e:
                print(f"更新泡沫相机 {i} 显示时出错: {e}")
                foam_info['status_label'].setText("错误")

    def update_display_data(self):
        """更新显示数据"""
        # 模拟数据更新 - 实际应用中从模型和传感器获取
        foam_features = self.get_foam_features()
        process_data = self.get_process_data()

        # 更新图表
        self.update_charts(foam_features)

        # 更新预测结果
        self.update_predictions(process_data)

        # 更新控制参数显示
        self.update_control_display(process_data)

    def update_status(self):
        """更新状态信息"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)

    def update_charts(self, foam_features):
        """更新图表显示"""
        try:
            # 模拟数据更新
            x_data = np.linspace(0, 10, 100)

            # 气泡大小分布
            y_bubble = np.sin(x_data + foam_features.get('bubble_size', 0) * 0.1)
            self.bubble_size_curve.setData(x_data, y_bubble)

            # 泡沫流速
            y_flow = np.cos(x_data + foam_features.get('flow_velocity', [0, 0])[0] * 10)
            self.flow_velocity_curve.setData(x_data, y_flow)

            # 纹理特征
            y_texture = np.sin(x_data * 2) * foam_features.get('texture_feature', 0.5)
            self.texture_curve.setData(x_data, y_texture)

        except Exception as e:
            print(f"更新图表时出错: {e}")

    def update_predictions(self, process_data):
        """更新预测结果显示"""
        try:
            grade = process_data.get('grade_prediction', 0)
            recovery = process_data.get('recovery_prediction', 0)

            self.grade_label.setText(f"铅品位: {grade:.1f}%")
            self.recovery_label.setText(f"回收率: {recovery:.1f}%")

        except Exception as e:
            print(f"更新预测显示时出错: {e}")

    def update_control_display(self, process_data):
        """更新控制参数显示"""
        try:
            current_level = process_data.get('current_level', 0)
            current_dosing = process_data.get('current_dosing', 0)

            self.current_level_label.setText(f"当前: {current_level:.2f} m")
            self.current_dosing_label.setText(f"当前: {current_dosing:.1f} ml/min")

        except Exception as e:
            print(f"更新控制显示时出错: {e}")

    def on_auto_mode_selected(self):
        """自动模式选择"""
        try:
            if self.auto_mode_btn.isChecked():
                self.manual_mode_btn.setChecked(False)
                self.status_label.setText("控制模式: 自动")
        except Exception as e:
            print(f"选择自动模式时出错: {e}")

    def on_manual_mode_selected(self):
        """手动模式选择"""
        try:
            if self.manual_mode_btn.isChecked():
                self.auto_mode_btn.setChecked(False)
                self.status_label.setText("控制模式: 手动")
        except Exception as e:
            print(f"选择手动模式时出错: {e}")
