import cv2
import threading
from queue import Queue, Empty
from typing import Optional, List, Dict
from dataclasses import dataclass

from config.settings import CameraConfig
from src.services.logging_service import SystemLogger


@dataclass
class FrameData:
    """帧数据"""
    camera_index: int
    frame: any
    timestamp: float
    frame_count: int


class VideoStreamService:
    """视频流服务"""

    def __init__(self, camera_configs: List[CameraConfig]):
        self.camera_configs = camera_configs
        self.logger = SystemLogger()
        self.streams: Dict[int, 'VideoStream'] = {}
        self.frame_queues: Dict[int, Queue] = {}
        self.is_running = False

    def initialize(self):
        """初始化视频流服务"""
        for i, config in enumerate(self.camera_configs):
            if config.enabled:
                stream = VideoStream(i, config, self.logger)
                self.streams[i] = stream
                self.frame_queues[i] = Queue(maxsize=1)

    def start_all(self):
        """启动所有视频流"""
        self.is_running = True
        for stream_id, stream in self.streams.items():
            if stream.start():
                threading.Thread(
                    target=self._process_stream_frames,
                    args=(stream_id,),
                    daemon=True
                ).start()

    def stop_all(self):
        """停止所有视频流"""
        self.is_running = False
        for stream in self.streams.values():
            stream.stop()

    def get_frame(self, camera_index: int, timeout: float = 1.0) -> Optional[FrameData]:
        """获取指定相机的帧"""
        if camera_index not in self.frame_queues:
            return None

        try:
            return self.frame_queues[camera_index].get(timeout=timeout)
        except Empty:
            return None

    def _process_stream_frames(self, stream_id: int):
        """处理视频流帧"""
        stream = self.streams[stream_id]
        frame_queue = self.frame_queues[stream_id]

        while self.is_running and stream.is_running:
            try:
                frame_data = stream.get_frame()
                if frame_data:
                    if not frame_queue.empty():
                        try:
                            frame_queue.get_nowait()
                        except Empty:
                            pass
                    frame_queue.put(frame_data)
            except Exception as e:
                self.logger.error(f"处理视频流 {stream_id} 失败: {e}")


class VideoStream:
    """单个视频流"""

    def __init__(self, stream_id: int, config: CameraConfig, logger: SystemLogger):
        self.stream_id = stream_id
        self.config = config
        self.logger = logger
        self.cap = None
        self.is_running = False
        self.frame_count = 0

    def start(self) -> bool:
        """启动视频流"""
        try:
            self.cap = cv2.VideoCapture(self.config.rtsp_url)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not self.cap.isOpened():
                self.logger.error(f"无法打开视频流: {self.config.rtsp_url}")
                return False

            self.is_running = True
            return True
        except Exception as e:
            self.logger.error(f"启动视频流失败: {e}")
            return False

    def stop(self):
        """停止视频流"""
        self.is_running = False
        if self.cap:
            self.cap.release()

    def get_frame(self) -> Optional[FrameData]:
        """获取帧"""
        if not self.is_running or not self.cap.isOpened():
            return None

        ret, frame = self.cap.read()
        if ret and frame is not None:
            self.frame_count += 1
            return FrameData(
                camera_index=self.stream_id,
                frame=frame,
                timestamp=cv2.getTickCount() / cv2.getTickFrequency(),
                frame_count=self.frame_count
            )
        return None