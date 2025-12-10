"""
数据服务
负责数据持久化存储 (SQLite + CSV)
"""

import time
import sqlite3
import csv
import os
import json
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

    def __init__(self, db_path: str = "data/system.db", csv_dir: str = "data/csv"):
        super().__init__("data_service")
        self.db_path = db_path
        self.csv_dir = Path(csv_dir)

        # 确保目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.csv_dir.mkdir(parents=True, exist_ok=True)

        self._cache: Dict[str, Any] = {}
        self._cache_lock = Lock()

        # 关键 KPI 定义 (用于 CSV 表头和 数据库字段)
        self.kpi_keys = [
            "KYFX.kyfx_dqxk_grade_Pb",  # 铅品位
            "KYFX.kyfx_dqxk_grade_Zn",  # 锌品位
            "KYFX.kyfx_yk_grade_Pb",    # 原矿/回收率参考
        ]

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
        """停止数据服务"""
        self.status = ServiceStatus.STOPPED
        return True

    # === [修复] 补回缺失的 restart 方法 ===
    def restart(self) -> bool:
        """重启数据服务"""
        self.stop()
        return self.start()

    def _init_database(self) -> None:
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            # 1. 过程数据表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS process_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    grade_pb REAL,
                    grade_zn REAL,
                    recovery REAL,
                    raw_data JSON
                )
            ''')

            # 2. 事件日志表
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
        """
        [核心方法] 接收并保存数据
        该方法应连接到 OPCWorker.data_updated 信号
        """
        try:
            timestamp = datetime.now()

            # 1. 更新内存缓存
            with self._cache_lock:
                self._cache.update(data)
                self._cache['last_updated'] = timestamp

            # 2. 数据扁平化处理
            flat_data = {}
            for key, val in data.items():
                if isinstance(val, dict) and 'value' in val:
                    flat_data[key] = float(val['value'])
                else:
                    flat_data[key] = val

            # 3. 存入 SQLite
            self._save_to_sqlite(timestamp, flat_data)

            # 4. 存入 CSV
            self._save_to_csv(timestamp, flat_data)

        except Exception as e:
            print(f"数据保存失败: {e}")

    def _save_to_sqlite(self, timestamp, flat_data: Dict[str, Any]):
        """保存到 SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            grade_pb = flat_data.get("KYFX.kyfx_dqxk_grade_Pb")
            grade_zn = flat_data.get("KYFX.kyfx_dqxk_grade_Zn")
            recovery = flat_data.get("KYFX.kyfx_yk_grade_Pb")

            json_dump = json.dumps(flat_data)

            cursor.execute('''
                INSERT INTO process_history (timestamp, grade_pb, grade_zn, recovery, raw_data)
                VALUES (?, ?, ?, ?, ?)
            ''', (timestamp, grade_pb, grade_zn, recovery, json_dump))
            conn.commit()

    def _save_to_csv(self, timestamp, flat_data: Dict[str, Any]):
        """保存到 CSV (按天分文件)"""
        filename = f"{timestamp.strftime('%Y%m%d')}_process_data.csv"
        filepath = self.csv_dir / filename

        file_exists = filepath.exists()

        with open(filepath, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)

            if not file_exists:
                header = ["Timestamp"] + self.kpi_keys + ["Raw_JSON"]
                writer.writerow(header)

            row = [timestamp.strftime("%Y-%m-%d %H:%M:%S")]

            for key in self.kpi_keys:
                val = flat_data.get(key, "")
                row.append(val)

            writer.writerow(row)

    def get_current_data(self, key: Optional[str] = None) -> Any:
        with self._cache_lock:
            if key:
                return self._cache.get(key)
            return self._cache.copy()

    def get_historical_data(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, grade_pb, grade_zn, recovery 
                FROM process_history
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            ''', (start_time, end_time))
            return [dict(row) for row in cursor.fetchall()]

# 单例模式
_data_service_instance = None
def get_data_service() -> DataService:
    global _data_service_instance
    if _data_service_instance is None:
        _data_service_instance = DataService()
    return _data_service_instance