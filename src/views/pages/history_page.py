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
    REAGENT_COLUMNS = [
        # --- 铅快粗工序 ---
        ('qkc_dinghuangyao1', '铅快粗\n丁黄药1'),
        ('qkc_dinghuangyao2', '铅快粗\n丁黄药2'),
        ('qkc_yiliudan1', '铅快粗\n乙硫氮1'),
        ('qkc_yiliudan2', '铅快粗\n乙硫氮2'),
        ('qkc_shihui', '铅快粗\n石灰'),
        ('qkc_5_you', '铅快粗\n2#油'),

        # --- 铅快精一工序 ---
        ('qkj1_dinghuangyao', '铅快精一\n丁黄药'),
        ('qkj1_yiliudan', '铅快精一\n乙硫氮'),
        ('qkj1_shihui', '铅快精一\n石灰'),

        # --- 铅快精二工序 ---
        ('qkj2_yiliudan', '铅快精二\n乙硫氮'),
        ('qkj2_shihui', '铅快精二\n石灰'),
        ('qkj2_dinghuangyao', '铅快精二\n丁黄药'),

        # --- 铅快精三工序 ---
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
        # 延迟加载，确保界面渲染完成
        # self.on_query_clicked()

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
        self.start_date_edit.setDate(QDate.currentDate().addDays(-1))  # 默认查前一天
        self.start_date_edit.setCalendarPopup(True)
        layout.addWidget(self.start_date_edit)

        layout.addWidget(QLabel("结束日期:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        layout.addWidget(self.end_date_edit)

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

        # 固定列 + 药剂列 + 状态列
        fixed_headers = ["时间", "原矿品位\n(%)", "高铅精矿品位\n(%)", "铅回收率\n(%)"]
        reagent_headers = [name for _, name in self.REAGENT_COLUMNS]
        all_headers = fixed_headers + reagent_headers + ["状态"]

        self.history_table.setColumnCount(len(all_headers))
        self.history_table.setHorizontalHeaderLabels(all_headers)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.horizontalHeader().setMinimumSectionSize(80)

        layout.addWidget(self.history_table)
        return widget

    def create_stats_section(self):
        """创建统计信息区域"""
        widget = QGroupBox("数据统计分析")
        layout = QHBoxLayout(widget)

        # 预留统计标签
        self.stat_labels = {}
        stats_config = [
            ("avg_lead", "平均精矿品位", "#c0392b"),
            ("avg_rec", "平均回收率", "#27ae60"),
            ("count", "数据点数", "#3498db")
        ]

        for key, name, color in stats_config:
            container = QWidget()
            v_layout = QVBoxLayout(container)
            v_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            lbl_name = QLabel(name)
            lbl_val = QLabel("--")
            lbl_val.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
            lbl_val.setStyleSheet(f"color: {color};")

            v_layout.addWidget(lbl_name)
            v_layout.addWidget(lbl_val)

            layout.addWidget(container)
            self.stat_labels[key] = lbl_val

        return widget

    def on_query_clicked(self):
        """查询数据"""
        try:
            start_qdate = self.start_date_edit.date()
            end_qdate = self.end_date_edit.date()
            start_dt = datetime.combine(start_qdate.toPython(), time.min)
            end_dt = datetime.combine(end_qdate.toPython(), time.max)

            # 调用 DataService
            if not hasattr(self.data_service, 'get_historical_data'):
                QMessageBox.critical(self, "错误", "DataService 未更新，请重启程序或检查代码")
                return

            db_results = self.data_service.get_historical_data(start_dt, end_dt)

            if not db_results:
                self.history_data = pd.DataFrame()
                self.history_table.setRowCount(0)
                QMessageBox.information(self, "提示", "该时间段内无数据记录")
                return

            # 解析数据
            parsed_rows = []
            for row in db_results:
                # 1. 时间处理
                ts = row['timestamp']
                try:
                    if isinstance(ts, str):
                        ts = datetime.fromisoformat(ts) if 'T' in ts else datetime.strptime(ts.split('.')[0],
                                                                                            "%Y-%m-%d %H:%M:%S")
                except:
                    pass

                item = {
                    'timestamp': ts,
                    'feed_grade': row.get('feed_grade', 0.0),
                    'conc_grade': row.get('conc_grade', 0.0),
                    'recovery_rate': row.get('recovery', 0.0)
                }

                # 2. 药剂列处理 (容错)
                for db_key, _ in self.REAGENT_COLUMNS:
                    item[db_key] = row[db_key] if db_key in row and row[db_key] is not None else 0.0

                parsed_rows.append(item)

            self.history_data = pd.DataFrame(parsed_rows)
            self.populate_table()
            self.update_statistics()

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "查询错误", f"详细错误: {str(e)}")

    def populate_table(self):
        """填充表格"""
        if self.history_data is None: return
        self.history_table.setRowCount(len(self.history_data))

        # 倒序显示 (最新在前)
        # sorted_df = self.history_data.sort_values('timestamp', ascending=False)

        for i, row in self.history_data.iterrows():
            # 时间
            ts = row['timestamp']
            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S") if isinstance(ts, datetime) else str(ts)
            self.history_table.setItem(i, 0, QTableWidgetItem(ts_str))

            # 核心指标
            self.history_table.setItem(i, 1, QTableWidgetItem(f"{row['feed_grade']:.2f}"))
            self.history_table.setItem(i, 2, QTableWidgetItem(f"{row['conc_grade']:.2f}"))
            self.history_table.setItem(i, 3, QTableWidgetItem(f"{row['recovery_rate']:.2f}"))

            # 药剂列
            col_idx = 4
            for db_key, _ in self.REAGENT_COLUMNS:
                val = row[db_key]
                item = QTableWidgetItem(f"{val:.1f}" if val > 0 else "--")
                if val > 0:
                    item.setBackground(QColor(235, 245, 255))
                self.history_table.setItem(i, col_idx, item)
                col_idx += 1

            self.history_table.setItem(i, col_idx, QTableWidgetItem("正常"))

    def update_statistics(self):
        if self.history_data is None or self.history_data.empty: return

        mean_conc = self.history_data['conc_grade'].mean()
        mean_rec = self.history_data['recovery_rate'].mean()
        count = len(self.history_data)

        self.stat_labels['avg_lead'].setText(f"{mean_conc:.2f}%")
        self.stat_labels['avg_rec'].setText(f"{mean_rec:.2f}%")
        self.stat_labels['count'].setText(str(count))

    def on_export_clicked(self):
        if self.history_data is not None and not self.history_data.empty:
            path = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            self.history_data.to_csv(path, index=False, encoding='utf-8-sig')
            QMessageBox.information(self, "导出成功", f"文件已保存至: {path}")