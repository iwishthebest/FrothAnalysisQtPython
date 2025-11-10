"""
设置页面 - 系统配置和参数设置
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QGroupBox, QLabel, QLineEdit, QComboBox,
                               QSpinBox, QDoubleSpinBox, QCheckBox,
                               QPushButton, QTabWidget, QTextEdit,
                               QMessageBox, QFileDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIntValidator
import json
import os


class SettingsPage(QWidget):
    """设置页面 - 系统配置和参数设置"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_file = "system_config.json"
        self.current_config = self._load_default_config()
        self._setup_ui()
        self._load_config()

    def _setup_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("系统设置")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 选项卡控件
        self.tab_widget = QTabWidget()

        # 添加各个设置选项卡
        self.tab_widget.addTab(self._create_general_tab(), "基本设置")
        self.tab_widget.addTab(self._create_camera_tab(), "相机设置")
        self.tab_widget.addTab(self._create_network_tab(), "网络设置")
        self.tab_widget.addTab(self._create_alarm_tab(), "报警设置")
        self.tab_widget.addTab(self._create_about_tab(), "关于")

        layout.addWidget(self.tab_widget)

        # 操作按钮
        button_layout = QHBoxLayout()

        self.save_btn = QPushButton("保存设置")
        self.save_btn.clicked.connect(self._save_config)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
            }
        """)

        self.reset_btn = QPushButton("恢复默认")
        self.reset_btn.clicked.connect(self._reset_config)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
            }
        """)

        self.export_btn = QPushButton("导出配置")
        self.export_btn.clicked.connect(self._export_config)

        self.import_btn = QPushButton("导入配置")
        self.import_btn.clicked.connect(self._import_config)

        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.import_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

    def _create_general_tab(self):
        """创建基本设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 界面设置
        interface_group = QGroupBox("界面设置")
        interface_layout = QVBoxLayout(interface_group)

        # 主题选择
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("主题:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色主题", "深色主题", "自动"])
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        interface_layout.addLayout(theme_layout)

        # 语言选择
        language_layout = QHBoxLayout()
        language_layout.addWidget(QLabel("语言:"))
        self.language_combo = QComboBox()
        self.language_combo.addItems(["中文", "English"])
        language_layout.addWidget(self.language_combo)
        language_layout.addStretch()
        interface_layout.addLayout(language_layout)

        # 刷新率设置
        refresh_layout = QHBoxLayout()
        refresh_layout.addWidget(QLabel("刷新率:"))
        self.refresh_spinbox = QSpinBox()
        self.refresh_spinbox.setRange(1, 100)
        self.refresh_spinbox.setSuffix(" Hz")
        refresh_layout.addWidget(self.refresh_spinbox)
        refresh_layout.addStretch()
        interface_layout.addLayout(refresh_layout)

        layout.addWidget(interface_group)

        # 数据设置
        data_group = QGroupBox("数据设置")
        data_layout = QVBoxLayout(data_group)

        # 数据保存周期
        save_layout = QHBoxLayout()
        save_layout.addWidget(QLabel("数据保存周期:"))
        self.save_interval = QSpinBox()
        self.save_interval.setRange(1, 60)
        self.save_interval.setSuffix(" 分钟")
        save_layout.addWidget(self.save_interval)
        save_layout.addStretch()
        data_layout.addLayout(save_layout)

        # 历史数据保留天数
        history_layout = QHBoxLayout()
        history_layout.addWidget(QLabel("历史数据保留:"))
        self.history_days = QSpinBox()
        self.history_days.setRange(1, 365)
        self.history_days.setSuffix(" 天")
        history_layout.addWidget(self.history_days)
        history_layout.addStretch()
        data_layout.addLayout(history_layout)

        layout.addWidget(data_group)

        return widget

    def _create_camera_tab(self):
        """创建相机设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # RTSP设置
        rtsp_group = QGroupBox("RTSP相机设置")
        rtsp_layout = QVBoxLayout(rtsp_group)

        cameras = ["铅快粗泡沫相机", "铅精一泡沫相机", "铅精二泡沫相机", "铅精三泡沫相机"]

        for i, camera in enumerate(cameras):
            camera_group = QGroupBox(camera)
            camera_layout = QVBoxLayout(camera_group)

            # RTSP地址
            url_layout = QHBoxLayout()
            url_layout.addWidget(QLabel("RTSP地址:"))
            url_edit = QLineEdit()
            url_edit.setPlaceholderText(f"rtsp://192.168.1.{101 + i}/stream")
            setattr(self, f"camera_{i}_url", url_edit)
            url_layout.addWidget(url_edit)
            camera_layout.addLayout(url_layout)

            # 用户名密码
            auth_layout = QHBoxLayout()
            auth_layout.addWidget(QLabel("用户名:"))
            user_edit = QLineEdit()
            user_edit.setPlaceholderText("admin")
            setattr(self, f"camera_{i}_user", user_edit)
            auth_layout.addWidget(user_edit)

            auth_layout.addWidget(QLabel("密码:"))
            pass_edit = QLineEdit()
            pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
            pass_edit.setPlaceholderText("password")
            setattr(self, f"camera_{i}_pass", pass_edit)
            auth_layout.addWidget(pass_edit)
            camera_layout.addLayout(auth_layout)

            # 启用复选框
            enable_check = QCheckBox("启用该相机")
            enable_check.setChecked(True)
            setattr(self, f"camera_{i}_enable", enable_check)
            camera_layout.addWidget(enable_check)

            rtsp_layout.addWidget(camera_group)

        layout.addWidget(rtsp_group)

        return widget

    def _create_network_tab(self):
        """创建网络设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # OPC UA设置
        opc_group = QGroupBox("OPC UA服务器设置")
        opc_layout = QVBoxLayout(opc_group)

        # 服务器地址
        server_layout = QHBoxLayout()
        server_layout.addWidget(QLabel("服务器地址:"))
        self.opc_server_url = QLineEdit()
        self.opc_server_url.setPlaceholderText("opc.tcp://localhost:4840")
        server_layout.addWidget(self.opc_server_url)
        opc_layout.addLayout(server_layout)

        # 连接超时
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("连接超时:"))
        self.opc_timeout = QSpinBox()
        self.opc_timeout.setRange(5, 60)
        self.opc_timeout.setSuffix(" 秒")
        timeout_layout.addWidget(self.opc_timeout)
        opc_layout.addLayout(timeout_layout)

        layout.addWidget(opc_group)

        # API设置
        api_group = QGroupBox("API接口设置")
        api_layout = QVBoxLayout(api_group)

        # API端点
        api_endpoint_layout = QHBoxLayout()
        api_endpoint_layout.addWidget(QLabel("API端点:"))
        self.api_endpoint = QLineEdit()
        self.api_endpoint.setPlaceholderText("http://localhost:8000/api")
        api_endpoint_layout.addWidget(self.api_endpoint)
        api_layout.addLayout(api_endpoint_layout)

        layout.addWidget(api_group)

        return widget

    def _create_alarm_tab(self):
        """创建报警设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 液位报警
        level_group = QGroupBox("液位报警设置")
        level_layout = QVBoxLayout(level_group)

        # 上限报警
        high_layout = QHBoxLayout()
        high_layout.addWidget(QLabel("上限报警:"))
        self.level_high_alarm = QDoubleSpinBox()
        self.level_high_alarm.setRange(1.0, 3.0)
        self.level_high_alarm.setValue(2.0)
        self.level_high_alarm.setSuffix(" m")
        high_layout.addWidget(self.level_high_alarm)
        level_layout.addLayout(high_layout)

        # 下限报警
        low_layout = QHBoxLayout()
        low_layout.addWidget(QLabel("下限报警:"))
        self.level_low_alarm = QDoubleSpinBox()
        self.level_low_alarm.setRange(0.5, 2.0)
        self.level_low_alarm.setValue(0.8)
        self.level_low_alarm.setSuffix(" m")
        low_layout.addWidget(self.level_low_alarm)
        level_layout.addLayout(low_layout)

        layout.addWidget(level_group)

        # 品位报警
        grade_group = QGroupBox("品位报警设置")
        grade_layout = QVBoxLayout(grade_group)

        grade_layout.addWidget(QLabel("铅品位下限报警:"))
        self.grade_low_alarm = QDoubleSpinBox()
        self.grade_low_alarm.setRange(50, 90)
        self.grade_low_alarm.setValue(80)
        self.grade_low_alarm.setSuffix(" %")
        grade_layout.addWidget(self.grade_low_alarm)

        layout.addWidget(grade_group)

        # 报警方式
        method_group = QGroupBox("报警方式")
        method_layout = QVBoxLayout(method_group)

        self.alarm_sound = QCheckBox("声音报警")
        self.alarm_sound.setChecked(True)
        method_layout.addWidget(self.alarm_sound)

        self.alarm_popup = QCheckBox("弹窗报警")
        self.alarm_popup.setChecked(True)
        method_layout.addWidget(self.alarm_popup)

        self.alarm_email = QCheckBox("邮件报警")
        method_layout.addWidget(self.alarm_email)

        layout.addWidget(method_group)

        return widget

    def _create_about_tab(self):
        """创建关于选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 系统信息
        info_group = QGroupBox("系统信息")
        info_layout = QVBoxLayout(info_group)

        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setPlainText("""
铅浮选过程工况智能监测与控制系统

版本: 1.0.0
开发团队: 智能控制实验室
联系方式: contact@example.com

系统功能:
- 实时视频监控
- 浮选过程参数监测
- 智能控制算法
- 历史数据分析
- 报警管理

技术支持热线: 400-123-4567
        """)
        info_layout.addWidget(info_text)
        layout.addWidget(info_group)

        # 版权信息
        copyright_label = QLabel("© 2024 智能控制实验室 版权所有")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copyright_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(copyright_label)

        return widget

    def _load_default_config(self):
        """加载默认配置"""
        return {
            "theme": "浅色主题",
            "language": "中文",
            "refresh_rate": 10,
            "save_interval": 5,
            "history_days": 30,
            "opc_server": "opc.tcp://localhost:4840",
            "opc_timeout": 30,
            "api_endpoint": "http://localhost:8000/api",
            "level_high_alarm": 2.0,
            "level_low_alarm": 0.8,
            "grade_low_alarm": 80,
            "alarm_sound": True,
            "alarm_popup": True,
            "alarm_email": False
        }

    def _load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.current_config.update(loaded_config)
            except Exception as e:
                QMessageBox.warning(self, "配置加载错误", f"加载配置文件时出错: {e}")

        self._apply_config_to_ui()

    def _apply_config_to_ui(self):
        """将配置应用到UI"""
        # 基本设置
        self.theme_combo.setCurrentText(self.current_config["theme"])
        self.language_combo.setCurrentText(self.current_config["language"])
        self.refresh_spinbox.setValue(self.current_config["refresh_rate"])
        self.save_interval.setValue(self.current_config["save_interval"])
        self.history_days.setValue(self.current_config["history_days"])

        # 网络设置
        self.opc_server_url.setText(self.current_config["opc_server"])
        self.opc_timeout.setValue(self.current_config["opc_timeout"])
        self.api_endpoint.setText(self.current_config["api_endpoint"])

        # 报警设置
        self.level_high_alarm.setValue(self.current_config["level_high_alarm"])
        self.level_low_alarm.setValue(self.current_config["level_low_alarm"])
        self.grade_low_alarm.setValue(self.current_config["grade_low_alarm"])
        self.alarm_sound.setChecked(self.current_config["alarm_sound"])
        self.alarm_popup.setChecked(self.current_config["alarm_popup"])
        self.alarm_email.setChecked(self.current_config["alarm_email"])

    def _save_config(self):
        """保存配置"""
        try:
            # 从UI收集配置
            self._collect_config_from_ui()

            # 保存到文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_config, f, ensure_ascii=False, indent=2)

            QMessageBox.information(self, "保存成功", "系统配置已成功保存")

        except Exception as e:
            QMessageBox.critical(self, "保存错误", f"保存配置时出错: {e}")

    def _collect_config_from_ui(self):
        """从UI收集配置"""
        self.current_config.update({
            "theme": self.theme_combo.currentText(),
            "language": self.language_combo.currentText(),
            "refresh_rate": self.refresh_spinbox.value(),
            "save_interval": self.save_interval.value(),
            "history_days": self.history_days.value(),
            "opc_server": self.opc_server_url.text(),
            "opc_timeout": self.opc_timeout.value(),
            "api_endpoint": self.api_endpoint.text(),
            "level_high_alarm": self.level_high_alarm.value(),
            "level_low_alarm": self.level_low_alarm.value(),
            "grade_low_alarm": self.grade_low_alarm.value(),
            "alarm_sound": self.alarm_sound.isChecked(),
            "alarm_popup": self.alarm_popup.isChecked(),
            "alarm_email": self.alarm_email.isChecked()
        })

    def _reset_config(self):
        """恢复默认配置"""
        reply = QMessageBox.question(self, "确认恢复",
                                     "确定要恢复默认配置吗？当前配置将丢失。",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.current_config = self._load_default_config()
            self._apply_config_to_ui()
            QMessageBox.information(self, "恢复成功", "已恢复默认配置")

    def _export_config(self):
        """导出配置"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出配置", "system_config.json", "JSON文件 (*.json)"
        )

        if file_path:
            try:
                self._collect_config_from_ui()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.current_config, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "导出成功", f"配置已导出到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "导出错误", f"导出配置时出错: {e}")

    def _import_config(self):
        """导入配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入配置", "", "JSON文件 (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_config = json.load(f)
                    self.current_config.update(imported_config)
                    self._apply_config_to_ui()
                QMessageBox.information(self, "导入成功", "配置已成功导入")
            except Exception as e:
                QMessageBox.critical(self, "导入错误", f"导入配置时出错: {e}")
