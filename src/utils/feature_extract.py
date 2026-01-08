import cv2
import numpy as np
import logging
import os
import pandas as pd
from typing import Tuple, Dict, List, Optional
from tqdm import tqdm
from scipy import ndimage as ndi

from skimage.feature import graycomatrix, graycoprops, local_binary_pattern, peak_local_max
from skimage.measure import regionprops
from skimage.segmentation import watershed

# 配置日志
logger = logging.getLogger(__name__)


class FrothFeatureExtractor:
    """
    [核心算法层] 浮选泡沫图像特征提取器
    包含颜色、纹理、形态学及动态特征提取算法。
    """

    @staticmethod
    def extract_all_static_features(image: np.ndarray) -> Dict[str, float]:
        """
        一次性提取所有静态特征（颜色 + 纹理 + 形态学）。
        """
        features = {}
        # 1. 颜色特征
        features.update(FrothFeatureExtractor.extract_color_stats(image))
        # 2. 纹理特征 (GLCM & LBP)
        features.update(FrothFeatureExtractor.extract_texture_glcm(image))
        features.update(FrothFeatureExtractor.extract_texture_lbp(image))
        # 3. 形态学特征 (气泡分割)
        features.update(FrothFeatureExtractor.extract_morphological_features(image))
        return features

    @staticmethod
    def extract_color_stats(image: np.ndarray, target_size: Tuple[int, int] = (256, 256)) -> Dict[str, float]:
        """提取颜色统计特征 (RGB/HSV/红灰比)"""
        if image is None: return {}
        try:
            if target_size and (image.shape[0] != target_size[0] or image.shape[1] != target_size[1]):
                image = cv2.resize(image, target_size)

            # --- RGB 空间 (OpenCV默认为BGR) ---
            b, g, r = cv2.split(image)
            r_mean = np.mean(r)
            g_mean = np.mean(g)
            b_mean = np.mean(b)

            # 计算灰度 (加权)
            gray = (0.299 * r + 0.587 * g + 0.114 * b)
            gray_mean = np.mean(gray)

            # 红灰比 (Red/Gray Ratio) - 关键浮选指标
            red_gray_ratio = r_mean / gray_mean if gray_mean > 0 else 0.0

            # 统计矩 (基于灰度)
            gray_flat = gray.flatten()
            gray_std = np.std(gray_flat)
            gray_var = gray_std ** 2

            # 偏度与峰度
            if gray_std > 0:
                skewness = np.mean(((gray_flat - gray_mean) / gray_std) ** 3)
                kurtosis = np.mean(((gray_flat - gray_mean) / gray_std) ** 4)
            else:
                skewness, kurtosis = 0.0, 0.0

            # --- HSV 空间 ---
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            h_mean, s_mean, v_mean = np.mean(hsv, axis=(0, 1))

            return {
                'color_r_mean': float(r_mean),
                'color_g_mean': float(g_mean),
                'color_b_mean': float(b_mean),
                'color_gray_mean': float(gray_mean),
                'color_red_gray_ratio': float(red_gray_ratio),
                'color_variance': float(gray_var),
                'color_skewness': float(skewness),
                'color_kurtosis': float(kurtosis),
                'color_h_mean': float(h_mean),
                'color_s_mean': float(s_mean),
                'color_v_mean': float(v_mean)
            }
        except Exception as e:
            logger.error(f"颜色特征提取错误: {e}")
            return {}

    @staticmethod
    def extract_texture_glcm(image: np.ndarray, nbit: int = 64) -> Dict[str, float]:
        """提取 GLCM (灰度共生矩阵) 纹理特征"""
        if image is None: return {}
        try:
            if len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 压缩灰度级 (量化) 以减少计算量
            img_digitized = (image / 256.0 * nbit).astype(np.uint8)
            img_digitized = np.clip(img_digitized, 0, nbit - 1)

            # 计算 GLCM (距离=1, 多角度平均)
            g_matrix = graycomatrix(img_digitized, [1], [0, np.pi / 4, np.pi / 2, 3 * np.pi / 4],
                                    levels=nbit, symmetric=True, normed=True)

            return {
                'glcm_contrast': float(graycoprops(g_matrix, 'contrast').mean()),
                'glcm_dissimilarity': float(graycoprops(g_matrix, 'dissimilarity').mean()),
                'glcm_homogeneity': float(graycoprops(g_matrix, 'homogeneity').mean()),
                'glcm_energy': float(graycoprops(g_matrix, 'energy').mean()),
                'glcm_correlation': float(graycoprops(g_matrix, 'correlation').mean())
            }
        except Exception as e:
            logger.error(f"GLCM 提取错误: {e}")
            return {}

    @staticmethod
    def extract_texture_lbp(image: np.ndarray) -> Dict[str, float]:
        """提取 LBP (局部二值模式) 纹理特征"""
        if image is None: return {}
        try:
            if len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # LBP 计算 (半径1, 8个点)
            lbp = local_binary_pattern(image, 8, 1, method='uniform')

            # 计算直方图熵 (Entropy)
            # Uniform LBP 产生 10 种模式 (8+2)
            hist, _ = np.histogram(lbp.ravel(), bins=np.arange(0, 11), density=True)
            hist = hist + 1e-7  # 避免 log(0)
            entropy = -np.sum(hist * np.log2(hist))

            return {'lbp_entropy': float(entropy)}
        except Exception as e:
            logger.error(f"LBP 提取错误: {e}")
            return {}

    @staticmethod
    def extract_morphological_features(image: np.ndarray) -> Dict[str, float]:
        """提取形态学特征 (分水岭算法分割气泡并统计尺寸)"""
        if image is None: return {}
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # 1. 预处理 (CLAHE增强 + 高斯模糊)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)

            # 2. 阈值分割 (Otsu)
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # 3. 距离变换与种子生成
            distance = ndi.distance_transform_edt(thresh)
            # min_distance 决定了最小识别的气泡间距
            coords = peak_local_max(distance, min_distance=7, labels=thresh)
            mask = np.zeros(distance.shape, dtype=bool)
            mask[tuple(coords.T)] = True
            markers, _ = ndi.label(mask)

            # 4. 分水岭算法
            labels = watershed(-distance, markers, mask=thresh)

            # 5. 区域属性统计
            regions = regionprops(labels)

            # 过滤极小的噪点区域
            regions = [r for r in regions if r.area > 5]

            if not regions:
                return {
                    'bubble_count': 0.0, 'bubble_mean_diam': 0.0,
                    'bubble_d10': 0.0, 'bubble_d50': 0.0, 'bubble_d90': 0.0
                }

            # 计算等效直径
            diams = np.array([r.equivalent_diameter for r in regions])
            areas = np.array([r.area for r in regions])

            # 计算圆度 (4*pi*Area / Perimeter^2)
            circularities = [(4 * np.pi * r.area) / (r.perimeter ** 2) if r.perimeter > 0 else 0 for r in regions]

            return {
                'bubble_count': float(len(regions)),
                'bubble_mean_area': float(np.mean(areas)),
                'bubble_std_area': float(np.std(areas)),
                'bubble_mean_diam': float(np.mean(diams)),
                'bubble_d10': float(np.percentile(diams, 10)),
                'bubble_d50': float(np.percentile(diams, 50)),  # 中值粒径
                'bubble_d90': float(np.percentile(diams, 90)),
                'bubble_mean_circularity': float(np.mean(circularities))
            }
        except Exception as e:
            logger.error(f"形态学特征提取错误: {e}")
            return {}

    @staticmethod
    def extract_dynamic_features(img1: np.ndarray, img2: np.ndarray, time_interval: float = 0.15) -> Dict[str, float]:
        """
        提取动态特征 (优先 SURF -> SIFT -> ORB)
        需要两帧图像
        """
        if img1 is None or img2 is None: return {}

        # 统一转灰度
        if len(img1.shape) == 3: img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        if len(img2.shape) == 3: img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        detector = None
        algorithm_name = "SURF"

        # 算法选择逻辑
        try:
            if hasattr(cv2, 'xfeatures2d'):
                detector = cv2.xfeatures2d.SURF_create(400)
            else:
                raise AttributeError
        except:
            try:
                algorithm_name = "SIFT"
                detector = cv2.SIFT_create()
            except:
                algorithm_name = "ORB"
                detector = cv2.ORB_create(1000)

        try:
            kp1, des1 = detector.detectAndCompute(img1, None)
            kp2, des2 = detector.detectAndCompute(img2, None)

            if des1 is None or des2 is None or len(kp1) < 2 or len(kp2) < 2:
                return {'speed_mean': 0.0, 'speed_variance': 0.0, 'stability': 0.0}

            # 匹配逻辑
            matcher = cv2.BFMatcher()
            matches = []

            if algorithm_name == "ORB":
                # ORB 使用 Hamming 距离
                matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                matches = matcher.match(des1, des2)
            else:
                # SIFT/SURF 使用 KNN + 比率测试
                raw_matches = matcher.knnMatch(des1, des2, k=2)
                for m, n in raw_matches:
                    if m.distance < 0.6 * n.distance:
                        matches.append(m)

            if not matches:
                return {'speed_mean': 0.0, 'speed_variance': 0.0, 'stability': 0.0}

            # 提取坐标计算距离
            pts1 = np.float32([kp1[m.queryIdx].pt for m in matches])
            pts2 = np.float32([kp2[m.trainIdx].pt for m in matches])

            # 欧氏距离
            distances = np.sqrt(np.sum((pts2 - pts1) ** 2, axis=1))

            if time_interval <= 0: time_interval = 0.1
            speeds = distances / time_interval

            # 稳定性: 匹配点数量 / 平均特征点总数
            stability = len(matches) / ((len(kp1) + len(kp2)) / 2.0)

            return {
                'speed_mean': float(np.mean(speeds)),
                'speed_variance': float(np.var(speeds)),
                'stability': float(stability)
            }
        except Exception as e:
            logger.error(f"动态特征提取错误 ({algorithm_name}): {e}")
            return {'speed_mean': 0.0, 'speed_variance': 0.0, 'stability': 0.0}


class FrothBatchProcessor:
    """
    [业务处理层] 批量处理工具
    用于处理文件夹下的图像数据集并导出 Excel
    """

    @staticmethod
    def process_folder(root_folder: str, output_file: str = 'static_features.xlsx'):
        """
        遍历文件夹 -> 提取静态特征 -> 保存 Excel
        """
        if not os.path.exists(root_folder):
            logger.error(f"路径不存在: {root_folder}")
            return

        results = []
        # 获取所有子文件夹
        subfolders = [f.path for f in os.scandir(root_folder) if f.is_dir()]

        # 如果根目录下直接有图片，也算一个任务
        if not subfolders:
            subfolders = [root_folder]

        logger.info(f"开始处理目录: {root_folder}")

        for folder in tqdm(subfolders, desc="Folders"):
            folder_name = os.path.basename(folder)

            image_files = [f.path for f in os.scandir(folder)
                           if f.is_file() and f.name.lower().endswith(('.jpg', '.png', '.jpeg', '.bmp'))]

            for img_path in tqdm(image_files, desc=f"Img in {folder_name}", leave=False):
                img = cv2.imread(img_path)
                if img is None: continue

                # 提取特征
                feats = FrothFeatureExtractor.extract_all_static_features(img)

                # 添加元数据
                feats['folder'] = folder_name
                feats['filename'] = os.path.basename(img_path)
                results.append(feats)

        if results:
            df = pd.DataFrame(results)
            # 调整列顺序: folder, filename 在最前
            cols = ['folder', 'filename'] + [c for c in df.columns if c not in ['folder', 'filename']]
            df = df[cols]

            if output_file.endswith('.csv'):
                df.to_csv(output_file, index=False)
            else:
                df.to_excel(output_file, index=False)
            logger.info(f"静态特征提取完成，已保存至: {output_file}")
        else:
            logger.info("未提取到任何数据。")

    @staticmethod
    def process_dynamic_folder(root_folder: str, output_file: str = 'dynamic_features.xlsx', interval: float = 0.15):
        """
        遍历文件夹 -> 提取动态特征(前后帧对比) -> 保存 Excel
        """
        results = []
        subfolders = [f.path for f in os.scandir(root_folder) if f.is_dir()]
        if not subfolders: subfolders = [root_folder]

        logger.info(f"开始动态特征分析: {root_folder}")

        for folder in tqdm(subfolders, desc="Dynamic Folders"):
            folder_name = os.path.basename(folder)
            files = sorted([f.path for f in os.scandir(folder)
                            if f.is_file() and f.name.lower().endswith(('.jpg', '.png'))])

            if len(files) < 2: continue

            for i in range(len(files) - 1):
                img1 = cv2.imread(files[i])
                img2 = cv2.imread(files[i + 1])

                feats = FrothFeatureExtractor.extract_dynamic_features(img1, img2, time_interval=interval)

                feats['folder'] = folder_name
                feats['pair'] = f"{os.path.basename(files[i])}-{os.path.basename(files[i + 1])}"
                results.append(feats)

        if results:
            pd.DataFrame(results).to_excel(output_file, index=False)
            logger.info(f"动态特征提取完成，已保存至: {output_file}")


if __name__ == '__main__':
    # 简单的运行测试
    logger.info("FrothFeatureExtractor 模块已加载。请通过其他脚本调用类方法，或取消下方注释运行批处理。")
    # FrothBatchProcessor.process_folder("D:/DataSet/Train", "train_data.xlsx")