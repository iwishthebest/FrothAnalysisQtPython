import cv2
import numpy as np
from skimage.feature import graycomatrix, graycoprops


class FrothFeatureExtractor:
    """泡沫特征提取器"""

    @staticmethod
    def extract_color_features(image: np.ndarray) -> dict:
        """提取颜色特征 (红/灰比, 均值)"""
        if image is None: return {}

        # 转换到 RGB (假设输入是 BGR，OpenCV默认)
        # 注意：您原代码中用 image[:, :, 2] 作为红色通道，这在 BGR 格式下是对的
        red_channel = image[:, :, 2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        red_mean = np.mean(red_channel)
        gray_mean = np.mean(gray)

        # 避免除以零
        red_gray_ratio = red_mean / gray_mean if gray_mean > 0 else 0

        return {
            "color_red_mean": float(red_mean),
            "color_gray_mean": float(gray_mean),
            "color_rg_ratio": float(red_gray_ratio)
        }

    @staticmethod
    def extract_texture_features(image: np.ndarray) -> dict:
        """提取纹理特征 (GLCM) - 基于您提供的代码简化"""
        if image is None: return {}

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # 缩小图像以加快计算速度 (GLCM非常耗时)
        gray_resized = cv2.resize(gray, (128, 128))

        # 计算 GLCM
        glcm = graycomatrix(gray_resized, distances=[1], angles=[0, np.pi / 4, np.pi / 2],
                            levels=256, symmetric=True, normed=True)

        return {
            "texture_contrast": float(graycoprops(glcm, 'contrast').mean()),
            "texture_homogeneity": float(graycoprops(glcm, 'homogeneity').mean()),
            "texture_energy": float(graycoprops(glcm, 'energy').mean()),
            "texture_correlation": float(graycoprops(glcm, 'correlation').mean())
        }

    @staticmethod
    def extract_geometry_features(image: np.ndarray) -> dict:
        """提取几何特征 (气泡平均大小) - 简单分水岭算法示例"""
        # 您可以基于原代码中的 watershed 部分实现
        # 这里仅做示例框架
        return {"bubble_avg_size": 0.0}