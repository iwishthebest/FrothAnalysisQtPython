"""
数据服务
负责数据采集、处理和存储
"""

import time
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from threading import Thread, Lock
from . import BaseService, ServiceError, ServiceStatus


class DataService(BaseService):
    """数据管理服务"""

    def __init__(self, db_path: str = "data/system.db"):
        super().__init__("data_service")
        self.db_path = db_path
        self._cache: Dict[str, Any] = {}
        self._cache_lock = Lock()
        self._collection_thread: Optional[Thread] = None
        self._running = False

    def start(self) -> bool:
        """启动数据服务"""
        try:
            self.status = ServiceStatus.STARTING

            # 初始化数据库
            self._init_database()

            # 启动数据收集线程
            self._running = True
            self._collection_thread = Thread(target=self._data_collection_loop, daemon=True)
            self._collection_thread.start()

            self.status = ServiceStatus.RUNNING
            return True

        except Exception as e:
            self.status = ServiceStatus.ERROR
            raise ServiceError(f"数据服务启动失败: {e}")

    def stop(self) -> bool:
        """停止数据服务"""
        self.status = ServiceStatus.STOPPING
        self._running = False

        if self._collection_thread:
            self._collection_thread.join(timeout=5)

        self.status = ServiceStatus.STOPPED
        return True

    def restart(self) -> bool:
        """重启数据服务"""
        self.stop()
        return self.start()

    def _init_database(self) -> None:
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                         CREATE TABLE IF NOT EXISTS process_data
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
                             tank_name
                             TEXT
                             NOT
                             NULL,
                             level
                             REAL,
                             temperature
                             REAL,
                             pressure
                             REAL
                         )
                         ''')
            conn.execute('''
                         CREATE TABLE IF NOT EXISTS event_log
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
                             event_type
                             TEXT
                             NOT
                             NULL,
                             message
                             TEXT,
                             severity
                             TEXT
                         )
                         ''')
            conn.commit()

    def _data_collection_loop(self) -> None:
        """数据收集循环"""
        while self._running:
            try:
                # 模拟数据收集
                current_data = self._collect_process_data()

                with self._cache_lock:
                    self._cache.update(current_data)

                # 存储到数据库
                self._store_to_database(current_data)

                time.sleep(1)  # 1秒采集一次

            except Exception as e:
                print(f"数据收集错误: {e}")
                time.sleep(5)

    def _collect_process_data(self) -> Dict[str, Any]:
        """收集过程数据（模拟实现）"""
        # 这里应该集成真实的OPC数据采集
        return {
            "tank1_level": 1.2 + 0.1 * (time.time() % 10 - 5),
            "tank1_temperature": 25.0 + 2.0 * (time.time() % 5 - 2.5),
            "tank2_level": 1.5 + 0.2 * (time.time() % 8 - 4),
            "timestamp": datetime.now()
        }

    def _store_to_database(self, data: Dict[str, Any]) -> None:
        """存储数据到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 存储过程数据
                cursor.execute('''
                               INSERT INTO process_data (timestamp, tank_name, level, temperature)
                               VALUES (?, ?, ?, ?)
                               ''', (
                                   data.get('timestamp', datetime.now()),
                                   'tank1',
                                   data.get('tank1_level'),
                                   data.get('tank1_temperature')
                               ))

                conn.commit()
        except Exception as e:
            print(f"数据存储失败: {e}")

    def get_current_data(self, key: Optional[str] = None) -> Any:
        """获取当前数据"""
        with self._cache_lock:
            if key:
                return self._cache.get(key)
            return self._cache.copy()

    def get_historical_data(self,
                            start_time: datetime,
                            end_time: datetime,
                            data_type: str = "process") -> List[Dict[str, Any]]:
        """获取历史数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                               SELECT *
                               FROM process_data
                               WHERE timestamp BETWEEN ? AND ?
                               ORDER BY timestamp
                               ''', (start_time, end_time))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            raise ServiceError(f"查询历史数据失败: {e}")