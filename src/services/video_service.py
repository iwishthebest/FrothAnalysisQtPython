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
    """
    frame_ready = Signal(int, QImage)
    status_changed = Signal(int, dict)

    def __init__(self, camera_index: int, config: CameraConfig):
        super().__init__()
        self.camera_index = camera_index
        self.config = config
        self.running = False
        self.force_exit = False  # [新增] 强制退出标志
        self.simulation_mode = False
        self.reader: Optional[RTSPStreamReader] = None
        self.display_size = (640, 480)

    def start_work(self):
        """线程启动入口"""
        self.running = True
        self.force_exit = False
        self.logger = get_logging_service()
        self._initialize_connection()
        self._capture_loop()

    def stop_work(self, force_exit=False):
        """停止工作
        Args:
            force_exit: 如果为 True，表示程序即将关闭，跳过耗时的资源释放
        """
        self.running = False
        self.force_exit = force_exit

    def set_simulation_mode(self, enabled: bool):
        self.simulation_mode = enabled
        if enabled and self.reader:
            try:
                self.reader.stop()
            except:
                pass
            self.reader = None

    def _initialize_connection(self):
        if not self.config.enabled:
            return

        # 如果已经处于强制退出状态，直接返回，不进行耗时的连接
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
            # [关键] 每次循环前检查，如果是强制退出，立即中断，不处理任何逻辑
            if self.force_exit:
                return  # 直接返回，跳过 finally 块中的清理

            loop_start = time.time()
            frame = None

            try:
                # 获取帧
                if not self.config.enabled:
                    frame = self._generate_simulation_frame(text="DISABLED")
                    self._smart_sleep(200)
                elif self.simulation_mode or self.reader is None:
                    frame = self._generate_simulation_frame()
                else:
                    frame = self.reader.get_frame(timeout=0.1)
                    if frame is None:
                        frame = self._generate_simulation_frame(text="NO SIGNAL")
            except Exception:
                frame = self._generate_simulation_frame(text="ERROR")

            # 处理帧
            if self.running and not self.force_exit and frame is not None:
                q_image = self._process_frame(frame)
                if q_image:
                    self.frame_ready.emit(self.camera_index, q_image)

            # 控制帧率
            elapsed = (time.time() - loop_start) * 1000
            sleep_time = max(1, int(33 - elapsed))
            self._smart_sleep(sleep_time)

        # === 退出循环后的清理 ===
        # [核心修复]：如果是强制退出 (App关闭)，直接跳过 reader.stop()。
        # reader.stop() 会调用 cv2.release()，这在断流时可能会卡死 GIL，导致主线程卡死。
        # 既然进程都要关了，让 OS 去回收 socket 资源即可。
        if not self.force_exit and self.reader:
            try:
                self.reader.stop()
            except Exception as e:
                print(f"相机 {self.camera_index} 资源释放异常: {e}")

    def _smart_sleep(self, ms):
        """智能切片睡眠"""
        if ms <= 0 or self.force_exit: return

        # 将长睡眠切成小片
        steps = ms // 10
        for _ in range(steps):
            if not self.running or self.force_exit:
                return
            QThread.msleep(10)

        remainder = ms % 10
        if remainder > 0 and self.running and not self.force_exit:
            QThread.msleep(remainder)

    def _process_frame(self, frame_bgr: np.ndarray) -> Optional[QImage]:
        try:
            # 再次检查，防止处理时退出
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
        cv2.putText(frame, display_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                    1.0, (255, 255, 255), 2)
        return frame

    def _emit_status(self, status_code, message):
        if not self.force_exit:
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
        """[最终优化] 弃船逃生式清理，确保零卡顿退出"""
        self.logger.info("正在停止所有视频线程 (FORCE EXIT)...", LogCategory.VIDEO)

        # 1. 发出弃船指令
        # 告诉所有 Worker：马上要关机了，手里有什么资源直接扔掉，不要尝试关闭连接，直接 return。
        for worker in self.workers.values():
            worker.stop_work(force_exit=True)

        # 2. 退出线程循环
        for thread in self.threads.values():
            thread.quit()

        # 3. 极速等待 (50ms)
        # 我们给线程 50ms 的时间去响应 return。
        # 如果它们正卡在 cv2.VideoCapture() 这种死胡同里出不来，我们就不等了。
        # Python 进程退出时会强制清理掉它们。
        for i, thread in self.threads.items():
            thread.wait(50)

        self.logger.info("视频服务资源清理完成", LogCategory.VIDEO)


# 单例模式实例
_video_service_instance = None


def get_video_service() -> VideoService:
    global _video_service_instance
    if _video_service_instance is None:
        _video_service_instance = VideoService()
    return _video_service_instance
