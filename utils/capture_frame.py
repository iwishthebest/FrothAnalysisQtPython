import time
import numpy as np
import cv2
from system_logger import SystemLogger  # 导入 SystemLogger

# 创建日志管理器实例
logger = SystemLogger()


def connect_camera(rtsp_url):
    logger.add_log("monitoring", f"尝试连接相机 {rtsp_url}", "INFO")  # 添加日志
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


def capture_frame_real(i):
    rtsp_url = "rtsp://admin:fkqxk010@192.168.1.101:554/Streaming/Channels/101?tcp"

    cap = connect_camera(rtsp_url)
    retry_count = 0  # 初始化重连尝试计数器

    while True:
        ret, frame = cap.read()
        if not ret:
            logger.add_log("monitoring", "读取帧失败，尝试重新连接...", "WARNING")  # 添加日志
            cap.release()
            time.sleep(2)
            cap = connect_camera(rtsp_url)
            if not cap.isOpened():
                retry_count += 1  # 增加重连尝试计数
                logger.add_log("monitoring", f"重连失败，1秒后重试... (尝试次数: {retry_count})", "ERROR")  # 添加日志
                if retry_count >= 3:  # 如果重连尝试次数达到三次
                    logger.add_log("monitoring", "重连失败三次，取消重连", "ERROR")  # 添加日志
                    return False, None  # 返回错误信息
                time.sleep(1)
                continue
            logger.add_log("monitoring", "重连成功！", "INFO")  # 添加日志
            continue
        # 返回成功标志和帧数据
        logger.add_log("monitoring", "帧捕获成功", "INFO")  # 添加日志
        return True, frame


def capture_frame_simulate(camera_index):
    """模拟视频帧捕获 - 根据相机索引生成不同的泡沫图像"""
    try:
        width, height = 640, 480
        base_colors = [
            (100, 150, 200),  # 蓝色调 - 铅快粗泡沫
            (200, 200, 100),  # 黄色调 - 铅精一泡沫
            (150, 100, 100),  # 红色调 - 铅精二泡沫
            (100, 200, 150)  # 绿色调 - 铅精三泡沫
        ]

        frame = np.full((height, width, 3), base_colors[camera_index], dtype=np.uint8)
        noise = np.random.randint(0, 30, (height, width, 3), dtype=np.uint8)
        frame = cv2.add(frame, noise)

        if camera_index == 0:  # 铅快粗泡沫
            cv2.putText(frame, "铅快粗泡沫", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            for _ in range(30):
                x, y = np.random.randint(0, width), np.random.randint(0, height // 2)
                radius = np.random.randint(15, 30)
                cv2.circle(frame, (x, y), radius, (255, 255, 255), -1)

        elif camera_index == 1:  # 铅精一泡沫
            cv2.putText(frame, "铅精一泡沫", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            for _ in range(50):
                x, y = np.random.randint(0, width), np.random.randint(0, height // 2)
                radius = np.random.randint(8, 20)
                cv2.circle(frame, (x, y), radius, (255, 255, 255), -1)

        elif camera_index == 2:  # 铅精二泡沫
            cv2.putText(frame, "铅精二泡沫", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            for _ in range(70):
                x, y = np.random.randint(0, width), np.random.randint(0, height // 2)
                radius = np.random.randint(5, 15)
                cv2.circle(frame, (x, y), radius, (255, 255, 255), -1)

        elif camera_index == 3:  # 铅精三泡沫
            cv2.putText(frame, "铅精三泡沫", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            for _ in range(100):
                x, y = np.random.randint(0, width), np.random.randint(0, height // 2)
                radius = np.random.randint(3, 10)
                cv2.circle(frame, (x, y), radius, (255, 255, 255), -1)

        logger.add_log("monitoring", f"模拟帧捕获成功，相机索引 {camera_index}", "INFO")  # 添加日志
        return True, frame
    except Exception as e:
        logger.add_log("monitoring", f"捕获相机 {camera_index} 视频帧时出错: {e}", "ERROR")  # 添加日志
        return False, None