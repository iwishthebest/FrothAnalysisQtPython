"""
数据服务
负责数据持久化存储 (SQLite + CSV)
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

# 尝试导入基类
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
    """数据管理服务 - 双模存储 (Database + CSV)"""

    def __init__(self, db_path: str = "data/system.db", csv_dir: str = "data/csv", tag_list_file: str = "resources/tags/tagList.csv"):
        super().__init__("data_service")
        self.db_path = db_path
        self.csv_dir = Path(csv_dir)
        self.tag_list_file = tag_list_file

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.csv_dir.mkdir(parents=True, exist_ok=True)

        self._cache: Dict[str, Any] = {}
        self._cache_lock = Lock()

        # [新增] 加载所有标签作为 CSV 表头
        self.all_csv_headers = self._load_all_headers()

        # 保存策略状态
        self.last_kyfx_save = datetime.min
        self.yj_data_cache = {} # 用于检测变化

    def start(self) -> bool:
        """启动数据服务"""
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
        """从文件加载所有标签名，确保CSV包含所有数据"""
        headers = []
        try:
            with open(self.tag_list_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row:
                        cleaned = re.sub(r'[\[\]]', '', row[0])
                        # 保持和 OPC Service 一致的前缀逻辑
                        if cleaned.startswith('yj_'): headers.append(f'YJ.{cleaned}')
                        elif cleaned.startswith('kyfx_'): headers.append(f'KYFX.{cleaned}')
                        else: headers.append(cleaned)
        except Exception as e:
            print(f"加载标签列表失败: {e}")
        return headers

    def _init_database(self) -> None:
        """初始化数据库表结构"""
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
            conn.execute('''
                CREATE TABLE IF NOT EXISTS event_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    event_type TEXT NOT NULL,
                    message TEXT,
                    severity TEXT
                )
            ''')
            conn.commit()

    def record_data(self, data: Dict[str, Any]) -> None:
        """接收并保存数据 (智能分频策略)"""
        try:
            timestamp = datetime.now()
            should_save = False

            # 1. 更新内存缓存
            with self._cache_lock:
                self._cache.update(data)
                self._cache['last_updated'] = timestamp

            # 2. 策略A: 10分钟强制保存 (针对 KYFX)
            if (timestamp - self.last_kyfx_save).total_seconds() >= 600:
                should_save = True
                self.last_kyfx_save = timestamp
                # print("触发定时保存 (KYFX)")

            # 3. 策略B: 实时变化保存 (针对 YJ)
            # 检查是否有 YJ 标签的值发生了变化
            yj_changed = False
            for key, val_dict in data.items():
                if key.startswith("YJ."):
                    val = val_dict.get('value')
                    if self.yj_data_cache.get(key) != val:
                        self.yj_data_cache[key] = val
                        yj_changed = True

            if yj_changed:
                should_save = True
                # print("触发实时保存 (YJ变化)")

            # 4. 执行保存
            if should_save:
                # 扁平化数据
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
        """保存到 SQLite (仅存KPI)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            f_grade = flat_data.get("KYFX.kyfx_yk_grade_Pb", 0.0)
            c_grade = flat_data.get("KYFX.kyfx_gqxk_grade_Pb", 0.0)
            t_grade = flat_data.get("KYFX.kyfx_qw_grade_Pb", 0.0)

            recovery = 0.0
            try:
                if f_grade > 0 and (c_grade - t_grade) != 0:
                    recovery = (c_grade * (f_grade - t_grade)) / (f_grade * (c_grade - t_grade)) * 100
            except: pass

            json_dump = json.dumps(flat_data)

            cursor.execute('''
                INSERT INTO process_history (timestamp, feed_grade, conc_grade, recovery, raw_data)
                VALUES (?, ?, ?, ?, ?)
            ''', (timestamp, f_grade, c_grade, recovery, json_dump))
            conn.commit()

    def _save_to_csv(self, timestamp, flat_data: Dict[str, Any]):
        """保存到 CSV (保存所有标签)"""
        filename = f"{timestamp.strftime('%Y%m%d')}_process_data.csv"
        filepath = self.csv_dir / filename
        file_exists = filepath.exists()

        with open(filepath, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)

            # 使用加载的全量 Headers
            header_keys = self.all_csv_headers if self.all_csv_headers else list(flat_data.keys())

            if not file_exists:
                # 表头：时间 + 所有标签
                writer.writerow(["Timestamp"] + header_keys)

            row = [timestamp.strftime("%Y-%m-%d %H:%M:%S")]
            for key in header_keys:
                row.append(flat_data.get(key, "")) # 没取到的留空

            writer.writerow(row)

    # ... (Getters 保持不变)
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