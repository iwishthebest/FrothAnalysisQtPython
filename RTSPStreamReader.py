import cv2
import time
import logging
import threading
from queue import Queue, Empty


class RTSPStreamReader:
    def __init__(self, rtsp_url, window_size=(640, 480), reconnect_interval=5, max_retries=10):
        self.rtsp_url = rtsp_url
        self.window_size = window_size  # (width, height)
        self.reconnect_interval = reconnect_interval
        self.max_retries = max_retries
        self.retry_count = 0
        self.is_running = False
        self.cap = None
        self.frame_queue = Queue(maxsize=1)
        self.logger = self._setup_logger()

    def _setup_logger(self):
        logger = logging.getLogger('RTSP_Reader')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _connect(self):
        """建立RTSP连接"""
        try:
            self.cap = cv2.VideoCapture(self.rtsp_url)

            # 设置连接和读取超时
            self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
            self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)

            if not self.cap.isOpened():
                self.logger.error("无法打开RTSP流")
                return False

            # 测试读取一帧
            ret, frame = self.cap.read()
            if not ret:
                self.logger.error("无法从RTSP流读取帧")
                return False

            self.retry_count = 0
            self.logger.info("RTSP连接成功")
            return True

        except Exception as e:
            self.logger.error(f"连接异常: {e}")
            return False

    def _read_frames(self):
        """读取帧并调整大小"""
        while self.is_running:
            try:
                if self.cap is None or not self.cap.isOpened():
                    self.logger.warning("连接断开，尝试重连...")
                    if not self._reconnect():
                        break
                    continue

                ret, frame = self.cap.read()

                if not ret:
                    self.logger.warning("读取帧失败，连接可能已断开")
                    self.cap.release()
                    self.cap = None
                    continue

                # 调整帧大小
                if frame is not None and self.window_size:
                    frame = cv2.resize(frame, self.window_size, interpolation=cv2.INTER_LINEAR)

                # 将帧放入队列
                if not self.frame_queue.empty():
                    try:
                        self.frame_queue.get_nowait()
                    except Empty:
                        pass
                self.frame_queue.put(frame)

            except Exception as e:
                self.logger.error(f"读取帧时发生异常: {e}")
                if self.cap:
                    self.cap.release()
                    self.cap = None
                time.sleep(1)

    def _reconnect(self):
        """重连机制"""
        if self.retry_count >= self.max_retries:
            self.logger.error("达到最大重试次数，停止重连")
            return False

        self.retry_count += 1
        self.logger.info(f"尝试重连 ({self.retry_count}/{self.max_retries})")

        time.sleep(self.reconnect_interval)
        return self._connect()

    def get_frame(self, timeout=2):
        """获取最新帧"""
        try:
            return self.frame_queue.get(timeout=timeout)
        except Empty:
            return None

    def set_window_size(self, width, height):
        """动态设置窗口大小"""
        self.window_size = (width, height)
        self.logger.info(f"窗口大小设置为: {width}x{height}")

    def start(self):
        """启动流读取"""
        if self.is_running:
            self.logger.warning("流读取已在运行中")
            return False

        if not self._connect():
            self.logger.error("初始连接失败")
            return False

        self.is_running = True
        self.thread = threading.Thread(target=self._read_frames, daemon=True)
        self.thread.start()
        self.logger.info("RTSP流读取已启动")
        return True

    def stop(self):
        """停止流读取"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        self.logger.info("RTSP流读取已停止")

# 使用示例
def main():
    # RTSP URL示例
    rtsp_url = "rtsp://admin:fkqxk010@192.168.1.101:554/Streaming/Channels/101"

    # 创建流读取器
    stream_reader = RTSPStreamReader(
        rtsp_url=rtsp_url,
        reconnect_interval=5,  # 重连间隔5秒
        max_retries=20  # 最大重试次数
    )

    try:
        cv2.namedWindow('RTSP Stream')
        cv2.resizeWindow('RTSP Stream', 800, 600)
        # 启动流读取
        if stream_reader.start():
            while True:
                # 获取帧
                frame = stream_reader.get_frame()
                if frame is not None:
                    # 处理帧（这里只是显示）
                    cv2.imshow('RTSP Stream', frame)

                # 按'q'退出
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    except KeyboardInterrupt:
        print("用户中断")
    finally:
        stream_reader.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()