import numpy as np
import json
import pandas as pd
from datetime import datetime, time
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QLabel, QTableWidget, QTableWidgetItem,
                               QPushButton, QDateEdit, QComboBox, QHeaderView, QMessageBox)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor

from src.services.data_service import get_data_service


class HistoryPage(QWidget):
    """历史数据页面 - 显示查询和分析历史数据"""

    # 定义药剂列映射 (数据库列名 -> 显示名称)
    # 对应 DataService.reagent_mapping 中的键
    REAGENT_COLUMNS = [
        # --- 铅快粗工序 (Rougher) ---
        ('qkc_dinghuangyao1', '铅快粗\n丁黄药1'),
        ('qkc_dinghuangyao2', '铅快粗\n丁黄药2'),
        ('qkc_yiliudan1', '铅快粗\n乙硫氮1'),
        ('qkc_yiliudan2', '铅快粗\n乙硫氮2'),
        ('qkc_shihui', '铅快粗\n石灰'),
        ('qkc_5_you', '铅快粗\n2#油'),

        # --- 铅快精一工序 (Cleaner 1) ---
        ('qkj1_dinghuangyao', '铅快精一\n丁黄药'),
        ('qkj1_yiliudan', '铅快精一\n乙硫氮'),
        ('qkj1_shihui', '铅快精一\n石灰'),

        # --- 铅快精二工序 (Cleaner 2) ---
        ('qkj2_yiliudan', '铅快精二\n乙硫氮'),
        ('qkj2_shihui', '铅快精二\n石灰'),
        ('qkj2_dinghuangyao', '铅快精二\n丁黄药'),

        # --- 铅快精三工序 (Cleaner 3) ---
        ('qkj3_dinghuangyao', '铅快精三\n丁黄药'),
        ('qkj3_yiliudan', '铅快精三\n乙硫氮'),
        ('qkj3_ds1', '铅快精三\nDS1'),
        ('qkj3_ds2', '铅快精三\nDS2'),
        ('qkj3_shihui', '铅快精三\n石灰'),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_service = get_data_service()
        self.history_data = None
        self.setup_ui()
        # 初始化时自动加载数据
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

        # 各功能区域
        layout.addWidget(self.create_query_section())
        layout.addWidget(self.create_table_section())
        layout.addWidget(self.create_stats_section())

    def create_query_section(self):
        """创建查询条件区域"""
        widget = QGroupBox("数据查询条件")
        layout = QHBoxLayout(widget)

        layout.addWidget(QLabel("开始日期:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addDays(-7))
        self.start_date_edit.setCalendarPopup(True)
        layout.addWidget(self.start_date_edit)

        layout.addWidget(QLabel("结束日期:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        layout.addWidget(self.end_date_edit)

        layout.addWidget(QLabel("数据类型:"))
        self.data_type_combo = QComboBox()
        self.data_type_combo.addItems(["全部数据", "品位数据", "回收率数据", "药剂流量数据"])
        layout.addWidget(self.data_type_combo)

        self.query_btn = QPushButton("查询数据")
        self.query_btn.setFixedSize(100, 30)
        self.query_btn.clicked.connect(self.on_query_clicked)
        layout.addWidget(self.query_btn)

        self.export_btn = QPushButton("导出数据")
        self.export_btn.setFixedSize(100, 30)
        self.export_btn.clicked.connect(self.on_export_clicked)
        layout.addWidget(self.export_btn)

        layout.addStretch()
        return widget

    def create_table_section(self):
        """创建数据表格区域 (动态列)"""
        widget = QGroupBox("历史数据记录")
        layout = QVBoxLayout(widget)

        self.history_table = QTableWidget()

        # 固定列 + 药剂列
        # 固定列: 时间, 铅品位, 锌品位, 回收率
        fixed_headers = ["时间", "原矿品位\n(%)", "高铅精矿品位\n(%)", "铅回收率\n(%)"]
        reagent_headers = [name for _, name in self.REAGENT_COLUMNS]
        # 结尾列: 状态
        end_headers = ["状态"]

        all_headers = fixed_headers + reagent_headers + end_headers

        self.history_table.setColumnCount(len(all_headers))
        self.history_table.setHorizontalHeaderLabels(all_headers)

        # 设置样式和属性
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.verticalHeader().setVisible(False)

        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setMinimumSectionSize(80)  # 保证列宽不至于太窄

        self.history_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.history_table.setMinimumHeight(400)

        layout.addWidget(self.history_table)
        return widget

    def create_stats_section(self):
        """创建统计信息区域"""
        widget = QGroupBox("数据统计分析")
        layout = QHBoxLayout(widget)

        stats_data = [
            {"name": "平均铅品位", "value": "--", "unit": "%", "color": "#e74c3c"},
            {"name": "最高铅品位", "value": "--", "unit": "%", "color": "#c0392b"},
            {"name": "平均回收率", "value": "--", "unit": "%", "color": "#27ae60"},
            {"name": "运行时长", "value": "--", "unit": "小时", "color": "#3498db"},
            {"name": "数据点数", "value": "--", "unit": "条", "color": "#9b59b6"}
        ]

        for stat in stats_data:
            stat_widget = self.create_stat_item(stat)
            layout.addWidget(stat_widget)

        return widget

    def create_stat_item(self, stat_info):
        """创建单个统计项"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_label = QLabel(stat_info["name"])
        name_label.setFont(QFont("Microsoft YaHei", 10))

        value_label = QLabel(stat_info["value"])
        value_label.setObjectName(f"stat_{stat_info['name']}")  # 方便查找更新
        value_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {stat_info['color']};")

        unit_label = QLabel(stat_info["unit"])
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
        sorted_data = self.history_data.sort_values(by='timestamp', ascending=False)

        for row, (_, record) in enumerate(sorted_data.iterrows()):
            # 1. 时间
            ts = record['timestamp']
            time_str = ts.strftime("%Y-%m-%d %H:%M:%S") if isinstance(ts, datetime) else str(ts)
            self.history_table.setItem(row, 0, QTableWidgetItem(time_str))

            # 2. 核心指标
            # 入矿品位
            feed_grade_val = record.get('feed_grade', 0.0)
            feed_grade_item = QTableWidgetItem(f"{feed_grade_val:.2f}" if feed_grade_val is not None else "--")
            self.set_grade_color(feed_grade_item, feed_grade_val, 3.5, high=0.5, low=0.5)  # 假设50是基准
            self.history_table.setItem(row, 1, feed_grade_item)

            # 高铅精矿品位
            conc_grade_val = record.get('conc_grade', 0.0)
            conc_grade_item = QTableWidgetItem(f"{conc_grade_val:.2f}" if conc_grade_val is not None else "--")
            self.set_grade_color(conc_grade_item, conc_grade_val, 50, high=5, low=2)  # 假设50是基准
            self.history_table.setItem(row, 2, conc_grade_item)

            # 铅回收率
            rec_val = record.get('recovery_rate', 0.0)
            rec_item = QTableWidgetItem(f"{rec_val:.2f}" if rec_val is not None else "--")
            self.set_grade_color(rec_item, rec_val, 80, high=5, low=2)  # 假设85是基准
            self.history_table.setItem(row, 3, rec_item)

            # 3. 动态药剂列 (从第4列开始)
            col_idx = 4
            for db_key, _ in self.REAGENT_COLUMNS:
                val = record.get(db_key)  # 直接使用数据库列名获取数据
                text = f"{val:.1f}" if val is not None and val != 0 else "--"
                item = QTableWidgetItem(text)
                if val is not None and val > 0:
                    item.setBackground(QColor(240, 248, 255))  # 有流量显示淡蓝色背景
                self.history_table.setItem(row, col_idx, item)
                col_idx += 1

            # 4. 状态 (最后一列)
            status_str = "正常"
            self.history_table.setItem(row, col_idx, QTableWidgetItem(status_str))

    def set_grade_color(self, item, value, target, high=2.0, low=5.0):
        """设置品位颜色"""
        if value is None:
            return
        if value >= target + high:
            item.setBackground(QColor(200, 255, 200))  # 优
        elif value < target - low:
            item.setBackground(QColor(255, 220, 220))  # 差

    def on_query_clicked(self):
        """查询数据并解析"""
        try:
            start_qdate = self.start_date_edit.date()
            end_qdate = self.end_date_edit.date()
            start_dt = datetime.combine(start_qdate.toPython(), time.min)
            end_dt = datetime.combine(end_qdate.toPython(), time.max)

            # 获取数据库数据 (get_historical_data 已包含所有列)
            db_results = self.data_service.get_historical_data(start_dt, end_dt)

            if not db_results:
                self.history_data = pd.DataFrame()
                if self.sender() == self.query_btn:  # 只有手动点击按钮才提示
                    QMessageBox.information(self, "提示", "该时间段内无数据记录")
            else:
                parsed_rows = []
                for row in db_results:
                    # row 是 sqlite3.Row 对象 (类似字典)

                    # 1. 基础信息解析
                    ts_str = row['timestamp']
                    try:
                        if isinstance(ts_str, str):
                            # 处理可能包含的毫秒
                            if '.' in ts_str:
                                ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S.%f")
                            else:
                                ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                        else:
                            ts = ts_str
                    except:
                        ts = datetime.now()

                    item = {
                        'timestamp': ts,
                        'feed_grade': row['feed_grade'],
                        'conc_grade': row['conc_grade'],
                        'recovery_rate': row['recovery']
                    }

                    # 2. 药剂数据解析 (直接读取数据库列)
                    for db_key, _ in self.REAGENT_COLUMNS:
                        # 尝试从 row 中获取列数据
                        # DataService 保证了这些列存在 (通过动态 ALTER TABLE)
                        try:
                            val = row[db_key]
                            item[db_key] = val if val is not None else 0.0
                        except (IndexError, KeyError):
                            # 如果列不存在 (可能是旧数据库文件未迁移完全)，则置0
                            item[db_key] = 0.0

                    parsed_rows.append(item)

                self.history_data = pd.DataFrame(parsed_rows)

            self.populate_table()
            self.update_statistics()

        except Exception as e:
            print(f"查询出错: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "错误", f"查询失败: {str(e)}")

    def update_statistics(self):
        """更新统计面板"""
        if self.history_data is None or self.history_data.empty:
            return

        # 示例统计
        avg_lead = self.history_data['conc_grade'].mean()
        max_lead = self.history_data['conc_grade'].max()
        avg_rec = self.history_data['recovery_rate'].mean()
        count = len(self.history_data)

        # 查找并更新Label
        label = self.findChild(QLabel, "stat_平均铅品位")
        if label: label.setText(f"{avg_lead:.2f}")

        label = self.findChild(QLabel, "stat_最高铅品位")
        if label: label.setText(f"{max_lead:.2f}")

        label = self.findChild(QLabel, "stat_平均回收率")
        if label: label.setText(f"{avg_rec:.2f}")

        label = self.findChild(QLabel, "stat_数据点数")
        if label: label.setText(str(count))

    def on_export_clicked(self):
        """导出数据"""
        if self.history_data is None or self.history_data.empty:
            QMessageBox.warning(self, "提示", "无数据可导出")
            return

        try:
            filename = f"history_export_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
            # 重命名列以便导出更友好的CSV
            export_df = self.history_data.copy()
            rename_map = {db_key: name.replace('\n', '') for db_key, name in self.REAGENT_COLUMNS}
            rename_map.update({
                'timestamp': '时间',
                'feed_grade': '原矿品位',
                'conc_grade': '精矿品位',
                'recovery_rate': '回收率'
            })
            export_df.rename(columns=rename_map, inplace=True)

            export_df.to_csv(filename, index=False, encoding='utf-8-sig')
            QMessageBox.information(self, "成功", f"数据已导出至 {filename}")
        except Exception as e:
            QMessageBox.warning(self, "导出失败", str(e))
