"""
数据管理模块 - 统一管理实时和历史数据
"""

import time
import threading
from collections import deque, OrderedDict
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import logging


@dataclass
class TankData:
    """浮选槽数据"""
    tank_id: int
    level: float
    dosing_rate: float
    reagent_type: str
    status: str
    timestamp: float


@dataclass
class CameraData:
    """相机数据"""
    camera_id: int
    frame_count: int
    fps: float
    status: str
    timestamp: float


class DataCache:
    """数据缓存管理器"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl  # 数据存活时间（秒）
        self.lock = threading.RLock()
        self.hit_count = 0
        self.miss_count = 0
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        with self.lock:
            if key in self.cache:
                data = self.cache[key]
                # 检查是否过期
                if time.time() - data['timestamp'] < self.ttl:
                    self.hit_count += 1
                    self.cache.move_to_end(key)  # 移动到最近使用
                    return data['value']
            
            self.miss_count += 1
            return None
    
    def set(self, key: str, value: Any):
        """设置缓存数据"""
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            
            self.cache[key] = {
                'value': value,
                'timestamp': time.time(),
                'version': self.cache.get(key, {}).get('version', 0) + 1
            }
            
            # 清理过期数据
            self._cleanup()
    
    def _cleanup(self):
        """清理过期和超量数据"""
        current_time = time.time()
        
        # 清理过期数据
        expired_keys = []
        for key, data in self.cache.items():
            if current_time - data['timestamp'] > self.ttl:
                expired_keys.append(key)
            else:
                break  # 有序字典，后面的数据更新
        
        for key in expired_keys:
            del self.cache[key]
        
        # 清理超量数据
        while len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self.lock:
            total_requests = self.hit_count + self.miss_count
            hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
            
            return {
                'size': len(self.cache),
                'hit_rate': hit_rate,
                'hit_count': self.hit_count,
                'miss_count': self.miss_count,
                'total_requests': total_requests
            }


class TimeSeriesData:
    """时间序列数据管理"""
    
    def __init__(self, max_points: int = 1000):
        self.data = deque(maxlen=max_points)
        self.lock = threading.RLock()
    
    def add_point(self, timestamp: float, value: float, metadata: Dict = None):
        """添加数据点"""
        with self.lock:
            point = {
                'timestamp': timestamp,
                'value': value,
                'metadata': metadata or {}
            }
            self.data.append(point)
    
    def get_range(self, start_time: float, end_time: float) -> List[Dict]:
        """获取时间范围内的数据"""
        with self.lock:
            return [
                point for point in self.data
                if start_time <= point['timestamp'] <= end_time
            ]
    
    def get_latest(self, count: int = 1) -> List[Dict]:
        """获取最新数据点"""
        with self.lock:
            return list(self.data)[-count:]
    
    def clear(self):
        """清空数据"""
        with self.lock:
            self.data.clear()


class DataManager:
    """数据管理器"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.cache = DataCache()
        self.tank_data = {}  # 浮选槽实时数据
        self.camera_data = {}  # 相机实时数据
        self.history_data = {}  # 历史数据
        self.opc_client = None
        self.is_running = False
        self.update_callbacks = []
        
        # 初始化数据结构
        self._initialize_data_structures()
    
    def _initialize_data_structures(self):
        """初始化数据结构"""
        # 初始化浮选槽数据存储
        for i in range(4):  # 4个浮选槽
            self.tank_data[i] = TimeSeriesData(1000)
            self.history_data[f'tank_{i}'] = TimeSeriesData(24 * 60)  # 24小时数据
        
        # 初始化相机数据存储
        for i in range(4):  # 4个相机
            self.camera_data[i] = TimeSeriesData(100)
    
    def start(self):
        """启动数据管理"""
        self.is_running = True
        
        # 启动数据更新线程
        threading.Thread(target=self._data_update_loop, daemon=True).start()
        threading.Thread(target=self._history_cleanup_loop, daemon=True).start()
        
        self.logger.info("数据管理器已启动")
    
    def stop(self):
        """停止数据管理"""
        self.is_running = False
        self.logger.info("数据管理器已停止")
    
    def _data_update_loop(self):
        """数据更新循环"""
        while self.is_running:
            try:
                # 模拟从OPC服务器获取数据
                self._update_tank_data()
                self._update_camera_data()
                
                # 调用更新回调
                for callback in self.update_callbacks:
                    try:
                        callback()
                    except Exception as e:
                        self.logger.error(f"数据更新回调失败: {e}")
                
                time.sleep(1)  # 1秒更新一次
                
            except Exception as e:
                self.logger.error(f"数据更新循环异常: {e}")
                time.sleep(5)
    
    def _update_tank_data(self):
        """更新浮选槽数据"""
        current_time = time.time()
        
        for tank_id in range(4):
            # 模拟浮选槽数据
            tank_data = TankData(
                tank_id=tank_id,
                level=1.2 + tank_id * 0.1 + (0.1 if current_time % 10 < 5 else -0.1),
                dosing_rate=50 + tank_id * 10,
                reagent_type=["捕收剂", "起泡剂", "抑制剂"][tank_id % 3],
                status="运行正常",
                timestamp=current_time
            )
            
            # 存储实时数据
            self.tank_data[tank_id].add_point(current_time, tank_data.level, asdict(tank_data))
            
            # 存储历史数据
            self.history_data[f'tank_{tank_id}'].add_point(current_time, tank_data.level)
            
            # 更新缓存
            self.cache.set(f'tank_{tank_id}_current', asdict(tank_data))
    
    def _update_camera_data(self):
        """更新相机数据"""
        current_time = time.time()
        
        for cam_id in range(4):
            camera_data = CameraData(
                camera_id=cam_id,
                frame_count=int(current_time) * 10 + cam_id,
                fps=15.0 + cam_id * 5,
                status="正常",
                timestamp=current_time
            )
            
            self.camera_data[cam_id].add_point(current_time, camera_data.fps, asdict(camera_data))
            self.cache.set(f'camera_{cam_id}_current', asdict(camera_data))
    
    def _history_cleanup_loop(self):
        """历史数据清理循环"""
        while self.is_running:
            try:
                # 每小时清理一次过期数据
                time.sleep(3600)
                
                # 这里可以实现历史数据归档逻辑
                self.logger.info("执行历史数据清理")
                
            except Exception as e:
                self.logger.error(f"历史数据清理异常: {e}")
    
    def get_tank_current_data(self, tank_id: int) -> Optional[Dict]:
        """获取浮选槽当前数据"""
        return self.cache.get(f'tank_{tank_id}_current')
    
    def get_tank_history_data(self, tank_id: int, hours: int = 1) -> List[Dict]:
        """获取浮选槽历史数据"""
        end_time = time.time()
        start_time = end_time - hours * 3600
        return self.history_data[f'tank_{tank_id}'].get_range(start_time, end_time)
    
    def get_camera_current_data(self, camera_id: int) -> Optional[Dict]:
        """获取相机当前数据"""
        return self.cache.get(f'camera_{camera_id}_current')
    
    def register_update_callback(self, callback):
        """注册数据更新回调"""
        self.update_callbacks.append(callback)
    
    def export_data(self, start_time: float, end_time: float, data_type: str = 'tank') -> str:
        """导出数据为JSON格式"""
        export_data = {
            'metadata': {
                'export_time': time.time(),
                'start_time': start_time,
                'end_time': end_time,
                'data_type': data_type
            },
            'data': []
        }
        
        if data_type == 'tank':
            for tank_id in range(4):
                tank_points = self.history_data[f'tank_{tank_id}'].get_range(start_time, end_time)
                export_data['data'].extend(tank_points)
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)


# 使用示例
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("DataManagerTest")
    
    manager = DataManager(logger)
    manager.start()
    
    try:
        # 测试数据获取
        for i in range(5):
            time.sleep(2)
            tank_data = manager.get_tank_current_data(0)
            print(f"浮选槽0数据: {tank_data}")
            
            cache_stats = manager.cache.get_stats()
            print(f"缓存统计: {cache_stats}")
    finally:
        manager.stop()
