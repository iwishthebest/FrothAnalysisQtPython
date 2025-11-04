import csv
import re
import time
import numpy as np
import cv2
import requests
import snap7
from snap7 import util

from system_logger import SystemLogger  # 导入 SystemLogger

# 创建日志管理器实例
logger = SystemLogger()

# Constants for Camera
BUFFER_SIZE = 1
TIMEOUT_MS = 3000
RTSP_URL = ["rtsp://admin:fkqxk010@192.168.1.101:554/Streaming/Channels/101",
            "rtsp://admin:fkqxk010@192.168.1.101:554/Streaming/Channels/101",
            "rtsp://admin:fkqxk010@192.168.1.101:554/Streaming/Channels/101",
            "rtsp://admin:fkqxk010@192.168.1.101:554/Streaming/Channels/101"]
MAX_RETRY_COUNT = 3
RETRY_DELAY = 2

# Constants for OPC data
OPC_URL = "http://10.12.18.2:8081/open/realdata/snapshot/batchGet"
TAG_LIST = ["KYFX.kyfx_gqxk_grade_Pb", "KYFX.kyfx_gqxk_grade_Zn"]
TAG_LIST_FILE = "src/tagList.csv"


def connect_camera(rtsp_url):
    logger.add_log(f"尝试连接相机 {rtsp_url}", "INFO")
    camera_capture = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    camera_capture.set(cv2.CAP_PROP_BUFFERSIZE, BUFFER_SIZE)
    return camera_capture


def retry_connection(rtsp_url):
    retry_count = 0
    while retry_count < MAX_RETRY_COUNT:
        camera_capture = connect_camera(rtsp_url)
        if camera_capture.isOpened():
            logger.add_log("重连成功！", "INFO")
            return camera_capture
        else:
            logger.add_log(f"重连失败，{RETRY_DELAY}秒后重试... (尝试次数: {retry_count + 1})", "ERROR")
            time.sleep(RETRY_DELAY)
            retry_count += 1
    logger.add_log("重连失败三次，取消重连", "ERROR")
    return None


def capture_frame_real(i):
    cap = connect_camera(RTSP_URL[i])

    ret, frame = cap.read()
    if not ret:
        logger.add_log("读取帧失败，尝试重新连接...", "WARNING")
        cap.release()
        cap = retry_connection(RTSP_URL[i])
        if cap is None:
            return False, None
    logger.add_log("帧捕获成功", "INFO")
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
        bubble_counts = [30, 50, 70, 100]
        bubble_radius_ranges = [(15, 30), (8, 20), (5, 15), (3, 10)]
        labels = ["铅快粗泡沫", "铅精一泡沫", "铅精二泡沫", "铅精三泡沫"]

        frame = np.full((height, width, 3), base_colors[camera_index], dtype=np.uint8)
        noise = np.random.randint(0, 30, (height, width, 3), dtype=np.uint8)
        frame = cv2.add(frame, noise)

        cv2.putText(frame, labels[camera_index], (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        for _ in range(bubble_counts[camera_index]):
            x, y = np.random.randint(0, width), np.random.randint(0, height // 2)
            radius = np.random.randint(*bubble_radius_ranges[camera_index])
            cv2.circle(frame, (x, y), radius, (255, 255, 255), -1)

        # logger.add_log(f"模拟帧捕获成功，相机索引 {camera_index}", "INFO")
        return frame
    except Exception as e:
        logger.add_log(f"捕获相机 {camera_index} 视频帧时出错: {e}", "ERROR")
        return None


def get_tag_list():
    """从CSV文件获取标签列表"""
    tag_list = []
    try:
        with open(TAG_LIST_FILE, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row_num, row in enumerate(reader, 1):
                if row:  # 跳过空行
                    cleaned_line = re.sub(r'[\[\]]', '', row[0])
                    with_prefix = add_prefix(cleaned_line.strip())
                    tag_list.append(with_prefix)
        # print(f"已加载 {len(tag_list)} 个标签")
    except Exception as e:
        logger.error(f"读取标签列表失败: {e}")
    return tag_list


def add_prefix(tag_name):
    """为标签添加前缀"""
    if tag_name.startswith('yj_'):
        return f'YJ.{tag_name}'
    elif tag_name.startswith('kyfx_'):
        return f'KYFX.{tag_name}'
    return tag_name


def get_process_data():
    url = OPC_URL
    tag_list = get_tag_list()
    tag_param = ",".join(tag_list)
    try:
        params = {"tagNameList": tag_param}
        response = requests.get(url=url, params=params, timeout=10)
        values = {}
        if response.status_code == 200:
            data = response.json()
            for item in data.get("data", []):
                tag_name = item['TagName'].strip()
                value = float(item['Value'])
                time = item['Time']
                values[tag_name] = value
        else:
            logger.add_log(f"请求失败，状态码：{response.status_code}", "ERROR")
            return False
    except Exception as e:
        logger.add_log(f"采集异常：{e}", "ERROR")
        return False
    return values


def get_plc_data():
    # 创建客户端并连接
    plc = snap7.client.Client()
    plc.set_connection_type(3)  # 对于200SMART，必须设置连接类型为3

    try:
        plc.connect('192.168.0.21', 0, 1)  # 参数：IP地址, 机架号, 槽号
        logger.add_log("PLC连接成功", "INFO")
    except Exception as e:
        logger.add_log(f"连接失败: {e}", "ERROR")
        return False

    # 读取布尔值（例如 V0.0）
    bool_data = plc.db_read(1, 0, 1)  # 读取DB1，起始地址0，长度为1字节
    value_bool = util.get_bool(bool_data, 0, 0)  # 从第0字节的第0位解析出布尔值
    logger.add_log(f"V0.0的状态: {value_bool}", "INFO")

    # 读取过程输入映像区（Area ID=0x81）从偏移量34开始的一个字（2字节）
    data = plc.read_area(snap7.type.Areas.PE, 0, 34, 2)
    value = int.from_bytes(data, byteorder='big')  # 可能需要根据实际情况调整字节序
    logger.add_log(f"AIW34的原始值为: {value}", "INFO")

    return True
