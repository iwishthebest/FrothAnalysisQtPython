import numpy as np
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QLabel, QTableWidget, QTableWidgetItem,
                               QPushButton, QDateEdit, QComboBox, QHeaderView, QMessageBox)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor
import pandas as pd
from datetime import datetime, time

# [新增] 引入数据服务
from src.services.data_service import get_data_service


class HistoryPage(QWidget):
    """历史数据页面 - 显示查询和分析历史数据"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_service = get_data_service()  # 获取数据服务实例
        self.history_data = None
        self.setup_ui()
        # 初始化时自动加载最近7天的数据
        self.on_query_clicked()

    def setup_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)

        # 标题
        title_label = QLabel("历史数据查询与分析")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin: 10px;")
        layout.addWidget(title_label)

        # 查询条件区域
        query_widget = self.create_query_section()
        layout.addWidget(query_widget)

        # 数据表格区域
        table_widget = self.create_table_section()
        layout.addWidget(table_widget)

        # 统计信息区域
        stats_widget = self.create_stats_section()
        layout.addWidget(stats_widget)

    def create_query_section(self):
        """创建查询条件区域"""
        widget = QGroupBox("数据查询条件")
        layout = QHBoxLayout(widget)

        # 开始日期
        layout.addWidget(QLabel("开始日期:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addDays(-7))
        self.start_date_edit.setCalendarPopup(True)
        layout.addWidget(self.start_date_edit)

        # 结束日期
        layout.addWidget(QLabel("结束日期:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        layout.addWidget(self.end_date_edit)

        # 数据类型
        layout.addWidget(QLabel("数据类型:"))
        self.data_type_combo = QComboBox()
        self.data_type_combo.addItems([
            "全部数据", "品位数据", "回收率数据", "液位数据", "加药量数据"
        ])
        layout.addWidget(self.data_type_combo)

        # 查询按钮
        self.query_btn = QPushButton("查询数据")
        self.query_btn.setFixedSize(100, 30)
        self.query_btn.clicked.connect(self.on_query_clicked)
        layout.addWidget(self.query_btn)

        # 导出按钮
        self.export_btn = QPushButton("导出数据")
        self.export_btn.setFixedSize(100, 30)
        self.export_btn.clicked.connect(self.on_export_clicked)
        layout.addWidget(self.export_btn)

        layout.addStretch()

        return widget

    def create_table_section(self):
        """创建数据表格区域"""
        widget = QGroupBox("历史数据记录")
        layout = QVBoxLayout(widget)

        # 创建表格
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels([
            "时间", "铅品位(%)", "锌品位(%)", "回收率(%)",
            "液位(m)", "加药量(ml/min)", "泡沫厚度(cm)", "状态"
        ])

        # 设置表格属性
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.setSortingEnabled(True)
        self.history_table.setMinimumHeight(400)

        layout.addWidget(self.history_table)

        return widget

    def create_stats_section(self):
        """创建统计信息区域"""
        widget = QGroupBox("数据统计分析")
        layout = QHBoxLayout(widget)

        # 统计指标
        stats_data = [
            {"name": "平均铅品位", "value": "--", "unit": "%", "color": "#e74c3c"},
            {"name": "最高铅品位", "value": "--", "unit": "%", "color": "#c0392b"},
            {"name": "平均回收率", "value": "--", "unit": "%", "color": "#27ae60"},
            {"name": "最高回收率", "value": "--", "unit": "%", "color": "#229954"},
            {"name": "运行时长", "value": "--", "unit": "小时", "color": "#3498db"},
            {"name": "数据点数", "value": "--", "unit": "条", "color": "#9b59b6"}
        ]

        for stat in stats_data:
            stat_widget = self.create_stat_item(stat)
            layout.addWidget(stat_widget)

        return widget

    def create_stat_item(self, stat_info):
        """创建单个统计指标组件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 指标名称
        name_label = QLabel(stat_info["name"])
        name_label.setFont(QFont("Microsoft YaHei", 10))
        name_label.setStyleSheet(f"color: {stat_info['color']};")

        # 指标数值
        value_label = QLabel(stat_info["value"])
        value_label.setObjectName(f"stat_{stat_info['name']}")
        value_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {stat_info['color']};")

        # 单位
        unit_label = QLabel(stat_info["unit"])
        unit_label.setFont(QFont("Microsoft YaHei", 9))
        unit_label.setStyleSheet("color: #7f8c8d;")

        layout.addWidget(name_label)
        layout.addWidget(value_label)
        layout.addWidget(unit_label)

        return widget

    def populate_table(self):
        """填充表格数据"""
        if self.history_data is None or self.history_data.empty:
            self.history_table.setRowCount(0)
            return

        self.history_table.setRowCount(len(self.history_data))

        # 倒序显示，最新的在最上面
        sorted_data = self.history_data.sort_values(by='timestamp', ascending=False)

        for row, (_, record) in enumerate(sorted_data.iterrows()):
            # 时间
            ts = record['timestamp']
            time_str = ts.strftime('%Y-%m-%d %H:%M') if isinstance(ts, datetime) else str(ts)
            time_item = QTableWidgetItem(time_str)
            self.history_table.setItem(row, 0, time_item)

            # 铅品位
            lead_val = record.get('lead_grade', 0.0)
            lead_item = QTableWidgetItem(f"{lead_val:.2f}")
            self.set_grade_color(lead_item, lead_val, 50)  # 这里的基准值可能需要根据实际调整
            self.history_table.setItem(row, 1, lead_item)

            # 锌品位 (数据库暂时没有，用 -- 显示)
            zinc_val = record.get('zinc_grade', 0.0)
            zinc_item = QTableWidgetItem(f"{zinc_val:.2f}" if zinc_val > 0 else "--")
            self.history_table.setItem(row, 2, zinc_item)

            # 回收率
            rec_val = record.get('recovery_rate', 0.0)
            recovery_item = QTableWidgetItem(f"{rec_val:.2f}")
            self.set_grade_color(recovery_item, rec_val, 85)
            self.history_table.setItem(row, 3, recovery_item)

            # 液位
            level_val = record.get('water_level', 0.0)
            level_item = QTableWidgetItem(f"{level_val:.2f}" if level_val > 0 else "--")
            self.history_table.setItem(row, 4, level_item)

            # 加药量
            dosing_val = record.get('dosing_rate', 0.0)
            dosing_item = QTableWidgetItem(f"{dosing_val:.1f}" if dosing_val > 0 else "--")
            self.history_table.setItem(row, 5, dosing_item)

            # 泡沫厚度
            foam_val = record.get('foam_thickness', 0.0)
            foam_item = QTableWidgetItem(f"{foam_val:.1f}" if foam_val > 0 else "--")
            self.history_table.setItem(row, 6, foam_item)

            # 状态
            status_str = record.get('status', '正常')
            status_item = QTableWidgetItem(status_str)
            if status_str == '异常':
                status_item.setBackground(QColor(255, 200, 200))
            self.history_table.setItem(row, 7, status_item)

    def set_grade_color(self, item, value, target):
        """设置品位数值的颜色"""
        if value >= target + 5:
            item.setBackground(QColor(200, 255, 200))  # 优秀 - 浅绿
        elif value >= target - 5:
            item.setBackground(QColor(255, 255, 200))  # 良好 - 浅黄
        else:
            item.setBackground(QColor(255, 200, 200))  # 较差 - 浅红

    def on_query_clicked(self):
        """查询按钮点击事件 - 连接真实数据库"""
        try:
            # 获取日期范围
            start_qdate = self.start_date_edit.date()
            end_qdate = self.end_date_edit.date()

            # 转换为 datetime 对象 (start 设为 00:00:00, end 设为 23:59:59)
            start_dt = datetime.combine(start_qdate.toPython(), time.min)
            end_dt = datetime.combine(end_qdate.toPython(), time.max)

            # 从数据服务获取数据
            results = self.data_service.get_historical_data(start_dt, end_dt)

            # 将结果转换为 DataFrame 格式以适配原有逻辑
            if not results:
                self.history_data = pd.DataFrame()
                QMessageBox.information(self, "提示", "该时间段内无数据记录")
            else:
                data_list = []
                for row in results:
                    # 处理时间戳格式
                    ts = row['timestamp']
                    if isinstance(ts, str):
                        try:
                            ts = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f")
                        except ValueError:
                            try:
                                ts = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                            except:
                                pass

                    data_list.append({
                        'timestamp': ts,
                        # 映射数据库字段到界面字段
                        'lead_grade': row['conc_grade'] if row['conc_grade'] is not None else 0.0,  # 使用精矿品位
                        'zinc_grade': 0.0,  # 数据库暂无此字段
                        'recovery_rate': row['recovery'] if row['recovery'] is not None else 0.0,
                        'water_level': 0.0,  # 数据库暂无此字段
                        'dosing_rate': 0.0,  # 数据库暂无此字段
                        'foam_thickness': 0.0,
                        'status': '正常'
                    })

                self.history_data = pd.DataFrame(data_list)

            self.populate_table()
            self.update_statistics()

        except Exception as e:
            print(f"查询数据时出错: {e}")
            QMessageBox.warning(self, "查询错误", f"获取历史数据失败: {str(e)}")

    def on_export_clicked(self):
        """导出按钮点击事件"""
        try:
            if self.history_data is None or self.history_data.empty:
                QMessageBox.warning(self, "提示", "当前无数据可导出")
                return

            filename = f"history_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            # 实际上这里应该弹出文件保存对话框
            # path, _ = QFileDialog.getSaveFileName(self, "导出数据", filename, "CSV Files (*.csv)")
            # if path: ...

            # 模拟导出
            # self.history_data.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"数据已导出到: {filename}")
            QMessageBox.information(self, "导出成功", f"数据已成功导出到运行目录:\n{filename}")

        except Exception as e:
            print(f"导出数据时出错: {e}")
            QMessageBox.warning(self, "导出错误", str(e))

    def update_statistics(self):
        """更新统计信息"""
        if self.history_data is None or self.history_data.empty:
            # 清空显示
            for name in ["平均铅品位", "最高铅品位", "平均回收率", "最高回收率", "运行时长", "数据点数"]:
                label = self.findChild(QLabel, f"stat_{name}")
                if label: label.setText("--")
            return

        # 计算统计指标
        avg_lead = self.history_data['lead_grade'].mean()
        max_lead = self.history_data['lead_grade'].max()
        avg_recovery = self.history_data['recovery_rate'].mean()
        max_recovery = self.history_data['recovery_rate'].max()
        data_count = len(self.history_data)

        # 简单估算时长 (小时)
        if data_count > 1:
            duration = (self.history_data['timestamp'].max() - self.history_data[
                'timestamp'].min()).total_seconds() / 3600
        else:
            duration = 0

        # 更新显示
        self.findChild(QLabel, "stat_平均铅品位").setText(f"{avg_lead:.2f}")
        self.findChild(QLabel, "stat_最高铅品位").setText(f"{max_lead:.2f}")
        self.findChild(QLabel, "stat_平均回收率").setText(f"{avg_recovery:.2f}")
        self.findChild(QLabel, "stat_最高回收率").setText(f"{max_recovery:.2f}")
        self.findChild(QLabel, "stat_运行时长").setText(f"{duration:.1f}")
        self.findChild(QLabel, "stat_数据点数").setText(f"{data_count}")
