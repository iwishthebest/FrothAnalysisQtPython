import cv2
import time
import os  # 用于处理文件目录

# 替换为你的相机RTSP地址
rtsp_url = "rtsp://admin:fkqxk010@192.168.1.101:554/Streaming/Channels/101?tcp"

# 抽帧参数设置
save_interval = 5  # 抽帧时间间隔（秒）
base_save_dir = "./data/extracted_frames_crop"  # 基础保存目录

# -------- 裁剪配置（可修改） --------
# 启用裁剪后，仅保存裁剪区域；如果禁用则保存整帧。
# 裁剪坐标为绝对像素： (left, top, width, height)
# 示例：crop_coords = (100, 50, 800, 600) 3840,2160
crop_enabled = True
# 如果你希望使用相对坐标，可改造此处为百分比（未实现）。
crop_coords = (1200, 300, 1600, 1200)
# ------------------------------------


def connect_camera(rtsp_url):
    # 不使用 CAP_PROP_RTSP_TRANSPORT，通过 URL 参数指定 TCP
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    # 限制缓冲大小（旧版本也支持此属性）
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


# 初始化变量：记录上次保存时间
last_save_time = 0  # 初始化为0，确保首次运行时会保存第一帧

cap = connect_camera(rtsp_url)
# cv2.namedWindow('Hikvision Camera', cv2.WINDOW_NORMAL)
# cv2.resizeWindow('Hikvision Camera', 800, 600)

while True:
    ret, frame = cap.read()
    if not ret:
        print("连接中断，尝试重新连接...")
        cap.release()
        time.sleep(2)
        cap = connect_camera(rtsp_url)
        if not cap.isOpened():
            print("重连失败，1秒后重试...")
            time.sleep(1)
            continue
        print("重连成功！")
        continue

    # 抽帧保存逻辑
    current_time = time.time()  # 获取当前时间戳（秒）
    if current_time - last_save_time >= save_interval:
        # 获取当前日期（用于创建子文件夹）和完整时间戳（用于文件名）
        date_str = time.strftime("%Y%m%d", time.localtime(current_time))
        timestamp = time.strftime(
            "%Y%m%d_%H%M%S", time.localtime(current_time))

        # 构建日期子文件夹路径
        date_dir = os.path.join(base_save_dir, date_str)
        # 创建日期子文件夹（如果不存在）
        if not os.path.exists(date_dir):
            os.makedirs(date_dir)
            print(f"创建日期文件夹：{date_dir}")

        # 生成图片保存路径（在日期子文件夹下）
        # 先对帧做裁剪（若启用），并确保裁剪坐标在有效范围内
        try:
            save_frame = frame
            if crop_enabled and frame is not None:
                fh, fw = frame.shape[:2]
                x, y, w, h = crop_coords
                # 边界检查并调整
                if x < 0:
                    x = 0
                if y < 0:
                    y = 0
                if w <= 0 or h <= 0:
                    # 无效尺寸，回退为整帧
                    print("裁剪尺寸无效，回退为保存整帧。")
                    save_frame = frame
                else:
                    # 限制到最大可用区域
                    if x + w > fw:
                        w = fw - x
                    if y + h > fh:
                        h = fh - y
                    # 如果调整后宽或高仍不正，回退为整帧
                    if w <= 0 or h <= 0:
                        print("裁剪区域超出边界，回退为保存整帧。")
                        save_frame = frame
                    else:
                        save_frame = frame[y:y+h, x:x+w]

            frame_path = os.path.join(date_dir, f"frame_{timestamp}.jpg")
            # 保存（裁剪后或整帧）图像
            cv2.imwrite(frame_path, save_frame)
            if crop_enabled and save_frame is not frame:
                print(f"已保存裁剪抽帧：{frame_path} (裁剪区域={crop_coords})")
            else:
                print(f"已保存抽帧：{frame_path}")
        except Exception as e:
            print(f"保存帧出错：{e}")
        # 更新上次保存时间
        last_save_time = current_time

    # 显示视频流
    # cv2.imshow('Hikvision Camera', frame)
    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #     break

cap.release()
cv2.destroyAllWindows()
