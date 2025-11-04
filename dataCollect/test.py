import cv2
import time
import os
import requests
import numpy as np

# HTTP取流配置
http_url = "http://192.168.1.101/doc/index.html#/preview"
save_interval = 5
base_save_dir = "./data/extracted_frames_crop"

# 裁剪配置
crop_enabled = True
crop_coords = (1200, 300, 1600, 1200)

last_save_time = 0

def get_frame_http():
    """通过HTTP获取单帧图片"""
    try:
        response = requests.get(http_url, auth=('admin', 'fkqxk010'), timeout=10)
        if response.status_code == 200:
            img_array = np.frombuffer(response.content, dtype=np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            return True, frame
        else:
            print(f"HTTP错误代码: {response.status_code}")
            return False, None
    except Exception as e:
        print(f"HTTP取流异常: {e}")
        return False, None

while True:
    ret, frame = get_frame_http()
    if not ret:
        print("HTTP取流失败，2秒后重试...")
        time.sleep(2)
        continue

    # 抽帧保存逻辑（与原代码相同）
    current_time = time.time()
    if current_time - last_save_time >= save_interval:
        date_str = time.strftime("%Y%m%d", time.localtime(current_time))
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime(current_time))
        
        date_dir = os.path.join(base_save_dir, date_str)
        if not os.path.exists(date_dir):
            os.makedirs(date_dir)
            print(f"创建日期文件夹：{date_dir}")

        try:
            save_frame = frame
            if crop_enabled and frame is not None:
                fh, fw = frame.shape[:2]
                x, y, w, h = crop_coords
                # 边界检查（与原代码相同）
                if x < 0: x = 0
                if y < 0: y = 0
                if w <= 0 or h <= 0:
                    save_frame = frame
                else:
                    if x + w > fw: w = fw - x
                    if y + h > fh: h = fh - y
                    if w <= 0 or h <= 0:
                        save_frame = frame
                    else:
                        save_frame = frame[y:y+h, x:x+w]

            frame_path = os.path.join(date_dir, f"frame_{timestamp}.jpg")
            cv2.imwrite(frame_path, save_frame)
            print(f"已保存HTTP抽帧：{frame_path}")
            
        except Exception as e:
            print(f"保存帧出错：{e}")
        
        last_save_time = current_time

    # 控制帧率，避免请求过快
    time.sleep(0.1)  # 每秒约10次请求