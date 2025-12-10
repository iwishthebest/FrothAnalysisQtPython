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
    # 信号：发送处理好的图片给UI显示 (相机索引, 图片对象)
    frame_ready = Signal(int, QImage)
    # 信号：发送状态变更 (相机索引, 状态字典)
    status_changed = Signal(int, dict)

    def __init__(self, camera_index: int, config: CameraConfig):
        super().__init__()
        self.camera_index = camera_index
        self.config = config
        self.running = False
        self.simulation_mode = False
        self.reader: Optional[RTSPStreamReader] = None
        self._mutex = QMutex()

        # 预计算显示尺寸 (从VideoFrame类中获取或固定，这里使用标准4:3)
        self.display_size = (640, 480)

    def start_work(self):
        """线程启动入口"""
        self.running = True
        self.logger = get_logging_service()

        # 初始化连接
        self._initialize_connection()

        # 开始循环
        self._capture_loop()

    def stop_work(self):
        """停止工作"""
        self.running = False

    def set_simulation_mode(self, enabled: bool):
        """切换模拟模式"""
        self.simulation_mode = enabled
        if enabled and self.reader:
            self.reader.stop()
            self.reader = None
        elif not enabled:
            # 标记为需要重连，下一次循环会处理
            pass

    def _initialize_connection(self):
        """初始化相机连接"""
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

            # 1. 获取原始帧
            if not self.config.enabled:
                frame = self._generate_simulation_frame(text="DISABLED")
                # 禁用状态下降低刷新率
                QThread.msleep(200)
            elif self.simulation_mode or self.reader is None:
                frame = self._generate_simulation_frame()
                # 尝试重连逻辑可在此处添加
            else:
                frame = self.reader.get_frame(timeout=0.1)
                if frame is None:
                    # 读取失败，可能是断线
                    frame = self._generate_simulation_frame(text="NO SIGNAL")

            # 2. 处理帧 (耗时操作都在这里做)
            if frame is not None:
                q_image = self._process_frame(frame)
                if q_image:
                    self.frame_ready.emit(self.camera_index, q_image)

            # 3. 控制帧率 (目标 30 FPS => ~33ms)
            elapsed = (time.time() - loop_start) * 1000
            sleep_time = max(1, int(33 - elapsed))
            QThread.msleep(sleep_time)

        # 退出循环后清理
        if self.reader:
            self.reader.stop()

    def _process_frame(self, frame_bgr: np.ndarray) -> Optional[QImage]:
        """图像处理流水线：缩放 -> 转色 -> QImage"""
        try:
            # A. 缩放 (显著降低后续处理和渲染开销)
            frame_resized = cv2.resize(frame_bgr, self.display_size)

            # B. 颜色转换 (BGR -> RGB)
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)

            # C. 创建 QImage
            # 注意：必须copy()，因为numpy数组在下一帧会被覆盖
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            return image.copy()

        except Exception as e:
            print(f"Frame processing error: {e}")
            return None

    def _generate_simulation_frame(self, text=None) -> np.ndarray:
        """生成模拟帧"""
        w, h = self.display_size  # 直接生成小图，省去缩放
        # 背景
        color = self.config.simulation_color
        frame = np.full((h, w, 3), color, dtype=np.uint8)

        # 噪点 (轻微)
        noise = np.random.randint(0, 20, (h, w, 3), dtype=np.uint8)
        frame = cv2.add(frame, noise)

        # 动态动画 (时间驱动)
        t = time.time()
        cx = int(w / 2 + np.sin(t) * 50)
        cy = int(h / 2 + np.cos(t) * 30)
        cv2.circle(frame, (cx, cy), 30, (255, 255, 255), -1)

        # 文字
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
    视频服务管理类 (重构版)
    负责管理多个 CameraWorker 线程
    """

    def __init__(self):
        super().__init__()
        self.logger = get_logging_service()
        self.camera_configs = config_manager.get_camera_configs()

        # 线程管理容器
        self.threads: Dict[int, QThread] = {}
        self.workers: Dict[int, CameraWorker] = {}

        self._initialize_workers()

    def _initialize_workers(self):
        """初始化所有工作线程"""
        for i, config in enumerate(self.camera_configs):
            # 1. 创建线程
            thread = QThread()

            # 2. 创建 Worker
            worker = CameraWorker(i, config)
            worker.moveToThread(thread)

            # 3. 连接信号
            # 线程启动 -> Worker 开始工作
            thread.started.connect(worker.start_work)
            # Worker 结束 -> 线程退出
            # (这里暂不自动退出线程，保持常驻直到 Service 销毁)

            # 4. 保存引用
            self.threads[i] = thread
            self.workers[i] = worker

            # 5. 启动线程
            thread.start()
            self.logger.info(f"相机线程 {i} 已启动", LogCategory.VIDEO)

    def get_worker(self, camera_index: int) -> Optional[CameraWorker]:
        """获取指定相机的 Worker (用于UI连接信号)"""
        return self.workers.get(camera_index)

    def set_simulation_mode(self, enabled: bool):
        """全局设置模拟模式"""
        for worker in self.workers.values():
            worker.set_simulation_mode(enabled)

    def cleanup(self):
        """清理资源"""
        self.logger.info("正在停止所有视频线程...", LogCategory.VIDEO)
        for i, worker in self.workers.items():
            worker.stop_work()

        for i, thread in self.threads.items():
            thread.quit()
            thread.wait(1000)  # 等待线程安全退出

        self.logger.info("视频服务资源已清理", LogCategory.VIDEO)


# 单例模式实例
_video_service_instance = None


def get_video_service() -> VideoService:
    global _video_service_instance
    if _video_service_instance is None:
        _video_service_instance = VideoService()
    return _video_service_instance
