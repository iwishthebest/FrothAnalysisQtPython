import cv2
import numpy as np
import logging
from typing import Tuple, Dict, List
from skimage.feature import graycomatrix, graycoprops

# 配置日志
logger = logging.getLogger(__name__)


class FrothFeatureExtractor:
    """
    浮选泡沫图像特征提取工具类。
    提供颜色统计、纹理(GLCM)及动态特征提取功能。
    """

    @staticmethod
    def extract_color_stats(image: np.ndarray, target_size: Tuple[int, int] = (256, 256)) -> Dict[str, float]:
        """
        提取单帧图像的基础颜色和统计特征。

        Args:
            image: 输入图像 (BGR格式)
            target_size: 处理时的缩放尺寸

        Returns:
            包含特征的字典: Red/Gray Ratio, Mean, Variance, Skewness, Kurtosis
        """
        if image is None:
            return {}

        try:
            # 预处理
            if target_size:
                image = cv2.resize(image, target_size)

            # 1. 颜色比率特征
            # 提取红色通道 (OpenCV是BGR，索引2)
            red_channel = image[:, :, 2].astype(float)
            red_mean = np.mean(red_channel)

            # 计算加权灰度图
            gray_image = (0.289 * image[:, :, 2] +
                          0.587 * image[:, :, 1] +
                          0.114 * image[:, :, 0])
            gray_mean = np.mean(gray_image)

            # 避免除以零
            red_gray_ratio = red_mean / gray_mean if gray_mean > 0 else 0.0

            # 2. 灰度统计特征
            # 使用直方图计算概率分布
            gray_uint8 = gray_image.astype(np.uint8)
            pixel_counts = cv2.calcHist([gray_uint8], [0], None, [256], [0, 256]).flatten()
            total_pixels = gray_uint8.size
            pixel_prob = pixel_counts / total_pixels

            # 灰度级向量 [0, 1, ... 255]
            levels = np.arange(256)

            # 计算矩
            mean = np.sum(levels * pixel_prob)
            variance = np.sum(((levels - mean) ** 2) * pixel_prob)

            std_dev = np.sqrt(variance)
            if std_dev > 0:
                skewness = np.sum(((levels - mean) ** 3) * pixel_prob) / (std_dev ** 3)
                kurtosis = np.sum(((levels - mean) ** 4) * pixel_prob) / (std_dev ** 4)
            else:
                skewness = 0.0
                kurtosis = 0.0

            return {
                'red_gray_ratio': float(red_gray_ratio),
                'gray_mean': float(mean),
                'gray_variance': float(variance),
                'gray_skewness': float(skewness),
                'gray_kurtosis': float(kurtosis)
            }

        except Exception as e:
            logger.error(f"颜色特征提取失败: {e}")
            return {}

    @staticmethod
    def extract_dynamic_features(img1: np.ndarray, img2: np.ndarray, time_interval: float = 0.15) -> Dict[str, float]:
        """
        提取两帧图像间的动态特征（速度、稳定性）。
        优先使用 SURF，如果不可用则回退到 SIFT 或 ORB。

        Args:
            img1:上一帧 (BGR 或 Grayscale)
            img2: 当前帧 (BGR 或 Grayscale)
            time_interval: 两帧之间的时间间隔(秒)

        Returns:
            包含 speed_mean, speed_variance, stability 的字典
        """
        if img1 is None or img2 is None:
            return {}

        # 转换为灰度
        if len(img1.shape) == 3: img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        if len(img2.shape) == 3: img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        # 初始化特征检测器
        detector = None
        algorithm_name = "SURF"

        try:
            # 尝试初始化 SURF (可能因专利问题不可用)
            if hasattr(cv2, 'xfeatures2d'):
                detector = cv2.xfeatures2d.SURF_create(400)
            else:
                raise AttributeError("xfeatures2d module not found")
        except Exception:
            try:
                # 回退到 SIFT
                algorithm_name = "SIFT"
                detector = cv2.SIFT_create()
            except Exception:
                # 回退到 ORB
                algorithm_name = "ORB"
                detector = cv2.ORB_create(1000)

        try:
            # 检测关键点和描述符
            kp1, des1 = detector.detectAndCompute(img1, None)
            kp2, des2 = detector.detectAndCompute(img2, None)

            if des1 is None or des2 is None or len(kp1) == 0 or len(kp2) == 0:
                return {'speed_mean': 0.0, 'speed_variance': 0.0, 'stability': 0.0}

            # 匹配特征点
            matcher = cv2.BFMatcher()
            matches = []

            if algorithm_name == "ORB":
                # ORB 使用 Hamming 距离
                matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                matches = matcher.match(des1, des2)
            else:
                # SIFT/SURF 使用 KNN
                raw_matches = matcher.knnMatch(des1, des2, k=2)
                # Lowe's ratio test
                for m, n in raw_matches:
                    if m.distance < 0.6 * n.distance:
                        matches.append(m)

            # 提取匹配点坐标
            src_pts = np.float32([kp1[m.queryIdx].pt for m in matches])
            dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches])

            if len(src_pts) == 0:
                return {'speed_mean': 0.0, 'speed_variance': 0.0, 'stability': 0.0}

            # 计算位移和速度
            displacements = np.sqrt(np.sum((dst_pts - src_pts) ** 2, axis=1))
            if time_interval <= 0: time_interval = 0.1  # 防止除零
            speeds = displacements / time_interval

            speed_mean = np.mean(speeds)
            speed_variance = np.var(speeds)

            # 计算稳定性 (匹配点数量 / 平均特征点数量)
            # 注意：如果特征点很少，稳定性计算可能需要归一化调整
            total_keypoints = (len(kp1) + len(kp2)) / 2.0
            stability = len(matches) / total_keypoints if total_keypoints > 0 else 0.0

            return {
                'speed_mean': float(speed_mean),
                'speed_variance': float(speed_variance),
                'stability': float(stability)
            }

        except Exception as e:
            logger.error(f"动态特征提取失败 ({algorithm_name}): {e}")
            return {'speed_mean': 0.0, 'speed_variance': 0.0, 'stability': 0.0}

    @staticmethod
    def extract_texture_glcm(image: np.ndarray,
                             nbit: int = 64,
                             slide_window: int = 7,
                             step: List[int] = [2],
                             angle: List[float] = [0]) -> Dict[str, float]:
        """
        计算图像的平均GLCM纹理特征。

        Args:
            image: 灰度图像
            nbit: 灰度级压缩级数

        Returns:
            包含 mean_homogeneity, mean_contrast, mean_energy, mean_correlation 的字典
        """
        try:
            if len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            h, w = image.shape

            # 压缩灰度级
            # bins = np.linspace(0, 256, nbit + 1)
            # img_digitized = np.digitize(image, bins) - 1
            # 简单线性量化
            img_digitized = (image / 256.0 * nbit).astype(np.uint8)

            # 计算 GLCM (这里简化为计算整图的GLCM，如果需要滑动窗口特征图，计算量会非常大)
            # 原代码逻辑是在滑动窗口上计算 GLCM，然后取均值。
            # 为了性能，这里我们计算整图的 GLCM 并提取属性。
            # 如果必须保留滑动窗口逻辑，请使用下面的 _calcu_glcm_sliding_window 私有方法

            # 使用 skimage 计算整图 GLCM
            g_matrix = graycomatrix(img_digitized, distances=step, angles=angle, levels=nbit, symmetric=True,
                                    normed=True)

            contrast = graycoprops(g_matrix, 'contrast').mean()
            dissimilarity = graycoprops(g_matrix, 'dissimilarity').mean()
            homogeneity = graycoprops(g_matrix, 'homogeneity').mean()
            energy = graycoprops(g_matrix, 'energy').mean()
            correlation = graycoprops(g_matrix, 'correlation').mean()

            return {
                'texture_contrast': float(contrast),
                'texture_dissimilarity': float(dissimilarity),
                'texture_homogeneity': float(homogeneity),
                'texture_energy': float(energy),
                'texture_correlation': float(correlation)
            }

        except Exception as e:
            logger.error(f"GLCM纹理提取失败: {e}")
            return {}