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

try:
    from . import BaseService, ServiceError, ServiceStatus
except ImportError:
    from PySide6.QtCore import QObject
    class BaseService(QObject):
        def __init__(self, name): super().__init__()
    class ServiceStatus:
        STARTING="STARTING"; RUNNING="RUNNING"; STOPPING="STOPPING"; STOPPED="STOPPED"; ERROR="ERROR"
    class ServiceError(Exception): pass

class DataService(BaseService):
    def __init__(self, db_path: str = "data/system.db", csv_dir: str = "data/csv", tag_list_file: str = "resources/tags/tagList.csv"):
        super().__init__("data_service")
        self.db_path = db_path
        self.csv_dir = Path(csv_dir)
        self.tag_list_file = tag_list_file

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.csv_dir.mkdir(parents=True, exist_ok=True)

        self._cache: Dict[str, Any] = {}
        self._cache_lock = Lock()

        # [核心] 加载所有标签作为 CSV 表头
        self.all_csv_headers = self._load_all_headers()

        # 状态记录
        # [修改] 使用独立的周期性保存计时器，避免被快频保存重置
        self.last_periodic_save_time = datetime.min
        self.yj_value_cache = {} # 用于比对药剂值是否变化

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

                    if cleaned.startswith('yj_'): tag = f'YJ.{cleaned}'
                    elif cleaned.startswith('kyfx_'): tag = f'KYFX.{cleaned}'
                    else: tag = cleaned
                    headers.append(tag)
        except Exception as e:
            print(f"加载标签列表失败: {e}")
        return headers

    def _init_database(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS process_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    feed_grade REAL,
                    conc_grade REAL,
                    recovery REAL,
                    raw_data JSON
                )
            ''')
            conn.commit()

    def record_data(self, data: Dict[str, Any]) -> None:
        """
        接收并保存数据
        策略：
        1. YJ (快频) 标签：数值变化即保存 (基于缓存比对)
        2. KYFX (慢频) 标签 / 定时：每10分钟强制保存一次 (不管值是否变)
        """
        try:
            timestamp = datetime.now()
            should_save = False

            with self._cache_lock:
                self._cache.update(data)
                self._cache['last_updated'] = timestamp

            # 策略1: 10分钟定时强制保存 (主要针对 KYFX)
            # [修改] 使用独立的 last_periodic_save_time，不受快频保存影响
            if (timestamp - self.last_periodic_save_time).total_seconds() >= 600:
                should_save = True
                self.last_periodic_save_time = timestamp
                # print("触发定时保存 (慢频/周期)")

            # 策略2: 药剂值 (YJ) 发生变化
            # 无论是否触发定时保存，都要更新 yj_value_cache 以保持最新状态
            yj_changed = False
            for key, val_dict in data.items():
                if key.startswith("YJ."):
                    val = val_dict.get('value')
                    # 如果值变了 (与上次缓存的值不同)
                    if self.yj_value_cache.get(key) != val:
                        self.yj_value_cache[key] = val
                        yj_changed = True

            if yj_changed:
                should_save = True
                # print(f"触发变动保存 (快频)")

            if should_save:
                # 提取扁平数据
                flat_data = {}
                for key, val in data.items():
                    if isinstance(val, dict) and 'value' in val:
                        flat_data[key] = float(val['value'])
                    else:
                        flat_data[key] = val

                self._save_to_sqlite(timestamp, flat_data)
                self._save_to_csv(timestamp, flat_data)

        except Exception as e:
            print(f"数据保存失败: {e}")

    def _save_to_sqlite(self, timestamp, flat_data: Dict[str, Any]):
        """存入数据库 (仅存 KPI 用于查询)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            f = flat_data.get("KYFX.kyfx_yk_grade_Pb", 0.0)
            c = flat_data.get("KYFX.kyfx_gqxk_grade_Pb", 0.0) # 高铅
            c_total = flat_data.get("KYFX.kyfx_zqxk_grade_Pb", 0.0) # 总铅
            t = flat_data.get("KYFX.kyfx_qw_grade_Pb", 0.0)

            rec = 0.0
            try:
                if f > 0 and (c_total - t) != 0:
                    rec = (c_total * (f - t)) / (f * (c_total - t)) * 100
            except: pass

            json_dump = json.dumps(flat_data)
            cursor.execute('''
                INSERT INTO process_history (timestamp, feed_grade, conc_grade, recovery, raw_data)
                VALUES (?, ?, ?, ?, ?)
            ''', (timestamp, f, c, rec, json_dump))
            conn.commit()

    def _save_to_csv(self, timestamp, flat_data: Dict[str, Any]):
        """存入 CSV (存所有标签)"""
        filename = f"{timestamp.strftime('%Y%m%d')}_process_data.csv"
        filepath = self.csv_dir / filename
        file_exists = filepath.exists()

        with open(filepath, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)

            # 使用全量 Headers
            headers = ["Timestamp"] + (self.all_csv_headers if self.all_csv_headers else list(flat_data.keys()))

            if not file_exists:
                writer.writerow(headers)

            row = [timestamp.strftime("%Y-%m-%d %H:%M:%S")]
            for key in headers[1:]: # 跳过 Timestamp
                row.append(flat_data.get(key, ""))

            writer.writerow(row)

    # (Getters 保持不变)
    def get_current_data(self, key: Optional[str] = None) -> Any:
        with self._cache_lock:
            if key: return self._cache.get(key)
            return self._cache.copy()

    def get_historical_data(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, feed_grade, conc_grade, recovery 
                FROM process_history
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            ''', (start_time, end_time))
            return [dict(row) for row in cursor.fetchall()]

_data_service_instance = None
def get_data_service() -> DataService:
    global _data_service_instance
    if _data_service_instance is None:
        _data_service_instance = DataService()
    return _data_service_instance