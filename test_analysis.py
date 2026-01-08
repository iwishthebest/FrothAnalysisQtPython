import cv2
import json
# 假设您的文件在 src/utils/feature_extract.py
from src.utils.feature_extract import FrothFeatureExtractor

def analyze_one_image(image_path):
    # 1. 读取图像
    img = cv2.imread(image_path)
    if img is None:
        print("错误：无法读取图像")
        return

    print(f"正在分析图像: {image_path} ...")

    # 2. 一键提取所有静态特征
    # 包括：颜色(RGB/HSV)、纹理(GLCM/LBP)、形态学(气泡尺寸/数量/圆度)
    all_features = FrothFeatureExtractor.extract_all_static_features(img)

    # 3. 打印结果 (格式化输出)
    print("\n=== 分析结果 ===")
    # 这里用 json.dumps 只是为了漂亮地打印字典
    print(json.dumps(all_features, indent=4, ensure_ascii=False))

    # 4. 访问特定特征示例
    print(f"\n关键指标速览:")
    print(f"- 气泡数量: {all_features.get('bubble_count', 0)}")
    print(f"- 平均尺寸(D50): {all_features.get('bubble_d50', 0):.2f}")
    print(f"- 载矿指示(红灰比): {all_features.get('color_red_gray_ratio', 0):.4f}")

# 运行
if __name__ == "__main__":
    analyze_one_image("test_froth.jpg") # 替换为您的实际图片路径