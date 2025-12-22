"""
src/services/data_service.py
"""
import time
import sqlite3
import csv
import os
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from threading import Lock
from pathlib import Path
from config.config_system import config_manager

# 保持原有的兼容性导入
try:
    from . import BaseService, ServiceError, ServiceStatus
except ImportError:
    from PySide6.QtCore import QObject
    class BaseService(QObject):
        def __init__(self, name): super().__init__()
    class ServiceStatus:
        STARTING = "STARTING"; RUNNING = "RUNNING"; STOPPING = "STOPPING"; STOPPED = "STOPPED"; ERROR = "ERROR"
    class ServiceError(Exception): pass


class DataService(BaseService):
    def __init__(self, db_path: str = "data/system.db", csv_dir: str = "data/csv",
                 tag_list_file: str = "resources/tags/tagList.csv"):
        super().__init__("data_service")
        self.db_path = db_path
        self.csv_dir = Path(csv_dir)
        self.tag_list_file = tag_list_file

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.csv_dir.mkdir(parents=True, exist_ok=True)

        self._cache: Dict[str, Any] = {}
        self._cache_lock = Lock()

        # [核心] 定义数据库列名与OPC标签的映射关系
        # 键为数据库列名(简化)，值为OPC完整标签名
        # 依据 src/views/pages/history_page.py 和 image_14ceb0.png
        self.reagent_mapping = {
            # --- 铅快粗工序 (Rougher) ---
            'qkc_dinghuangyao1': 'YJ.yj_qkc_dinghuangyao1:actualflow',
            'qkc_dinghuangyao2': 'YJ.yj_qkc_dinghuangyao2:actualflow',
            'qkc_yiliudan1':     'YJ.yj_qkc_yiliudan1:actualflow',
            'qkc_yiliudan2':     'YJ.yj_qkc_yiliudan2:actualflow',
            'qkc_shihui':        'YJ.yj_qkc_shihui:actualflow',
            'qkc_5_you':         'YJ.yj_qkc_5#you:actualflow',

            # --- 铅快精一工序 (Cleaner 1) ---
            'qkj1_dinghuangyao': 'YJ.yj_qkj1_dinghuangyao:actualflow',
            'qkj1_yiliudan':     'YJ.yj_qkj1_yiliudan:actualflow',
            'qkj1_shihui':       'YJ.yj_qkj1_shihui:actualflow',

            # --- 铅快精二工序 (Cleaner 2) ---
            'qkj2_yiliudan':     'YJ.yj_qkj2_yiliudan:actualflow',
            'qkj2_shihui':       'YJ.yj_qkj2_shihui:actualflow',
            'qkj2_dinghuangyao': 'YJ.yj_qkj2_dinghuangyao:actualflow',

            # --- 铅快精三工序 (Cleaner 3) ---
            'qkj3_dinghuangyao': 'YJ.yj_qkj3_dinghuangyao:actualflow',
            'qkj3_yiliudan':     'YJ.yj_qkj3_yiliudan:actualflow',
            'qkj3_ds1':          'YJ.yj_qkj3_ds1:actualflow',
            'qkj3_ds2':          'YJ.yj_qkj3_ds2:actualflow',
            'qkj3_shihui':       'YJ.yj_qkj3_shihui:actualflow'
        }

        self.all_csv_headers = self._load_all_headers()
        self.last_periodic_save_time = datetime.min
        self.yj_value_cache = {}

    def start(self) -> bool:
        try:
            self.status = ServiceStatus.STARTING
            self._init_database()
            self.status = ServiceStatus.RUNNING
            return True
        except Exception as e:
            self.status = ServiceStatus.ERROR
            raise ServiceError(f"数据服务启动失败: {e}")

    def stop(self) -> bool:
        self.status = ServiceStatus.STOPPED
        return True

    def restart(self) -> bool:
        self.stop()
        return self.start()

    def _load_all_headers(self) -> List[str]:
        """从CSV加载所有标签名"""
        headers = []
        try:
            with open(self.tag_list_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if not row: continue
                    raw = row[0]
                    if "source:" in raw: raw = raw.split(']')[-1]
                    cleaned = re.sub(r'[\[\]]', '', raw).strip()

                    if cleaned.startswith('yj_'):
                        tag = f'YJ.{cleaned}'
                    elif cleaned.startswith('kyfx_'):
                        tag = f'KYFX.{cleaned}'
                    else:
                        tag = cleaned
                    headers.append(tag)
        except Exception as e:
            print(f"加载标签列表失败: {e}")
        return headers

    def _init_database(self) -> None:
        """初始化数据库结构 - 混合存储 (列存储 + JSON)"""
        # 构建动态列定义 SQL
        reagent_columns_sql = ""
        for col_name in self.reagent_mapping.keys():
            reagent_columns_sql += f",\n                             {col_name} REAL"

        # 注意：此处保留了 raw_data JSON 字段
        create_table_sql = f'''
                         CREATE TABLE IF NOT EXISTS process_history
                         (
                             id INTEGER PRIMARY KEY AUTOINCREMENT,
                             timestamp DATETIME NOT NULL,
                             feed_grade REAL,
                             conc_grade REAL,
                             recovery REAL{reagent_columns_sql},
                             raw_data JSON
                         )
                         '''
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(create_table_sql)
            conn.commit()

    def record_data(self, data: Dict[str, Any]) -> None:
        try:
            timestamp = datetime.now()
            should_save = False

            with self._cache_lock:
                self._cache.update(data)
                self._cache['last_updated'] = timestamp

            slow_interval = config_manager.get_network_config().slow_tag_interval

            # 策略1: 定时强制保存
            if (timestamp - self.last_periodic_save_time).total_seconds() >= slow_interval:
                should_save = True
                self.last_periodic_save_time = timestamp

            # 策略2: 药剂值 (YJ) 发生变化
            yj_changed = False
            for key, val_dict in data.items():
                if key.startswith("YJ."):
                    val = val_dict.get('value')
                    if self.yj_value_cache.get(key) != val:
                        self.yj_value_cache[key] = val
                        yj_changed = True

            if yj_changed:
                should_save = True

            if should_save:
                flat_data = {}
                for key, val in data.items():
                    if isinstance(val, dict) and 'value' in val:
                        v = val['value']
                        flat_data[key] = float(v) if v is not None else None
                    else:
                        flat_data[key] = val

                self._save_to_sqlite(timestamp, flat_data)
                self._save_to_csv(timestamp, flat_data)

        except Exception as e:
            print(f"数据保存失败: {e}")

    def _save_to_sqlite(self, timestamp, flat_data: Dict[str, Any]):
        """存入数据库 (同时保存展平列和原始 JSON)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            def get_clean(key):
                val = flat_data.get(key)
                if val == -9999.0 or val is None:
                    return None
                return val

            # 1. 核心指标
            f = get_clean("KYFX.kyfx_yk_grade_Pb")
            c = get_clean("KYFX.kyfx_gqxk_grade_Pb")
            c_total = get_clean("KYFX.kyfx_zqxk_grade_Pb")
            t = get_clean("KYFX.kyfx_qw_grade_Pb")

            rec = None
            try:
                if f is not None and c_total is not None and t is not None:
                    if f > 0 and (c_total - t) != 0:
                        rec = (c_total * (f - t)) / (f * (c_total - t)) * 100
            except:
                pass

            # 2. 准备 SQL 语句和参数
            columns = ['timestamp', 'feed_grade', 'conc_grade', 'recovery']
            values = [timestamp, f, c, rec]
            placeholders = ['?', '?', '?', '?']

            # 3. 动态添加药剂列
            for col_name, tag_name in self.reagent_mapping.items():
                columns.append(col_name)
                values.append(get_clean(tag_name))
                placeholders.append('?')

            # 4. 添加 raw_data JSON
            columns.append('raw_data')
            values.append(json.dumps(flat_data))
            placeholders.append('?')

            # 5. 执行插入
            sql = f'''
                INSERT INTO process_history ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
            '''

            cursor.execute(sql, values)
            conn.commit()

    def _save_to_csv(self, timestamp, flat_data: Dict[str, Any]):
        """存入 CSV (保持不变，CSV结构通常包含所有原始标签更灵活)"""
        filename = f"{timestamp.strftime('%Y%m%d')}_process_data.csv"
        filepath = self.csv_dir / filename
        file_exists = filepath.exists()

        with open(filepath, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            headers = ["Timestamp"] + (self.all_csv_headers if self.all_csv_headers else list(flat_data.keys()))
            if not file_exists:
                writer.writerow(headers)

            row = [timestamp.strftime("%Y-%m-%d %H:%M:%S")]
            for key in headers[1:]:
                val = flat_data.get(key)
                if val == -9999.0 or val is None:
                    row.append("")
                else:
                    row.append(val)
            writer.writerow(row)

    def get_current_data(self, key: Optional[str] = None) -> Any:
        with self._cache_lock:
            if key: return self._cache.get(key)
            return self._cache.copy()

    def get_historical_data(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """查询历史数据 (返回字典列表)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 动态构建查询列，包含 raw_data
            reagent_cols = ", ".join(self.reagent_mapping.keys())

            # 构建查询 SQL，包含核心指标、所有药剂列和 raw_data
            sql = f'''
               SELECT timestamp, feed_grade, conc_grade, recovery, {reagent_cols}, raw_data
               FROM process_history
               WHERE timestamp BETWEEN ? AND ?
               ORDER BY timestamp
            '''

            cursor.execute(sql, (start_time, end_time))
            return [dict(row) for row in cursor.fetchall()]

_data_service_instance = None

def get_data_service() -> DataService:
    global _data_service_instance
    if _data_service_instance is None:
        _data_service_instance = DataService()
    return _data_service_instance