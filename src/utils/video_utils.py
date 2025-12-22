import cv2
import time
import logging
import threading
from queue import Queue, Empty


class RTSPStreamReader:
    def __init__(self, rtsp_url, window_size=(640, 480), reconnect_interval=5, max_retries=10):
        self.thread = None
        self.rtsp_url = rtsp_url
        self.window_size = window_size  # (width, height)
        self.reconnect_interval = reconnect_interval
        self.max_retries = max_retries
        self.retry_count = 0
        self.is_running = False
        self.cap = None
        self.frame_queue = Queue(maxsize=1)

    def _connect(self):
        """建立RTSP连接"""
        try:
            self.cap = cv2.VideoCapture(self.rtsp_url)

            # 设置连接和读取超时 (部分后端支持)
            self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
            self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)

            if not self.cap.isOpened():
                return False

            ret, frame = self.cap.read()
            if not ret:
                return False

            self.retry_count = 0
            return True

        except Exception as e:
            print(f"连接异常: {e}")
            return False

    def _read_frames(self):
        """读取帧并调整大小 (独立线程)"""
        try:
            while self.is_running:
                try:
                    if self.cap is None or not self.cap.isOpened():
                        if not self._reconnect():
                            break
                        continue

                    # 这里可能会阻塞，直到超时或读到帧
                    ret, frame = self.cap.read()

                    if not ret:
                        # 读取失败，短暂休眠后重试或重连
                        if self.cap:
                            self.cap.release()
                            self.cap = None
                        time.sleep(1)
                        continue

                    # 调整帧大小
                    if frame is not None and self.window_size:
                        frame = cv2.resize(frame, self.window_size, interpolation=cv2.INTER_LINEAR)

                    # 将帧放入队列 (非阻塞替换旧帧)
                    if not self.frame_queue.empty():
                        try:
                            self.frame_queue.get_nowait()
                        except Empty:
                            pass
                    self.frame_queue.put(frame)

                except Exception as e:
                    # print(f"读取帧异常: {e}")
                    if self.cap:
                        self.cap.release()
                        self.cap = None
                    time.sleep(1)
        finally:
            # [核心修复] 资源释放必须在读取线程内部完成
            # 当 is_running 置为 False 后，循环结束，线程自然走到这里释放资源
            # 这样避免了外部线程调用 release() 导致的 GIL 死锁
            if self.cap:
                try:
                    self.cap.release()
                except:
                    pass
                self.cap = None
            # print("RTSP资源已安全释放")

    def _reconnect(self):
        """重连机制"""
        if self.retry_count >= self.max_retries:
            return False
        self.retry_count += 1
        # 在重连等待期间也要响应停止信号
        for _ in range(self.reconnect_interval):
            if not self.is_running: return False
            time.sleep(1)
        return self._connect()

    def get_frame(self, timeout=2):
        """获取最新帧"""
        try:
            return self.frame_queue.get(timeout=timeout)
        except Empty:
            return None

    def start(self):
        """启动流读取"""
        if self.is_running:
            return False

        if not self._connect():
            return False

        self.is_running = True
        self.thread = threading.Thread(target=self._read_frames, daemon=True)
        self.thread.start()
        return True

    def stop(self):
        """停止流读取 (非阻塞)"""
        # [核心修复] 只设置标志位，不调用 release()
        # 释放操作交由 _read_frames 的 finally 块处理
        self.is_running = False

        # 不等待线程结束 (join)，也不调用 release，确保 UI 线程瞬间返回