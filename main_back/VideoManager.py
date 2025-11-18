"""
视频管理模块 - 统一管理所有RTSP视频流
"""

import cv2
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue, Empty
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
import logging

from Config import CameraConfig, config_manager


@dataclass
class FrameData:
    """帧数据类"""
    camera_index: int
    frame: any
    timestamp: float
    frame_count: int


class VideoStreamManager:
    """视频流管理器"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.camera_configs = config_manager.get_camera_configs()
        self.active_streams: Dict[int, 'VideoStream'] = {}
        self.frame_queues: Dict[int, Queue] = {}
        self.is_running = False
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.update_callbacks: List[Callable] = []
        
        # 性能监控
        self.performance_stats = {
            'fps': {},
            'frame_counts': {},
            'last_update_time': time.time()
        }
    
    def initialize(self):
        """初始化所有视频流"""
        enabled_cameras = [cam for cam in self.camera_configs if cam.enabled]
        
        for i, config in enumerate(enabled_cameras):
            stream = VideoStream(i, config, self.logger)
            self.active_streams[i] = stream
            self.frame_queues[i] = Queue(maxsize=1)
            
            # 初始化性能统计
            self.performance_stats['fps'][i] = 0
            self.performance_stats['frame_counts'][i] = 0
        
        self.logger.info(f"初始化了 {len(enabled_cameras)} 个视频流")
    
    def start_all(self):
        """启动所有视频流"""
        self.is_running = True
        
        for stream_id, stream in self.active_streams.items():
            if stream.start():
                # 启动帧处理线程
                threading.Thread(
                    target=self._process_stream_frames,
                    args=(stream_id,),
                    daemon=True
                ).start()
        
        self.logger.info("所有视频流已启动")
    
    def stop_all(self):
        """停止所有视频流"""
        self.is_running = False
        
        for stream in self.active_streams.values():
            stream.stop()
        
        self.thread_pool.shutdown(wait=False)
        self.logger.info("所有视频流已停止")
    
    def _process_stream_frames(self, stream_id: int):
        """处理单个视频流的帧"""
        stream = self.active_streams[stream_id]
        frame_queue = self.frame_queues[stream_id]
        
        while self.is_running and stream.is_running:
            try:
                frame_data = stream.get_frame(timeout=1.0)
                if frame_data is not None:
                    # 更新性能统计
                    self.performance_stats['frame_counts'][stream_id] += 1
                    
                    # 放入队列（替换旧帧）
                    if not frame_queue.empty():
                        try:
                            frame_queue.get_nowait()
                        except Empty:
                            pass
                    
                    frame_queue.put(frame_data, timeout=0.5)
                    
                    # 调用更新回调
                    for callback in self.update_callbacks:
                        try:
                            callback(stream_id, frame_data)
                        except Exception as e:
                            self.logger.error(f"回调函数执行失败: {e}")
                
            except Exception as e:
                self.logger.error(f"处理视频流 {stream_id} 帧数据失败: {e}")
                time.sleep(0.1)
    
    def get_frame(self, stream_id: int, timeout: float = 1.0) -> Optional[FrameData]:
        """获取指定视频流的帧"""
        if stream_id not in self.frame_queues:
            return None
        
        try:
            return self.frame_queues[stream_id].get(timeout=timeout)
        except Empty:
            return None
    
    def get_performance_stats(self) -> Dict:
        """获取性能统计"""
        current_time = time.time()
        time_diff = current_time - self.performance_stats['last_update_time']
        
        if time_diff > 0:
            for stream_id, frame_count in self.performance_stats['frame_counts'].items():
                self.performance_stats['fps'][stream_id] = frame_count / time_diff
                self.performance_stats['frame_counts'][stream_id] = 0
            
            self.performance_stats['last_update_time'] = current_time
        
        return self.performance_stats
    
    def register_update_callback(self, callback: Callable):
        """注册帧更新回调函数"""
        self.update_callbacks.append(callback)
    
    def add_camera(self, config: CameraConfig) -> int:
        """添加新相机"""
        new_index = max(self.active_streams.keys(), default=-1) + 1
        stream = VideoStream(new_index, config, self.logger)
        
        if stream.start():
            self.active_streams[new_index] = stream
            self.frame_queues[new_index] = Queue(maxsize=1)
            
            # 启动处理线程
            threading.Thread(
                target=self._process_stream_frames,
                args=(new_index,),
                daemon=True
            ).start()
            
            self.logger.info(f"添加新相机: {config.name}")
            return new_index
        
        return -1


class VideoStream:
    """单个视频流处理"""
    
    def __init__(self, stream_id: int, config: CameraConfig, logger: logging.Logger):
        self.stream_id = stream_id
        self.config = config
        self.logger = logger
        self.cap = None
        self.is_running = False
        self.last_frame = None
        self.frame_count = 0
        self.last_read_time = 0
    
    def start(self) -> bool:
        """启动视频流"""
        try:
            self.cap = cv2.VideoCapture(self.config.rtsp_url)
            
            # 设置OpenCV参数
            self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, self.config.timeout * 1000)
            self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, self.config.timeout * 1000)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            if not self.cap.isOpened():
                self.logger.error(f"无法打开视频流: {self.config.rtsp_url}")
                return False
            
            # 测试读取
            ret, frame = self.cap.read()
            if not ret:
                self.logger.error(f"无法从视频流读取帧: {self.config.name}")
                return False
            
            self.is_running = True
            self.last_read_time = time.time()
            self.logger.info(f"视频流启动成功: {self.config.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"启动视频流失败 {self.config.name}: {e}")
            return False
    
    def stop(self):
        """停止视频流"""
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def get_frame(self, timeout: float = 1.0) -> Optional[FrameData]:
        """获取帧数据"""
        if not self.is_running or self.cap is None or not self.cap.isOpened():
            return None
        
        try:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                self.frame_count += 1
                self.last_read_time = time.time()
                self.last_frame = frame
                
                return FrameData(
                    camera_index=self.stream_id,
                    frame=frame,
                    timestamp=time.time(),
                    frame_count=self.frame_count
                )
            else:
                # 读取失败，尝试重新连接
                self.logger.warning(f"视频流 {self.config.name} 读取失败，尝试重新连接")
                self._reconnect()
                
        except Exception as e:
            self.logger.error(f"获取帧数据失败 {self.config.name}: {e}")
            self._reconnect()
        
        return None
    
    def _reconnect(self):
        """重新连接"""
        self.stop()
        time.sleep(self.config.reconnect_interval)
        self.start()


# 使用示例
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("VideoManagerTest")
    
    manager = VideoStreamManager(logger)
    manager.initialize()
    manager.start_all()
    
    try:
        # 模拟运行一段时间
        for i in range(10):
            time.sleep(1)
            stats = manager.get_performance_stats()
            print(f"性能统计: {stats}")
    finally:
        manager.stop_all()
