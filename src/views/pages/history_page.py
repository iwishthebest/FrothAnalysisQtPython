import numpy as np
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QLabel, QTableWidget, QTableWidgetItem, 
                               QPushButton, QDateEdit, QComboBox, QHeaderView)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor
import pandas as pd
from datetime import datetime, timedelta


class HistoryPage(QWidget):
    """历史数据页面 - 显示查询和分析历史数据"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history_data = None
        self.setup_ui()
        self.load_sample_data()  # 加载示例数据
        
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
        
    def load_sample_data(self):
        """加载示例数据"""
        # 生成示例数据
        dates = pd.date_range(start='2024-01-01', end='2024-01-07', freq='h')
        sample_data = []
        
        for date in dates:
            record = {
                'timestamp': date,
                'lead_grade': round(np.random.normal(85, 3), 2),
                'zinc_grade': round(np.random.normal(5, 1), 2),
                'recovery_rate': round(np.random.normal(92, 2), 2),
                'water_level': round(np.random.uniform(1.1, 1.3), 2),
                'dosing_rate': round(np.random.uniform(45, 55), 1),
                'foam_thickness': round(np.random.uniform(20, 30), 1),
                'status': '正常' if np.random.random() > 0.05 else '异常'
            }
            sample_data.append(record)
            
        self.history_data = pd.DataFrame(sample_data)
        self.populate_table()
        
    def populate_table(self):
        """填充表格数据"""
        if self.history_data is None:
            return
            
        self.history_table.setRowCount(len(self.history_data))
        
        for row, (_, record) in enumerate(self.history_data.iterrows()):
            # 时间
            time_item = QTableWidgetItem(record['timestamp'].strftime('%Y-%m-%d %H:%M'))
            self.history_table.setItem(row, 0, time_item)
            
            # 铅品位
            lead_item = QTableWidgetItem(f"{record['lead_grade']:.2f}")
            self.set_grade_color(lead_item, record['lead_grade'], 85)
            self.history_table.setItem(row, 1, lead_item)
            
            # 锌品位
            zinc_item = QTableWidgetItem(f"{record['zinc_grade']:.2f}")
            self.history_table.setItem(row, 2, zinc_item)
            
            # 回收率
            recovery_item = QTableWidgetItem(f"{record['recovery_rate']:.2f}")
            self.set_grade_color(recovery_item, record['recovery_rate'], 92)
            self.history_table.setItem(row, 3, recovery_item)
            
            # 液位
            level_item = QTableWidgetItem(f"{record['water_level']:.2f}")
            self.history_table.setItem(row, 4, level_item)
            
            # 加药量
            dosing_item = QTableWidgetItem(f"{record['dosing_rate']:.1f}")
            self.history_table.setItem(row, 5, dosing_item)
            
            # 泡沫厚度
            foam_item = QTableWidgetItem(f"{record['foam_thickness']:.1f}")
            self.history_table.setItem(row, 6, foam_item)
            
            # 状态
            status_item = QTableWidgetItem(record['status'])
            if record['status'] == '异常':
                status_item.setBackground(QColor(255, 200, 200))
            self.history_table.setItem(row, 7, status_item)
            
    def set_grade_color(self, item, value, target):
        """设置品位数值的颜色"""
        if value >= target + 2:
            item.setBackground(QColor(200, 255, 200))  # 优秀 - 浅绿
        elif value >= target - 2:
            item.setBackground(QColor(255, 255, 200))  # 良好 - 浅黄
        else:
            item.setBackground(QColor(255, 200, 200))  # 较差 - 浅红
            
    def on_query_clicked(self):
        """查询按钮点击事件"""
        try:
            start_date = self.start_date_edit.date().toString('yyyy-MM-dd')
            end_date = self.end_date_edit.date().toString('yyyy-MM-dd')
            data_type = self.data_type_combo.currentText()
            
            # 这里应该是实际的数据查询逻辑
            # 暂时使用示例数据过滤
            
            filtered_data = self.history_data.copy()
            self.populate_table()
            
            # 更新统计信息
            self.update_statistics()
            
        except Exception as e:
            print(f"查询数据时出错: {e}")
            
    def on_export_clicked(self):
        """导出按钮点击事件"""
        try:
            # 这里应该是实际的数据导出逻辑
            filename = f"history_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            # 模拟导出成功
            print(f"数据已导出到: {filename}")
            
        except Exception as e:
            print(f"导出数据时出错: {e}")
            
    def update_statistics(self):
        """更新统计信息"""
        if self.history_data is None:
            return
            
        # 计算统计指标
        avg_lead = self.history_data['lead_grade'].mean()
        max_lead = self.history_data['lead_grade'].max()
        avg_recovery = self.history_data['recovery_rate'].mean()
        max_recovery = self.history_data['recovery_rate'].max()
        data_count = len(self.history_data)
        
        # 更新显示
        self.findChild(QLabel, "stat_平均铅品位").setText(f"{avg_lead:.2f}")
        self.findChild(QLabel, "stat_最高铅品位").setText(f"{max_lead:.2f}")
        self.findChild(QLabel, "stat_平均回收率").setText(f"{avg_recovery:.2f}")
        self.findChild(QLabel, "stat_最高回收率").setText(f"{max_recovery:.2f}")