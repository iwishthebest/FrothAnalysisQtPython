import cv2
import time
import os
import numpy as np
from scipy import ndimage

# 替换为你的相机RTSP地址
rtsp_url = "rtsp://admin:fkqxk010@192.168.1.101:554/Streaming/Channels/101?tcp"

# 抽帧参数设置
save_interval = 5  # 抽帧时间间隔（秒）
base_save_dir = "./data/extracted_frames_check"

# 图像质量检测参数
MIN_VARIANCE = 20.0  # 最小方差阈值（检测模糊）
MIN_BRIGHTNESS = 15  # 最小亮度阈值
MAX_BRIGHTNESS = 245  # 最大亮度阈值

# 损坏检测参数
MAX_CONSECUTIVE_BAD_FRAMES = 5  # 最大连续损坏帧数
SAVE_CORRUPTED_FOR_ANALYSIS = True  # 是否保存损坏帧用于分析
CORRUPTED_FRAMES_DIR = "./data/corrupted_frames"  # 损坏帧保存目录

# -------- 裁剪配置 --------
crop_enabled = True
crop_coords = (1200, 300, 1600, 1200)


# ------------------------------------


def connect_camera(rtsp_url):
    """连接相机"""
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


def is_frame_valid_basic(frame):
    """基础帧有效性检查"""
    if frame is None:
        return False, "帧为空"

    height, width = frame.shape[:2]
    if height <= 10 or width <= 10:
        return False, f"帧尺寸过小: {width}x{height}"

    if frame.size == 0:
        return False, "帧数据为空"

    return True, "基础检查通过"


def check_image_quality(frame):
    """图像质量检查"""
    try:
        # 转换为灰度图
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        # 检查方差（模糊检测）
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        if variance < MIN_VARIANCE:
            return False, f"图像模糊，方差: {variance:.2f}"

        # 检查亮度
        avg_brightness = cv2.mean(gray)[0]
        if avg_brightness < MIN_BRIGHTNESS or avg_brightness > MAX_BRIGHTNESS:
            return False, f"亮度异常: {avg_brightness:.2f}"

        return True, f"质量正常(方差: {variance:.2f}, 亮度: {avg_brightness:.2f})"

    except Exception as e:
        return False, f"质量检查出错: {str(e)}"


def detect_image_tearing(gray_frame):
    """检测图像撕裂"""
    height, width = gray_frame.shape

    # 检测水平方向的突然跳变
    row_std = np.std(gray_frame, axis=1)
    if len(row_std) > 1:
        row_diff = np.abs(np.diff(row_std))
        if np.max(row_diff) > np.mean(row_std) * 3:
            return True, "检测到水平撕裂"

    # 检测垂直线性异常
    col_std = np.std(gray_frame, axis=0)
    if len(col_std) > 1:
        col_diff = np.abs(np.diff(col_std))
        if np.max(col_diff) > np.mean(col_std) * 3:
            return True, "检测到垂直撕裂"

    # 边缘连续性分析
    edges = cv2.Canny(gray_frame, 50, 150)
    horizontal_edges = np.sum(edges, axis=1)
    edge_gaps = np.where(horizontal_edges == 0)[0]

    if len(edge_gaps) > 1:
        gap_lengths = np.diff(edge_gaps)
        if len(gap_lengths) > 0 and np.max(gap_lengths) > height * 0.1:
            return True, "检测到边缘不连续"

    return False, "无撕裂"


def detect_compression_artifacts(gray_frame, block_size=8):
    """检测压缩伪影（块效应）"""
    height, width = gray_frame.shape

    block_artifacts = 0
    total_blocks = 0
    max_value = 0

    for i in range(block_size, height - block_size, block_size):
        for j in range(block_size, width - block_size, block_size):
            total_blocks += 1
            # 检查块边界的不连续性
            if i + block_size < height and j + block_size < width:
                # 水平边界
                top_block = gray_frame[i - block_size:i, j:j + block_size]
                bottom_block = gray_frame[i:i + block_size, j:j + block_size]
                if top_block.size > 0 and bottom_block.size > 0:
                    diff = np.abs(np.mean(top_block) - np.mean(bottom_block))
                    if diff > max_value:
                        max_value = diff
                    if diff > 1000:  # 阈值可调整
                        block_artifacts += 1

    if total_blocks > 0 and block_artifacts / total_blocks > 0.1:
        return True, f"检测到压缩伪影: {block_artifacts}处"

    return False, "无压缩伪影"


def calculate_texture_features(gray_frame):
    """计算纹理特征"""
    # 计算梯度特征
    grad_x = cv2.Sobel(gray_frame, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray_frame, cv2.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

    # 计算灰度直方图特征
    hist = cv2.calcHist([gray_frame], [0], None, [64], [0, 256])
    hist = hist.flatten() / hist.sum()  # 归一化
    hist_entropy = -np.sum(hist * np.log(hist + 1e-8))

    return {
        'grad_max': np.max(gradient_magnitude),
        'grad_mean': np.mean(gradient_magnitude),
        'grad_std': np.std(gradient_magnitude),
        'hist_entropy': hist_entropy
    }


def detect_texture_anomaly(gray_frame):
    """检测纹理异常"""
    try:
        features = calculate_texture_features(gray_frame)

        # 泡沫纹理的典型特征：适中的梯度值和熵值
        grad_max = features['grad_max']
        hist_entropy = features['hist_entropy']

        # 异常纹理检测规则
        anomalies = []

        # 梯度异常（过低或过高）
        if grad_max < 5:
            anomalies.append(f"梯度过低({grad_max:.2f})")
        elif grad_max > 725:
            anomalies.append(f"梯度过高({grad_max:.2f})")

        # 直方图熵异常（分布异常）
        if hist_entropy < 1.5:
            anomalies.append(f"纹理过简({hist_entropy:.2f})")
        elif hist_entropy > 5.0:
            anomalies.append(f"纹理过杂({hist_entropy:.2f})")

        if anomalies:
            return True, "纹理异常: " + ", ".join(anomalies)

        return False, f"纹理正常(梯度大值: {grad_max:.2f}, 熵: {hist_entropy:.2f})"

    except Exception as e:
        return False, f"纹理检查出错: {str(e)}"


def detect_color_anomaly(color_frame):
    """检测色彩异常"""
    if len(color_frame.shape) != 3:
        return False, "非彩色图像"

    try:
        b, g, r = cv2.split(color_frame.astype(np.float32))

        # 检查通道相关性
        bg_corr = np.corrcoef(b.flatten(), g.flatten())[0, 1]
        gr_corr = np.corrcoef(g.flatten(), r.flatten())[0, 1]

        if bg_corr < 0.7 or gr_corr < 0.7:
            return True, f"色彩通道相关性低(B-G: {bg_corr:.2f}, G-R: {gr_corr:.2f})"

        # 检查色彩饱和度
        hsv = cv2.cvtColor(color_frame, cv2.COLOR_BGR2HSV)
        saturation = hsv[:, :, 1]
        avg_saturation = np.mean(saturation)

        if avg_saturation < 10:
            return True, f"饱和度过低: {avg_saturation:.2f}"
        elif avg_saturation > 200:
            return True, f"饱和度过高: {avg_saturation:.2f}"

        return False, "色彩正常"

    except Exception as e:
        return False, f"色彩检查出错: {str(e)}"


def is_frame_corrupted(frame):
    """综合检测图像是否损坏"""
    # 1. 基础检查
    is_valid, valid_msg = is_frame_valid_basic(frame)
    if not is_valid:
        return True, valid_msg

    # 2. 转换为灰度图用于后续检测
    if len(frame.shape) == 3:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame

    # 3. 检测图像撕裂
    is_torn, tear_msg = detect_image_tearing(gray)
    if is_torn:
        return True, tear_msg

    # 4. 检测压缩伪影
    # has_artifacts, artifact_msg = detect_compression_artifacts(gray)
    # if has_artifacts:
    #     return True, artifact_msg

    # 5. 检测纹理异常
    texture_anomaly, texture_msg = detect_texture_anomaly(gray)
    if texture_anomaly:
        return True, texture_msg

    # 6. 检测色彩异常（如果是彩色图像）
    if len(frame.shape) == 3:
        color_anomaly, color_msg = detect_color_anomaly(frame)
        if color_anomaly:
            return True, color_msg

    return False, "图像完好"


def save_corrupted_frame(frame, reason):
    """保存损坏的帧用于分析"""
    if not os.path.exists(CORRUPTED_FRAMES_DIR):
        os.makedirs(CORRUPTED_FRAMES_DIR)

    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    # 清理原因字符串，移除特殊字符
    clean_reason = "".join(c if c.isalnum() else "_" for c in reason[:30])
    filename = f"corrupted_{timestamp}_{clean_reason}.jpg"
    filepath = os.path.join(CORRUPTED_FRAMES_DIR, filename)

    try:
        cv2.imwrite(filepath, frame)
        print(f"⚠ 已保存损坏样本: {filename}")
    except Exception as e:
        print(f"保存损坏样本失败: {e}")


def safe_crop_frame(frame, crop_coords):
    """安全的图像裁剪，包含边界检查"""
    if frame is None or not crop_enabled:
        return frame

    try:
        fh, fw = frame.shape[:2]
        x, y, w, h = crop_coords

        # 边界检查
        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if w <= 0 or h <= 0:
            return frame

        # 限制到最大可用区域
        if x + w > fw:
            w = fw - x
        if y + h > fh:
            h = fh - y

        # 如果调整后宽或高仍不正，返回原帧
        if w <= 0 or h <= 0:
            return frame

        return frame[y:y + h, x:x + w]

    except Exception as e:
        print(f"裁剪出错: {e}, 返回原帧")
        return frame


def main():
    """主函数"""
    # 创建必要的目录
    os.makedirs(base_save_dir, exist_ok=True)
    if SAVE_CORRUPTED_FOR_ANALYSIS:
        os.makedirs(CORRUPTED_FRAMES_DIR, exist_ok=True)

    # 初始化变量
    last_save_time = 0
    consecutive_bad_frames = 0
    cap = None

    print("开始相机监控...")
    print(f"抽帧间隔: {save_interval}秒")
    print(f"保存目录: {base_save_dir}")
    print(f"裁剪启用: {crop_enabled}, 坐标: {crop_coords}")

    while True:
        try:
            # 连接相机（如果未连接）
            if cap is None or not cap.isOpened():
                print("正在连接相机...")
                cap = connect_camera(rtsp_url)
                if not cap.isOpened():
                    print("连接失败，5秒后重试...")
                    time.sleep(5)
                    continue
                print("相机连接成功!")
                consecutive_bad_frames = 0  # 重置计数器

            # 读取帧
            ret, frame = cap.read()
            # frame = cv2.imread(r'D:\dataCollect\data\extracted_frames_crop\20251029\frame_20251029_000013.jpg')
            if not ret:
                print("读取帧失败，尝试重新连接...")
                cap.release()
                cap = None
                time.sleep(2)
                continue

            # 抽帧保存逻辑
            current_time = time.time()
            if current_time - last_save_time >= save_interval:
                # 检查图像质量
                is_quality_ok, quality_msg = check_image_quality(frame)

                if is_quality_ok:
                    # 检查图像是否损坏
                    is_corrupted, corrupt_msg = is_frame_corrupted(frame)

                    if not is_corrupted:
                        # 图像完好，进行保存
                        consecutive_bad_frames = 0  # 重置连续损坏计数

                        try:
                            # 裁剪处理
                            save_frame = safe_crop_frame(frame, crop_coords)

                            # 构建保存路径
                            date_str = time.strftime(
                                "%Y%m%d", time.localtime(current_time))
                            timestamp = time.strftime(
                                "%Y%m%d_%H%M%S", time.localtime(current_time))

                            date_dir = os.path.join(base_save_dir, date_str)
                            os.makedirs(date_dir, exist_ok=True)

                            frame_path = os.path.join(
                                date_dir, f"frame_{timestamp}.jpg")
                            cv2.imwrite(frame_path, save_frame)

                            crop_status = "(已裁剪)" if save_frame is not frame else "(原图)"
                            print(
                                f"✓ 已保存正常帧: {frame_path} {crop_status} - {quality_msg}")
                            last_save_time = current_time

                        except Exception as e:
                            print(f"✗ 保存帧出错: {e}")
                            last_save_time = current_time
                    else:
                        # 图像损坏
                        consecutive_bad_frames += 1
                        print(f"✗ 图像损坏，跳过保存: {corrupt_msg}")

                        if SAVE_CORRUPTED_FOR_ANALYSIS:
                            save_corrupted_frame(frame, corrupt_msg)

                        last_save_time = current_time
                else:
                    # 图像质量差
                    consecutive_bad_frames += 1
                    print(f"⚠ 图像质量差，跳过保存: {quality_msg}")
                    last_save_time = current_time

                # 检查连续损坏帧数，可能需要重新连接
                if consecutive_bad_frames >= MAX_CONSECUTIVE_BAD_FRAMES:
                    print(f"⚠ 连续{consecutive_bad_frames}帧损坏，重新连接相机...")
                    if cap is not None:
                        cap.release()
                        cap = None
                    consecutive_bad_frames = 0
                    time.sleep(2)

            # 短暂休眠以减少CPU占用
            time.sleep(0.01)

        except KeyboardInterrupt:
            print("\n用户中断，退出程序...")
            break
        except Exception as e:
            print(f"程序异常: {e}")
            if cap is not None:
                cap.release()
                cap = None
            time.sleep(2)

    # 清理资源
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()
    print("程序已退出")


if __name__ == "__main__":
    main()
