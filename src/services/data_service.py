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

try:
    from . import BaseService, ServiceError, ServiceStatus
except ImportError:
    from PySide6.QtCore import QObject


    class BaseService(QObject):
        def __init__(self, name): super().__init__()


    class ServiceStatus:
        STARTING = "STARTING";
        RUNNING = "RUNNING";
        STOPPING = "STOPPING";
        STOPPED = "STOPPED";
        ERROR = "ERROR"


    class ServiceError(Exception):
        pass


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

        # [核心] 加载所有标签作为 CSV 表头
        self.all_csv_headers = self._load_all_headers()

        # 状态记录
        # [修改] 使用独立的周期性保存计时器，避免被快频保存重置
        self.last_periodic_save_time = datetime.min
        self.yj_value_cache = {}  # 用于比对药剂值是否变化

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
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                         CREATE TABLE IF NOT EXISTS process_history
                         (
                             id
                             INTEGER
                             PRIMARY
                             KEY
                             AUTOINCREMENT,
                             timestamp
                             DATETIME
                             NOT
                             NULL,
                             feed_grade
                             REAL,
                             conc_grade
                             REAL,
                             recovery
                             REAL,
                             raw_data
                             JSON
                         )
                         ''')
            conn.commit()

    def record_data(self, data: Dict[str, Any]) -> None:
        """
        接收并保存数据
        策略：
        1. YJ (快频) 标签：数值变化即保存 (基于缓存比对)
        2. KYFX (慢频) 标签 / 定时：每10分钟(默认)强制保存一次
        """
        try:
            timestamp = datetime.now()
            should_save = False

            with self._cache_lock:
                self._cache.update(data)
                self._cache['last_updated'] = timestamp

            # [修改] 获取配置的慢频间隔，用于定时保存
            slow_interval = config_manager.get_network_config().slow_tag_interval

            # 策略1: 定时强制保存 (主要针对 KYFX)
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
                        # [修改] 处理 None 值 (例如 OPC 返回的无效数据)
                        v = val['value']
                        flat_data[key] = float(v) if v is not None else None
                    else:
                        flat_data[key] = val

                self._save_to_sqlite(timestamp, flat_data)
                self._save_to_csv(timestamp, flat_data)

        except Exception as e:
            print(f"数据保存失败: {e}")

    def _save_to_sqlite(self, timestamp, flat_data: Dict[str, Any]):
        """存入数据库 (处理无效值)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # [新增] 辅助函数：清洗无效值
            def get_clean(key):
                val = flat_data.get(key)
                if val == -9999.0 or val is None:
                    return None  # 数据库存为 NULL
                return val

            f = get_clean("KYFX.kyfx_yk_grade_Pb")
            c = get_clean("KYFX.kyfx_gqxk_grade_Pb")
            c_total = get_clean("KYFX.kyfx_zqxk_grade_Pb")
            t = get_clean("KYFX.kyfx_qw_grade_Pb")

            rec = None
            try:
                # 只有数据全有效才计算回收率
                if f is not None and c_total is not None and t is not None:
                    if f > 0 and (c_total - t) != 0:
                        rec = (c_total * (f - t)) / (f * (c_total - t)) * 100
            except:
                pass

            json_dump = json.dumps(flat_data)

            cursor.execute('''
                           INSERT INTO process_history (timestamp, feed_grade, conc_grade, recovery, raw_data)
                           VALUES (?, ?, ?, ?, ?)
                           ''', (timestamp, f, c, rec, json_dump))
            conn.commit()

    def _save_to_csv(self, timestamp, flat_data: Dict[str, Any]):
        """存入 CSV (处理无效值)"""
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
                # [新增] CSV 中将 -9999 和 None 存为空字符串
                if val == -9999.0 or val is None:
                    row.append("")
                else:
                    row.append(val)

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