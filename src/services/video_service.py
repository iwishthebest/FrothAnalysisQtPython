import cv2
import numpy as np
import time
import threading  # [新增] 用于异步释放资源
from typing import Optional, List, Dict, Any
from PySide6.QtCore import QObject, QThread, Signal, Qt, QMutex
from PySide6.QtGui import QImage

from config.config_system import config_manager, CameraConfig
from src.services.logging_service import get_logging_service
from src.common.constants import LogCategory
from src.utils.video_utils import RTSPStreamReader


class CameraWorker(QObject):
    """
    相机工作线程类
    """
    frame_ready = Signal(int, QImage)
    status_changed = Signal(int, dict)
    start_requested = Signal()

    def __init__(self, camera_index: int, config: CameraConfig):
        super().__init__()
        self.camera_index = camera_index
        self.config = config
        self.running = False
        self.force_exit = False
        self.simulation_mode = False
        self.reader: Optional[RTSPStreamReader] = None
        self.display_size = (640, 480)

        self.start_requested.connect(self.start_work)

    def start_work(self):
        """线程启动入口"""
        if self.running:
            return

        self.running = True
        self.force_exit = False
        self.logger = get_logging_service()

        self._emit_status("starting", "正在启动...")

        self._initialize_connection()
        self._capture_loop()

        # 循环结束后的状态在 _capture_loop 中处理

    def stop_work(self, force_exit=False):
        """停止工作"""
        self.running = False
        self.force_exit = force_exit

    def set_simulation_mode(self, enabled: bool):
        self.simulation_mode = enabled
        # 模拟模式切换也建议异步处理防止卡顿，但通常模拟模式关闭很快
        if enabled and self.reader:
            self._async_release_reader(self.reader)
            self.reader = None

    def _initialize_connection(self):
        if self.force_exit:
            return

        if not self.simulation_mode:
            try:
                self.reader = RTSPStreamReader(
                    rtsp_url=self.config.rtsp_url,
                    window_size=tuple(map(int, self.config.resolution.split('x'))),
                    reconnect_interval=self.config.reconnect_interval,
                    max_retries=self.config.max_retries
                )
                if self.reader.start():
                    self.logger.info(f"相机 {self.camera_index} 连接成功", LogCategory.VIDEO)
                    self._emit_status("connected", "连接正常")
                else:
                    self.logger.warning(f"相机 {self.camera_index} 连接失败，切换模拟", LogCategory.VIDEO)
                    self.simulation_mode = True
                    self._emit_status("simulation", "连接失败-模拟中")
            except Exception as e:
                self.logger.error(f"相机 {self.camera_index} 初始化异常: {e}", LogCategory.VIDEO)
                self.simulation_mode = True
        else:
            self._emit_status("simulation", "模拟模式")

    def _capture_loop(self):
        """主捕获循环"""
        while self.running:
            if self.force_exit:
                break

            loop_start = time.time()
            frame = None

            try:
                if self.simulation_mode or self.reader is None:
                    frame = self._generate_simulation_frame()
                else:
                    frame = self.reader.get_frame(timeout=0.1)
                    if frame is None:
                        frame = self._generate_simulation_frame(text="NO SIGNAL")
            except Exception:
                frame = self._generate_simulation_frame(text="ERROR")

            if self.running and not self.force_exit and frame is not None:
                q_image = self._process_frame(frame)
                if q_image:
                    self.frame_ready.emit(self.camera_index, q_image)

            elapsed = (time.time() - loop_start) * 1000
            sleep_time = max(1, int(33 - elapsed))
            self._smart_sleep(sleep_time)

        # === 循环结束后的清理 ===

        # 1. 如果是程序强制退出，什么都不做，直接返回
        if self.force_exit:
            return

        # 2. 如果是手动停止，执行异步清理
        if self.reader:
            self._async_release_reader(self.reader)
            self.reader = None

        # 3. 立即通知 UI 已停止
        self._emit_status("stopped", "已断开")

    def _async_release_reader(self, reader_instance):
        """
        [核心修复] 异步释放 RTSP 资源
        创建一个临时的后台线程去执行 reader.stop()，避免阻塞当前 Worker 线程。
        这样 UI 可以立即收到 "已断开" 信号，而不用等待底层 socket 关闭。
        """

        def cleanup_task(r):
            try:
                # 这句代码可能会阻塞几秒钟，但在后台线程中运行不会影响主程序
                r.stop()
            except Exception as e:
                print(f"资源释放异常(已忽略): {e}")

        cleanup_thread = threading.Thread(target=cleanup_task, args=(reader_instance,))
        cleanup_thread.daemon = True  # 设置为守护线程，防止阻碍程序退出
        cleanup_thread.start()

    def _smart_sleep(self, ms):
        if ms <= 0 or self.force_exit: return
        steps = ms // 10
        for _ in range(steps):
            if not self.running or self.force_exit: return
            QThread.msleep(10)
        remainder = ms % 10
        if remainder > 0 and self.running and not self.force_exit:
            QThread.msleep(remainder)

    def _process_frame(self, frame_bgr: np.ndarray) -> Optional[QImage]:
        try:
            if self.force_exit: return None
            frame_resized = cv2.resize(frame_bgr, self.display_size)
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            return image.copy()
        except Exception:
            return None

    def _generate_simulation_frame(self, text=None) -> np.ndarray:
        w, h = self.display_size
        color = self.config.simulation_color
        frame = np.full((h, w, 3), color, dtype=np.uint8)
        noise = np.random.randint(0, 20, (h, w, 3), dtype=np.uint8)
        frame = cv2.add(frame, noise)
        t = time.time()
        cx = int(w / 2 + np.sin(t) * 50)
        cy = int(h / 2 + np.cos(t) * 30)
        cv2.circle(frame, (cx, cy), 30, (255, 255, 255), -1)
        display_text = text if text else ("SIMULATION" if self.simulation_mode else "Connecting...")
        cv2.putText(frame, display_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        return frame

    def _emit_status(self, status_code, message):
        if not self.force_exit:
            self.status_changed.emit(self.camera_index, {
                "status": status_code,
                "message": message,
                "name": self.config.name
            })


class VideoService(QObject):
    def __init__(self):
        super().__init__()
        self.logger = get_logging_service()
        self.camera_configs = config_manager.get_camera_configs()
        self.threads: Dict[int, QThread] = {}
        self.workers: Dict[int, CameraWorker] = {}
        self._initialize_workers()

    def _initialize_workers(self):
        for i, config in enumerate(self.camera_configs):
            thread = QThread()
            worker = CameraWorker(i, config)
            worker.moveToThread(thread)

            if config.enabled:
                thread.started.connect(worker.start_work)

            self.threads[i] = thread
            self.workers[i] = worker
            thread.start()
            self.logger.info(f"相机线程 {i} 已就绪", LogCategory.VIDEO)

    def get_worker(self, camera_index: int) -> Optional[CameraWorker]:
        return self.workers.get(camera_index)

    def start_camera(self, index: int):
        """手动启动指定相机"""
        if index in self.workers:
            self.workers[index].start_requested.emit()
            self.logger.info(f"发送启动指令: 相机 {index}", LogCategory.VIDEO)

    def stop_camera(self, index: int):
        """手动停止指定相机"""
        if index in self.workers:
            self.workers[index].stop_work()
            self.logger.info(f"发送停止指令: 相机 {index}", LogCategory.VIDEO)

    def set_simulation_mode(self, enabled: bool):
        for worker in self.workers.values():
            worker.set_simulation_mode(enabled)

    def cleanup(self):
        self.logger.info("正在停止所有视频线程 (FORCE EXIT)...", LogCategory.VIDEO)
        for worker in self.workers.values():
            worker.stop_work(force_exit=True)
        for thread in self.threads.values():
            thread.quit()
        for i, thread in self.threads.items():
            thread.wait(50)
        self.logger.info("视频服务资源清理完成", LogCategory.VIDEO)


_video_service_instance = None


def get_video_service() -> VideoService:
    global _video_service_instance
    if _video_service_instance is None:
        _video_service_instance = VideoService()
    return _video_service_instance