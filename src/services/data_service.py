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

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.csv_dir.mkdir(parents=True, exist_ok=True)

        self._cache: Dict[str, Any] = {}
        self._cache_lock = Lock()

        # [修改] 关键 KPI 定义 (用于 CSV 表头)
        # 对应：原矿、高铅精矿、尾矿
        self.kpi_keys = [
            "KYFX.kyfx_yk_grade_Pb",    # 原矿
            "KYFX.kyfx_gqxk_grade_Pb",  # 高铅精矿
            "KYFX.kyfx_qw_grade_Pb",    # 尾矿 (用于后续验证计算)
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

    def restart(self) -> bool:
        """重启数据服务"""
        self.stop()
        return self.start()

    def _init_database(self) -> None:
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            # 1. 过程数据表 (更新字段以匹配新指标)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS process_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    feed_grade REAL,    -- 原矿
                    conc_grade REAL,    -- 精矿
                    recovery REAL,      -- 回收率
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
        """接收并保存数据"""
        try:
            timestamp = datetime.now()

            with self._cache_lock:
                self._cache.update(data)
                self._cache['last_updated'] = timestamp

            # 数据扁平化
            flat_data = {}
            for key, val in data.items():
                if isinstance(val, dict) and 'value' in val:
                    flat_data[key] = float(val['value'])
                else:
                    flat_data[key] = val

            # 存入 SQLite
            self._save_to_sqlite(timestamp, flat_data)

            # 存入 CSV
            self._save_to_csv(timestamp, flat_data)

        except Exception as e:
            print(f"数据保存失败: {e}")

    def _save_to_sqlite(self, timestamp, flat_data: Dict[str, Any]):
        """保存到 SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 提取数据
            f_grade = flat_data.get("KYFX.kyfx_yk_grade_Pb", 0.0)
            c_grade = flat_data.get("KYFX.kyfx_gqxk_grade_Pb", 0.0)
            t_grade = flat_data.get("KYFX.kyfx_qw_grade_Pb", 0.0)

            # 计算回收率 (存入数据库方便查询)
            recovery = 0.0
            try:
                if f_grade > 0 and (c_grade - t_grade) != 0:
                    recovery = (c_grade * (f_grade - t_grade)) / (f_grade * (c_grade - t_grade)) * 100
            except:
                recovery = 0.0

            json_dump = json.dumps(flat_data)

            cursor.execute('''
                INSERT INTO process_history (timestamp, feed_grade, conc_grade, recovery, raw_data)
                VALUES (?, ?, ?, ?, ?)
            ''', (timestamp, f_grade, c_grade, recovery, json_dump))
            conn.commit()

    def _save_to_csv(self, timestamp, flat_data: Dict[str, Any]):
        """保存到 CSV"""
        filename = f"{timestamp.strftime('%Y%m%d')}_process_data.csv"
        filepath = self.csv_dir / filename
        file_exists = filepath.exists()

        with open(filepath, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)

            if not file_exists:
                header = ["Timestamp"] + self.kpi_keys + ["Calculated_Recovery", "Raw_JSON"]
                writer.writerow(header)

            row = [timestamp.strftime("%Y-%m-%d %H:%M:%S")]

            # 写入定义的 KPI
            f_grade = 0.0
            c_grade = 0.0
            t_grade = 0.0

            for key in self.kpi_keys:
                val = flat_data.get(key, "")
                row.append(val)
                # 顺便获取值用于计算
                if key == "KYFX.kyfx_yk_grade_Pb": f_grade = val if isinstance(val, (int, float)) else 0
                if key == "KYFX.kyfx_gqxk_grade_Pb": c_grade = val if isinstance(val, (int, float)) else 0
                if key == "KYFX.kyfx_qw_grade_Pb": t_grade = val if isinstance(val, (int, float)) else 0

            # 写入计算出的回收率
            rec = 0.0
            try:
                if f_grade > 0 and (c_grade - t_grade) != 0:
                    rec = (c_grade * (f_grade - t_grade)) / (f_grade * (c_grade - t_grade)) * 100
            except: pass
            row.append(f"{rec:.2f}")

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
                SELECT timestamp, feed_grade, conc_grade, recovery 
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