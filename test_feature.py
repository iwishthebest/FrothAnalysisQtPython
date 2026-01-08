import cv2
import numpy as np
# 导入我们重构后的类
from src.utils.feature_extract import FrothFeatureExtractor


def analyze_single_image(image_path):
    # 1. 读取图像 (OpenCV 读取默认为 BGR 格式)
    img = cv2.imread(image_path)

    if img is None:
        print(f"错误：无法找到或读取图像 {image_path}")
        return

    print(f"正在分析图像: {image_path} (尺寸: {img.shape})")

    # 2. 提取颜色与统计特征 (传入单张图像)
    # 这会计算红灰比、灰度均值、方差、偏度、峰度等
    color_stats = FrothFeatureExtractor.extract_color_stats(img)
    print("\n[颜色与统计特征]:")
    for k, v in color_stats.items():
        print(f"  {k}: {v:.4f}")

    # 3. 提取纹理特征 (GLCM) (传入单张图像)
    # 这会计算对比度、能量、相关性等
    texture_stats = FrothFeatureExtractor.extract_texture_glcm(img)
    print("\n[GLCM 纹理特征]:")
    for k, v in texture_stats.items():
        print(f"  {k}: {v:.4f}")

    # 4. 关于动态特征的说明
    print("\n[动态特征]:")
    print("  警告：动态特征(速度/稳定性)需要两帧图像才能计算。")
    print("  如果您有连续的第二张图，可以调用: FrothFeatureExtractor.extract_dynamic_features(img1, img2)")


# --- 运行测试 ---
if __name__ == "__main__":
    # 请替换为您实际的图片路径
    image_file = "test_froth.jpg"

    # 为了演示，我们先创建一个模拟的泡沫图像（如果您的目录下没有真实图片）
    dummy_img = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
    cv2.imwrite(image_file, dummy_img)

    analyze_single_image(image_file)