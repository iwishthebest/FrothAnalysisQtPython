import cv2
import numpy as np
from scipy import ndimage
import matplotlib.pyplot as plt

# 阈值设置（基于前面的分析）
DIRECTIONALITY_THRESHOLD = 0.65
EDGE_ROUGHNESS_THRESHOLD = 15.0
BRIGHTNESS_UNIFORMITY_THRESHOLD = 0.25
SURFACE_ROUGHNESS_THRESHOLD = 12.0
MIN_COLOR_SATURATION = 8.0
MAX_GRAYSCALE_RATIO = 0.85


def load_and_preprocess_images(image1_path, image2_path):
    """加载并预处理两张图像"""
    img1 = cv2.imread(image1_path)
    img2 = cv2.imread(image2_path)

    if img1 is None or img2 is None:
        raise ValueError("无法加载图像，请检查路径是否正确")

    # 转换为RGB格式用于显示
    img1_rgb = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)
    img2_rgb = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)

    # 转换为灰度图用于分析
    img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    return img1, img2, img1_rgb, img2_rgb, img1_gray, img2_gray


def display_images_side_by_side(img1_rgb, img2_rgb, title1="图像1", title2="图像2"):
    """并排显示两张图像"""
    # Set the font to SimHei which supports CJK characters
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False  # Ensure proper rendering of minus signs

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    ax1.imshow(img1_rgb)
    ax1.set_title(title1)
    ax1.axis('off')

    ax2.imshow(img2_rgb)
    ax2.set_title(title2)
    ax2.axis('off')

    plt.tight_layout()
    plt.show()


def analyze_basic_properties(img1_gray, img2_gray):
    """分析基本图像属性"""
    print("=" * 50)
    print("基本属性分析")
    print("=" * 50)

    properties = {
        "尺寸": lambda img: img.shape[:2],
        "平均亮度": lambda img: np.mean(img),
        "亮度标准差": lambda img: np.std(img),
        "对比度": lambda img: np.max(img) - np.min(img),
        "动态范围": lambda img: (np.min(img), np.max(img))
    }

    for prop_name, prop_func in properties.items():
        val1 = prop_func(img1_gray)
        val2 = prop_func(img2_gray)
        print(f"{prop_name}: 图像1 = {val1}, 图像2 = {val2}")


def analyze_texture_directionality(img1_gray, img2_gray):
    """分析纹理方向性"""
    print("\n" + "=" * 50)
    print("纹理方向性分析")
    print("=" * 50)

    def calculate_directionality(img):
        # 计算梯度方向
        sobelx = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)

        # 计算梯度幅值和方向
        magnitude = np.sqrt(sobelx ** 2 + sobely ** 2)
        direction = np.arctan2(sobely, sobelx)

        # 计算方向直方图
        hist, bins = np.histogram(direction[magnitude > 10], bins=8, range=(-np.pi, np.pi))

        if np.sum(hist) > 0:
            max_bin = np.max(hist)
            directionality = max_bin / np.sum(hist)

            # 计算方向方差
            bin_centers = (bins[:-1] + bins[1:]) / 2
            weighted_directions = hist * bin_centers
            mean_direction = np.sum(weighted_directions) / np.sum(hist)
            direction_variance = np.sum(hist * (bin_centers - mean_direction) ** 2) / np.sum(hist)

            return directionality, direction_variance
        return 0, 0

    dir1, var1 = calculate_directionality(img1_gray)
    dir2, var2 = calculate_directionality(img2_gray)

    print(f"方向性系数: 图像1 = {dir1:.3f}, 图像2 = {dir2:.3f}")
    print(f"方向方差: 图像1 = {var1:.3f}, 图像2 = {var2:.3f}")

    # 判断是否超过阈值
    if dir2 > DIRECTIONALITY_THRESHOLD and var2 < 0.3:
        print(f"⚠ 图像2检测到强烈方向性纹理(超过阈值 {DIRECTIONALITY_THRESHOLD})")
    else:
        print("✓ 方向性纹理正常")


def analyze_edge_roughness(img1_gray, img2_gray):
    """分析边缘粗糙度"""
    print("\n" + "=" * 50)
    print("边缘粗糙度分析")
    print("=" * 50)

    def calculate_edge_roughness(img):
        # 使用Canny边缘检测
        edges = cv2.Canny(img, 50, 150)

        # 计算边缘点的曲率/粗糙度
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        if len(contours) > 0:
            total_roughness = 0
            valid_contours = 0

            for contour in contours:
                if len(contour) > 10:
                    x = contour[:, 0, 0].astype(np.float32)
                    y = contour[:, 0, 1].astype(np.float32)

                    dx = np.gradient(x)
                    dy = np.gradient(y)
                    d2x = np.gradient(dx)
                    d2y = np.gradient(dy)

                    # Add a small epsilon to avoid division by zero
                    epsilon = 1e-8
                    curvature = np.abs(dx * d2y - dy * d2x) / ((dx ** 2 + dy ** 2) + epsilon) ** 1.5
                    curvature = curvature[np.isfinite(curvature)]

                    if len(curvature) > 0:
                        avg_roughness = np.mean(curvature)
                        total_roughness += avg_roughness
                        valid_contours += 1

            if valid_contours > 0:
                return total_roughness / valid_contours
        return 0

    roughness1 = calculate_edge_roughness(img1_gray)
    roughness2 = calculate_edge_roughness(img2_gray)

    print(f"边缘粗糙度: 图像1 = {roughness1:.2f}, 图像2 = {roughness2:.2f}")

    if roughness2 > EDGE_ROUGHNESS_THRESHOLD:
        print(f"⚠ 图像2边缘粗糙度过高(超过阈值 {EDGE_ROUGHNESS_THRESHOLD})")
    else:
        print("✓ 边缘粗糙度正常")


def analyze_brightness_uniformity(img1_gray, img2_gray):
    """分析亮度均匀性"""
    print("\n" + "=" * 50)
    print("亮度均匀性分析")
    print("=" * 50)

    def calculate_brightness_uniformity(img):
        height, width = img.shape
        block_size = 32
        blocks = []

        for i in range(0, height - block_size, block_size):
            for j in range(0, width - block_size, block_size):
                block = img[i:i + block_size, j:j + block_size]
                blocks.append(np.mean(block))

        if len(blocks) > 0:
            block_range = np.max(blocks) - np.min(blocks)
            return 1 - (block_range / 255.0)
        return 0

    uniformity1 = calculate_brightness_uniformity(img1_gray)
    uniformity2 = calculate_brightness_uniformity(img2_gray)

    print(f"亮度均匀性得分: 图像1 = {uniformity1:.3f}, 图像2 = {uniformity2:.3f}")

    if uniformity2 < BRIGHTNESS_UNIFORMITY_THRESHOLD:
        print(f"⚠ 图像2亮度不均匀(低于阈值 {BRIGHTNESS_UNIFORMITY_THRESHOLD})")
    else:
        print("✓ 亮度分布均匀")


def analyze_surface_roughness(img1_gray, img2_gray):
    """分析表面粗糙度"""
    print("\n" + "=" * 50)
    print("表面粗糙度分析")
    print("=" * 50)

    def calculate_surface_roughness(img):
        radius = 3
        lbp = np.zeros_like(img, dtype=np.uint8)

        for i in range(radius, img.shape[0] - radius):
            for j in range(radius, img.shape[1] - radius):
                center = img[i, j]
                code = 0
                for k, (di, dj) in enumerate([(radius, 0), (radius, radius), (0, radius), (-radius, radius),
                                              (-radius, 0), (-radius, -radius), (0, -radius), (radius, -radius)]):
                    if img[i + di, j + dj] >= center:
                        code |= (1 << k)
                lbp[i, j] = code

        # 计算LBP直方图的熵
        hist, _ = np.histogram(lbp.ravel(), bins=256, range=(0, 255))
        hist = hist[hist > 0]
        prob = hist / hist.sum()
        entropy = -np.sum(prob * np.log2(prob))

        return entropy

    roughness1 = calculate_surface_roughness(img1_gray)
    roughness2 = calculate_surface_roughness(img2_gray)

    print(f"表面粗糙度(熵): 图像1 = {roughness1:.2f}, 图像2 = {roughness2:.2f}")

    if roughness2 > SURFACE_ROUGHNESS_THRESHOLD:
        print(f"⚠ 图像2表面粗糙度过高(超过阈值 {SURFACE_ROUGHNESS_THRESHOLD})")
    else:
        print("✓ 表面粗糙度正常")


def analyze_color_saturation(img1, img2):
    """分析色彩饱和度"""
    print("\n" + "=" * 50)
    print("色彩饱和度分析")
    print("=" * 50)

    def calculate_color_saturation(img):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        saturation = hsv[:, :, 1]

        avg_saturation = np.mean(saturation)
        low_saturation_ratio = np.sum(saturation < MIN_COLOR_SATURATION) / saturation.size

        return avg_saturation, low_saturation_ratio

    sat1, low_sat_ratio1 = calculate_color_saturation(img1)
    sat2, low_sat_ratio2 = calculate_color_saturation(img2)

    print(f"平均饱和度: 图像1 = {sat1:.2f}, 图像2 = {sat2:.2f}")
    print(f"低饱和度像素比例: 图像1 = {low_sat_ratio1:.3f}, 图像2 = {low_sat_ratio2:.3f}")

    if sat2 < MIN_COLOR_SATURATION or low_sat_ratio2 > MAX_GRAYSCALE_RATIO:
        print(f"⚠ 图像2色彩饱和度不足(低于阈值 {MIN_COLOR_SATURATION} 或灰度化比例高于 {MAX_GRAYSCALE_RATIO})")
    else:
        print("✓ 色彩饱和度正常")


def analyze_histogram_comparison(img1_gray, img2_gray):
    """分析直方图对比"""
    print("\n" + "=" * 50)
    print("直方图对比分析")
    print("=" * 50)

    # 计算直方图
    hist1 = cv2.calcHist([img1_gray], [0], None, [256], [0, 256])
    hist2 = cv2.calcHist([img2_gray], [0], None, [256], [0, 256])

    # 归一化直方图
    hist1 = hist1 / hist1.sum()
    hist2 = hist2 / hist2.sum()

    # 计算直方图相关性
    correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
    print(f"直方图相关性: {correlation:.3f}")

    # 计算直方图交集
    intersection = cv2.compareHist(hist1, hist2, cv2.HISTCMP_INTERSECT)
    print(f"直方图交集: {intersection:.3f}")

    # 计算巴氏距离
    bhattacharyya = cv2.compareHist(hist1, hist2, cv2.HISTCMP_BHATTACHARYYA)
    print(f"巴氏距离: {bhattacharyya:.3f}")

    # 可视化直方图
    plt.figure(figsize=(10, 4))
    plt.plot(hist1, color='blue', alpha=0.7, label='图像1')
    plt.plot(hist2, color='red', alpha=0.7, label='图像2')
    plt.title('灰度直方图对比')
    plt.xlabel('像素值')
    plt.ylabel('频率')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()


def analyze_gradient_comparison(img1_gray, img2_gray):
    """分析梯度对比"""
    print("\n" + "=" * 50)
    print("梯度对比分析")
    print("=" * 50)

    # 计算梯度
    grad_x1 = cv2.Sobel(img1_gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y1 = cv2.Sobel(img1_gray, cv2.CV_64F, 0, 1, ksize=3)
    grad_mag1 = np.sqrt(grad_x1 ** 2 + grad_y1 ** 2)

    grad_x2 = cv2.Sobel(img2_gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y2 = cv2.Sobel(img2_gray, cv2.CV_64F, 0, 1, ksize=3)
    grad_mag2 = np.sqrt(grad_x2 ** 2 + grad_y2 ** 2)

    print(f"最大梯度幅值: 图像1 = {np.max(grad_mag1):.2f}, 图像2 = {np.max(grad_mag2):.2f}")
    print(f"平均梯度幅值: 图像1 = {np.mean(grad_mag1):.2f}, 图像2 = {np.mean(grad_mag2):.2f}")
    print(f"梯度标准差: 图像1 = {np.std(grad_mag1):.2f}, 图像2 = {np.std(grad_mag2):.2f}")

    # 可视化梯度图
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))

    ax1.imshow(grad_mag1, cmap='jet')
    ax1.set_title('图像1梯度图')
    ax1.axis('off')

    ax2.imshow(grad_mag2, cmap='jet')
    ax2.set_title('图像2梯度图')
    ax2.axis('off')

    ax3.hist(grad_mag1.ravel(), bins=50, color='blue', alpha=0.7, label='图像1')
    ax3.set_title('图像1梯度分布')
    ax3.legend()

    ax4.hist(grad_mag2.ravel(), bins=50, color='red', alpha=0.7, label='图像2')
    ax4.set_title('图像2梯度分布')
    ax4.legend()

    plt.tight_layout()
    plt.show()


def comprehensive_comparison(image1_path, image2_path):
    """综合比较两张图像的所有特征"""
    # 加载图像
    img1, img2, img1_rgb, img2_rgb, img1_gray, img2_gray = load_and_preprocess_images(
        image1_path, image2_path)

    # 并排显示图像
    display_images_side_by_side(img1_rgb, img2_rgb)

    # 执行各项分析
    analyze_basic_properties(img1_gray, img2_gray)
    analyze_texture_directionality(img1_gray, img2_gray)
    analyze_edge_roughness(img1_gray, img2_gray)
    analyze_brightness_uniformity(img1_gray, img2_gray)
    analyze_surface_roughness(img1_gray, img2_gray)
    analyze_color_saturation(img1, img2)
    analyze_histogram_comparison(img1_gray, img2_gray)
    analyze_gradient_comparison(img1_gray, img2_gray)

    print("\n" + "=" * 50)
    print("综合分析完成")
    print("=" * 50)


# 使用示例
if __name__ == "__main__":
    # 替换为您的图像路径
    image1_path = r"D:\dataCollect\data\extracted_frames_check\20251029\frame_20251029_112635.jpg"  # 第一张（完好）图像路径
    image2_path = r"D:\dataCollect\data\extracted_frames_check\20251029\frame_20251029_112640.jpg"  # 第二张（损坏）图像路径

    try:
        comprehensive_comparison(image1_path, image2_path)
    except Exception as e:
        print(f"错误: {e}")
