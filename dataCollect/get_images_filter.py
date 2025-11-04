import os
import cv2
import numpy as np
import time
import argparse
import logging
# 导入 RTSPStreamReader 类
from RTSPStreamReader import RTSPStreamReader

# 配置日志
log_filename = "get_images_filter.log"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加文件处理器
file_handler = logging.FileHandler(log_filename, mode='w', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)


def connect_camera(url):
    """连接相机 - 使用 RTSPStreamReader 版本"""
    try:
        # 创建 RTSPStreamReader 实例
        stream_reader = RTSPStreamReader(
            rtsp_url=url,
            reconnect_interval=5,
            max_retries=20
        )

        # 启动流读取
        if stream_reader.start():
            logger.info("RTSPStreamReader 连接成功")
            return stream_reader
        else:
            logger.error("RTSPStreamReader 启动失败")
            return None

    except Exception as e:
        logger.error(f"创建 RTSPStreamReader 失败: {e}")
        return None


def save_corrupted_frame(frame, reason, corrupted_frames_dir):
    """保存损坏的帧用于分析 - 修复中文乱码"""
    if not os.path.exists(corrupted_frames_dir):
        os.makedirs(corrupted_frames_dir)

    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())

    # 使用英文原因描述，避免中文乱码
    reason_mapping = {
        "梯度过高": "gradient_too_high",
        "梯度正常": "gradient_normal",
        "亮度过高": "brightness_too_high",
        "亮度正常": "brightness_normal",
    }

    # 将中文原因转换为英文
    clean_reason = reason_mapping.get(reason.split("(")[0], "unknown")
    if "(" in reason:
        value_part = reason.split("(")[1].split(")")[0]
        clean_reason += f"_{value_part}"

    filename = f"corrupted_{timestamp}_{clean_reason}.jpg"
    filepath = os.path.join(corrupted_frames_dir, filename)

    try:
        success, encoded_image = cv2.imencode('.jpg', frame)
        if success:
            with open(filepath, 'wb') as f:
                f.write(encoded_image.tobytes())
            logger.warning(f"⚠ 已保存损坏样本: {filename}")
        else:
            logger.error(f"图像编码失败")
    except Exception as e:
        logger.error(f"保存损坏样本失败: {e}")


def save_frame_safe(frame, filepath):
    """安全保存图像，避免中文乱码"""
    try:
        success, encoded_image = cv2.imencode('.jpg', frame)
        if success:
            with open(filepath, 'wb') as f:
                f.write(encoded_image.tobytes())
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"保存图像失败: {e}")
        return False


def check_grad_mag(frame, max_grad_thresh):
    """计算单个图像的最大梯度幅值"""
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    grad_x = cv2.Sobel(gray_frame, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray_frame, cv2.CV_64F, 0, 1, ksize=3)
    grad_mag = np.sqrt(grad_x ** 2 + grad_y ** 2)
    max_grad_mag = np.max(grad_mag)

    if max_grad_mag > max_grad_thresh:
        return False, f"梯度过高({max_grad_mag:.2f})"
    return True, f"梯度正常(梯度大值: {max_grad_mag:.2f})"


def check_bright_mag(frame, max_mean_brightness_thresh):
    """计算单个图像的最大梯度幅值"""
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray_frame)

    if mean_brightness > max_mean_brightness_thresh:
        return False, f"亮度过高({mean_brightness:.2f})"
    return True, f"亮度度正常(亮度值: {mean_brightness:.2f})"


def check_img_quality(frame, max_grad_thresh, max_mean_brightness_thresh):
    """检查图像质量"""
    is_grad_ok, grad_msg = check_grad_mag(frame, max_grad_thresh)
    if not is_grad_ok:
        return False, grad_msg
    is_bright_ok, bright_msg = check_bright_mag(frame, max_mean_brightness_thresh)
    if not is_bright_ok:
        return False, bright_msg

    return True, f"图像质量正常"


def safe_crop_frame(frame, coords, crop_enabled):
    """安全的图像裁剪，包含边界检查"""
    if frame is None or not crop_enabled:
        return frame

    try:
        fh, fw = frame.shape[:2]
        x, y, w, h = coords

        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if w <= 0 or h <= 0:
            return frame

        if x + w > fw:
            w = fw - x
        if y + h > fh:
            h = fh - y

        if w <= 0 or h <= 0:
            return frame

        return frame[y:y + h, x:x + w]

    except Exception as e:
        logger.error(f"裁剪出错: {e}, 返回原帧")
        return frame


def main(rtsp_url, save_interval, base_save_dir, max_grad_thresh, max_mean_brightness_thresh,
         max_consecutive_bad_frames, save_corrupted_for_analysis, corrupted_frames_dir, crop_enabled, crop_coords):
    """主函数"""
    os.makedirs(base_save_dir, exist_ok=True)
    if save_corrupted_for_analysis:
        os.makedirs(corrupted_frames_dir, exist_ok=True)

    last_save_time = 0
    consecutive_bad_frames = 0
    stream_reader = None

    logger.info("开始相机监控...")
    logger.info(f"抽帧间隔: {save_interval}秒")
    logger.info(f"保存目录: {base_save_dir}")
    logger.info(f"裁剪启用: {crop_enabled}, 坐标: {crop_coords}")

    while True:
        try:
            if stream_reader is None or not stream_reader.is_running:
                logger.info("正在连接相机...")
                stream_reader = connect_camera(rtsp_url)
                if stream_reader is None:
                    logger.error("连接失败，1秒后重试...")
                    time.sleep(1)
                    continue
                logger.info("相机连接成功!")
                consecutive_bad_frames = 0

            # 使用 RTSPStreamReader 获取帧
            frame = stream_reader.get_frame(timeout=2)
            if frame is None:
                logger.error("获取帧失败或超时，尝试重新连接...")
                if stream_reader is not None:
                    stream_reader.stop()
                stream_reader = None
                time.sleep(1)
                continue

            current_time = time.time()
            if current_time - last_save_time >= save_interval:
                crop_frame = safe_crop_frame(frame, crop_coords, crop_enabled)
                is_quality_ok, quality_msg = check_img_quality(crop_frame, max_grad_thresh, max_mean_brightness_thresh)
                if not is_quality_ok:
                    consecutive_bad_frames += 1
                    logger.warning(f"✗✗ 图像损坏，跳过保存: {quality_msg}")

                    if save_corrupted_for_analysis:
                        save_corrupted_frame(crop_frame, quality_msg, corrupted_frames_dir)

                    last_save_time = current_time
                    continue

                consecutive_bad_frames = 0

                date_str = time.strftime("%Y%m%d", time.localtime(current_time))
                timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime(current_time))

                date_dir = os.path.join(base_save_dir, date_str)
                os.makedirs(date_dir, exist_ok=True)

                frame_path = os.path.join(date_dir, f"frame_{timestamp}.jpg")

                if save_frame_safe(crop_frame, frame_path):
                    crop_status = "(已裁剪)" if crop_frame is not frame else "(原图)"
                    logger.info(f"已保存正常帧: {frame_path} {crop_status} - {quality_msg}")
                else:
                    logger.error(f"✗✗ 保存帧失败: {frame_path}")

                last_save_time = current_time

                if consecutive_bad_frames >= max_consecutive_bad_frames:
                    logger.warning(f"⚠ 连续{consecutive_bad_frames}帧损坏，重新连接相机...")
                    if stream_reader is not None:
                        stream_reader.stop()
                        stream_reader = None
                    consecutive_bad_frames = 0
                    time.sleep(2)

            time.sleep(0.01)

        except KeyboardInterrupt:
            logger.info("\n用户中断，退出程序...")
            break
        except Exception as e:
            logger.error(f"程序异常: {e}")
            if stream_reader is not None:
                stream_reader.stop()
                stream_reader = None
            time.sleep(2)

    # 清理资源
    if stream_reader is not None:
        stream_reader.stop()
    cv2.destroyAllWindows()
    logger.info("程序已退出")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Image Filter Script")
    parser.add_argument('--rtsp-url', type=str,
                        default="rtsp://admin:fkqxk010@192.168.1.101:554/Streaming/Channels/101?tcp",
                        help="RTSP URL of the camera")
    parser.add_argument('--save-interval', type=int, default=5, help="Save interval in seconds")
    parser.add_argument('--base-save-dir', type=str, default="./data/extracted_frames_check",
                        help="Base directory to save frames")
    parser.add_argument('--max-grad-thresh', type=int, default=800, help="Maximum gradient threshold")
    parser.add_argument('--max-mean-brightness-thresh', type=int, default=160, help="Maximum mean brightness threshold")
    parser.add_argument('--max-consecutive-bad-frames', type=int, default=5,
                        help="Maximum consecutive bad frames before reconnecting")
    parser.add_argument('--save-corrupted-for-analysis', action='store_true', help="Save corrupted frames for analysis")
    parser.add_argument('--corrupted-frames-dir', type=str, default="./data/corrupted_frames",
                        help="Directory to save corrupted frames")
    parser.add_argument('--crop-enabled', action='store_true', help="Enable cropping")
    parser.add_argument('--crop-coords', type=str, default="1200,300,1600,1200", help="Crop coordinates (x, y, w, h)")

    args = parser.parse_args()

    rtsp_url = args.rtsp_url
    save_interval = args.save_interval
    base_save_dir = args.base_save_dir
    max_grad_thresh = args.max_grad_thresh
    max_mean_brightness_thresh = args.max_mean_brightness_thresh
    max_consecutive_bad_frames = args.max_consecutive_bad_frames
    save_corrupted_for_analysis = args.save_corrupted_for_analysis
    corrupted_frames_dir = args.corrupted_frames_dir
    crop_enabled = args.crop_enabled
    crop_coords = tuple(map(int, args.crop_coords.split(',')))

    stream_reader = None  # 确保变量在全局作用域

    try:
        main(rtsp_url, save_interval, base_save_dir, max_grad_thresh, max_mean_brightness_thresh,
             max_consecutive_bad_frames, save_corrupted_for_analysis, corrupted_frames_dir, crop_enabled, crop_coords)
    except KeyboardInterrupt:
        logger.info("\n程序已手动停止")
    except Exception as e:
        logger.error(f"程序异常终止：{e}")
    finally:
        # 确保程序退出时释放资源
        if 'stream_reader' in globals() and stream_reader is not None:
            stream_reader.stop()
