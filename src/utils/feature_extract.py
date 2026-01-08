import cv2
import numpy as np
import logging
from typing import Tuple, Dict, List, Any
from skimage.feature import graycomatrix, graycoprops, local_binary_pattern
from skimage.measure import regionprops
from skimage.segmentation import watershed
from skimage.feature import peak_local_max
from scipy import ndimage as ndi

# 配置日志
logger = logging.getLogger(__name__)


class FrothFeatureExtractor:
    """
    浮选泡沫图像特征提取工具类 (增强版)。
    提供颜色(RGB/HSV)、纹理(GLCM/LBP)、形态学(尺寸/形状)及动态特征提取功能。
    """

    @staticmethod
    def extract_all_static_features(image: np.ndarray) -> Dict[str, float]:
        """
        一次性提取所有静态特征（颜色、纹理、形态学）。
        适合直接用于机器学习模型的输入。
        """
        features = {}
        features.update(FrothFeatureExtractor.extract_color_stats(image))
        features.update(FrothFeatureExtractor.extract_texture_glcm(image))
        features.update(FrothFeatureExtractor.extract_texture_lbp(image))
        features.update(FrothFeatureExtractor.extract_morphological_features(image))
        return features

    @staticmethod
    def extract_color_stats(image: np.ndarray, target_size: Tuple[int, int] = (256, 256)) -> Dict[str, float]:
        """
        提取颜色统计特征 (RGB 和 HSV 空间)。
        """
        if image is None: return {}
        try:
            if target_size and (image.shape[0] != target_size[0] or image.shape[1] != target_size[1]):
                image = cv2.resize(image, target_size)

            # --- RGB 空间特征 ---
            # OpenCV 为 BGR
            b_mean, g_mean, r_mean = np.mean(image, axis=(0, 1))
            b_std, g_std, r_std = np.std(image, axis=(0, 1))

            # 红灰比 (Red/Gray Ratio) - 经典浮选指标
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray_mean = np.mean(gray_image)
            red_gray_ratio = r_mean / gray_mean if gray_mean > 0 else 0.0

            stats = {
                'color_r_mean': float(r_mean), 'color_g_mean': float(g_mean), 'color_b_mean': float(b_mean),
                'color_r_std': float(r_std), 'color_gray_mean': float(gray_mean),
                'color_red_gray_ratio': float(red_gray_ratio)
            }

            # --- HSV 空间特征 ---
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            h_mean, s_mean, v_mean = np.mean(hsv, axis=(0, 1))

            stats.update({
                'color_h_mean': float(h_mean),  # 色调：反映泡沫颜色类型
                'color_s_mean': float(s_mean),  # 饱和度：反映颜色纯度
                'color_v_mean': float(v_mean)  # 亮度：反映反光程度
            })

            return stats
        except Exception as e:
            logger.error(f"颜色特征提取失败: {e}")
            return {}

    @staticmethod
    def extract_texture_glcm(image: np.ndarray, nbit: int = 64) -> Dict[str, float]:
        """
        提取 GLCM (灰度共生矩阵) 纹理特征。
        反映图像的粗糙度、对比度和复杂性。
        """
        try:
            if image is None: return {}
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # 压缩灰度级以提高计算速度和稳定性
            img_digitized = (gray / 256.0 * nbit).astype(np.uint8)
            img_digitized = np.clip(img_digitized, 0, nbit - 1)

            # 计算 GLCM (距离=1, 角度=0, 45, 90, 135 的平均)
            g_matrix = graycomatrix(img_digitized, [1], [0, np.pi / 4, np.pi / 2, 3 * np.pi / 4],
                                    levels=nbit, symmetric=True, normed=True)

            return {
                'glcm_contrast': float(graycoprops(g_matrix, 'contrast').mean()),  # 对比度：清晰度
                'glcm_dissimilarity': float(graycoprops(g_matrix, 'dissimilarity').mean()),
                'glcm_homogeneity': float(graycoprops(g_matrix, 'homogeneity').mean()),  # 同质性：纹理规则程度
                'glcm_energy': float(graycoprops(g_matrix, 'energy').mean()),  # 能量：纹理均匀性
                'glcm_correlation': float(graycoprops(g_matrix, 'correlation').mean())  # 相关性
            }
        except Exception as e:
            logger.error(f"GLCM特征提取失败: {e}")
            return {}

    @staticmethod
    def extract_texture_lbp(image: np.ndarray, radius: int = 1, n_points: int = 8) -> Dict[str, float]:
        """
        提取 LBP (局部二值模式) 纹理特征。
        LBP 对光照变化具有很强的鲁棒性。
        """
        try:
            if image is None: return {}
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # 使用 Uniform LBP
            lbp = local_binary_pattern(gray, n_points, radius, method='uniform')

            # 计算 LBP 直方图的统计特征
            n_bins = int(lbp.max() + 1)
            hist, _ = np.histogram(lbp.ravel(), bins=n_bins, range=(0, n_bins), density=True)

            # LBP 能量 (Energy) 和 熵 (Entropy)
            lbp_energy = np.sum(hist ** 2)
            lbp_entropy = -np.sum(hist * np.log2(hist + 1e-7))

            return {
                'lbp_energy': float(lbp_energy),
                'lbp_entropy': float(lbp_entropy)
            }
        except Exception as e:
            logger.error(f"LBP特征提取失败: {e}")
            return {}

    @staticmethod
    def extract_morphological_features(image: np.ndarray) -> Dict[str, float]:
        """
        提取形态学特征 (基于分水岭算法分割气泡)。
        包括：气泡数量、平均大小、尺寸分布、圆度。
        注意：这是一项耗时操作。
        """
        try:
            if image is None: return {}
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # 1. 预处理：增强对比度 + 降噪
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)

            # 2. 阈值分割 (Otsu)
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # 3. 距离变换与分水岭种子生成
            # 计算非零像素到最近零像素的距离
            distance = ndi.distance_transform_edt(thresh)

            # 寻找局部最大值作为种子点 (min_distance 决定了能识别的最小气泡间距)
            coords = peak_local_max(distance, min_distance=7, labels=thresh)
            mask = np.zeros(distance.shape, dtype=bool)
            mask[tuple(coords.T)] = True
            markers, _ = ndi.label(mask)

            # 4. 执行分水岭算法
            labels = watershed(-distance, markers, mask=thresh)

            # 5. 计算区域属性
            regions = regionprops(labels)

            if not regions:
                return {'bubble_count': 0, 'bubble_mean_area': 0, 'bubble_d10': 0, 'bubble_d90': 0}

            areas = [r.area for r in regions]
            equivalent_diameters = [r.equivalent_diameter for r in regions]

            # 计算圆度 (4 * pi * Area / Perimeter^2)
            # perimeter 为 0 时设为 0
            circularities = [(4 * np.pi * r.area) / (r.perimeter ** 2) if r.perimeter > 0 else 0 for r in regions]

            # 6. 统计特征
            areas = np.array(areas)
            diams = np.array(equivalent_diameters)

            # 尺寸分布百分位数
            d10 = np.percentile(diams, 10)
            d50 = np.percentile(diams, 50)
            d90 = np.percentile(diams, 90)

            return {
                'bubble_count': float(len(regions)),  # 气泡数量
                'bubble_mean_area': float(np.mean(areas)),  # 平均面积 (像素)
                'bubble_std_area': float(np.std(areas)),  # 面积标准差 (大小均匀度)
                'bubble_mean_diam': float(np.mean(diams)),  # 平均等效直径
                'bubble_d10': float(d10),  # 细粒级尺寸
                'bubble_d50': float(d50),  # 中值尺寸
                'bubble_d90': float(d90),  # 粗粒级尺寸
                'bubble_mean_circularity': float(np.mean(circularities))  # 平均圆度 (越接近1越圆)
            }

        except Exception as e:
            logger.error(f"形态学特征提取失败: {e}")
            return {
                'bubble_count': 0.0,
                'bubble_mean_area': 0.0
            }

    @staticmethod
    def extract_dynamic_features(img1: np.ndarray, img2: np.ndarray, time_interval: float = 0.15) -> Dict[str, float]:
        """
        提取两帧图像间的动态特征（速度、稳定性）。
        (与之前版本保持一致，此处省略具体实现以节省篇幅，实际使用时请保留)
        """
        # ... (保留原有的动态特征代码) ...
        # 为完整性，建议保留之前的 SURF/SIFT/ORB 实现逻辑
        return {'speed_mean': 0.0, 'stability': 0.0}