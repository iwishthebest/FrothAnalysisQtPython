import cv2
import numpy as np
import time
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
    负责：捕获帧 -> 缩放 -> 格式转换 -> 发送信号
    """
    frame_ready = Signal(int, QImage)
    status_changed = Signal(int, dict)

    def __init__(self, camera_index: int, config: CameraConfig):
        super().__init__()
        self.camera_index = camera_index
        self.config = config
        self.running = False
        self.simulation_mode = False
        self.reader: Optional[RTSPStreamReader] = None
        self._mutex = QMutex()

        self.display_size = (640, 480)

    def start_work(self):
        """线程启动入口"""
        self.running = True
        self.logger = get_logging_service()
        self._initialize_connection()
        self._capture_loop()

    def stop_work(self):
        """停止工作"""
        self.running = False

    def set_simulation_mode(self, enabled: bool):
        self.simulation_mode = enabled
        if enabled and self.reader:
            try:
                self.reader.stop()
            except Exception:
                pass
            self.reader = None

    def _initialize_connection(self):
        if not self.config.enabled:
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
            loop_start = time.time()
            frame = None

            # 1. 获取帧
            try:
                if not self.config.enabled:
                    frame = self._generate_simulation_frame(text="DISABLED")
                    self._smart_sleep(200)  # 使用智能睡眠
                elif self.simulation_mode or self.reader is None:
                    frame = self._generate_simulation_frame()
                else:
                    frame = self.reader.get_frame(timeout=0.1)
                    if frame is None:
                        frame = self._generate_simulation_frame(text="NO SIGNAL")
            except Exception as e:
                print(f"Capture error: {e}")
                frame = self._generate_simulation_frame(text="ERROR")

            # 2. 处理帧
            if self.running and frame is not None:
                q_image = self._process_frame(frame)
                if q_image:
                    self.frame_ready.emit(self.camera_index, q_image)

            # 3. 控制帧率
            elapsed = (time.time() - loop_start) * 1000
            sleep_time = max(1, int(33 - elapsed))
            self._smart_sleep(sleep_time)

        # 退出循环后清理
        if self.reader:
            try:
                self.reader.stop()
            except Exception as e:
                print(f"相机 {self.camera_index} 资源释放异常: {e}")

    def _smart_sleep(self, ms):
        """[优化] 智能切片睡眠，每10ms检查一次退出标志，防止卡死"""
        if ms <= 0: return

        # 如果睡眠时间很短，直接睡
        if ms < 20:
            QThread.msleep(ms)
            return

        # 如果时间较长，分段睡，随时响应退出
        steps = ms // 10
        for _ in range(steps):
            if not self.running:
                return
            QThread.msleep(10)

        # 补齐剩下的时间
        remainder = ms % 10
        if remainder > 0 and self.running:
            QThread.msleep(remainder)

    def _process_frame(self, frame_bgr: np.ndarray) -> Optional[QImage]:
        try:
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
        cv2.putText(frame, display_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                    1.0, (255, 255, 255), 2)
        return frame

    def _emit_status(self, status_code, message):
        self.status_changed.emit(self.camera_index, {
            "status": status_code,
            "message": message,
            "name": self.config.name
        })


class VideoService(QObject):
    """
    视频服务管理类
    """

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
            thread.started.connect(worker.start_work)

            self.threads[i] = thread
            self.workers[i] = worker

            thread.start()
            self.logger.info(f"相机线程 {i} 已启动", LogCategory.VIDEO)

    def get_worker(self, camera_index: int) -> Optional[CameraWorker]:
        return self.workers.get(camera_index)

    def set_simulation_mode(self, enabled: bool):
        for worker in self.workers.values():
            worker.set_simulation_mode(enabled)

    def cleanup(self):
        """[优化] 极速清理资源，防止界面卡死"""
        self.logger.info("正在停止所有视频线程...", LogCategory.VIDEO)

        # 1. 广播停止：先告诉所有 Worker 停止干活
        for worker in self.workers.values():
            worker.stop_work()

        # 2. 广播退出：告诉所有线程结束事件循环
        for thread in self.threads.values():
            thread.quit()

        # 3. 极速等待：每个线程只等 100ms
        # 在程序退出阶段，我们不需要优雅地等待资源释放，
        # 如果 100ms 内线程没退出来（比如卡在 opencv release），
        # 我们直接放弃等待，让操作系统去回收进程资源。
        # 这样可以保证界面瞬间关闭，不会卡顿。
        for i, thread in self.threads.items():
            if not thread.wait(100):
                # self.logger.warning(f"相机线程 {i} 退出超时，强制跳过", LogCategory.VIDEO)
                pass

        self.logger.info("视频服务资源清理完成", LogCategory.VIDEO)


# 单例模式实例
_video_service_instance = None


def get_video_service() -> VideoService:
    global _video_service_instance
    if _video_service_instance is None:
        _video_service_instance = VideoService()
    return _video_service_instance