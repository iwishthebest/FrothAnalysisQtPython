import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy import ndimage as ndi
from skimage.feature import peak_local_max
from skimage.segmentation import watershed
from skimage.color import label2rgb


def visualize_bubble_segmentation(image_path):
    # --- 1. 读取图像 ---
    image = cv2.imread(image_path)
    if image is None:
        print(f"无法读取图像: {image_path}")
        return

    # 转换为 RGB 用于 matplotlib 显示
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # --- 2. 预处理 (增强对比度 + 模糊) ---
    # CLAHE (限制对比度自适应直方图均衡化) 增强气泡边缘
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    # 高斯模糊去除噪点
    blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)

    # --- 3. 二值化 (Otsu阈值) ---
    # 将图像分为前景(气泡)和背景(黑色)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # --- 4. 距离变换 (核心步骤) ---
    # 计算每个白色像素到最近黑色像素的距离
    # 气泡中心越亮，边缘越暗，形成“山峰”
    distance = ndi.distance_transform_edt(thresh)

    # --- 5. 生成种子点 (Markers) ---
    # 寻找局部最大值(气泡中心)作为注水的“泉眼”
    # min_distance 决定了允许的最小气泡间距，防止过度分割
    coords = peak_local_max(distance, min_distance=7, labels=thresh)
    mask = np.zeros(distance.shape, dtype=bool)
    mask[tuple(coords.T)] = True
    markers, _ = ndi.label(mask)

    # --- 6. 分水岭算法 (Watershed) ---
    # 从种子点开始注水，直到填满盆地(distance)
    # -distance 表示取反，因为算法寻找的是盆地(最小值)，而我们的是山峰(最大值)
    labels = watershed(-distance, markers, mask=thresh)

    # --- 7. 结果可视化 ---

    # 将标签转化为彩色覆盖层 (Image overlay)
    image_label_overlay = label2rgb(labels, image=image_rgb, bg_label=0, alpha=0.3)

    # 绘制轮廓 (Contours) 到原图上
    contour_img = image_rgb.copy()
    # 遍历每个标签值（跳过0背景）
    for label_val in np.unique(labels):
        if label_val == 0: continue
        # 创建单个气泡的掩码
        mask = np.zeros(gray.shape, dtype="uint8")
        mask[labels == label_val] = 255
        # 查找轮廓
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # 绘制绿色轮廓
        cv2.drawContours(contour_img, cnts, -1, (0, 255, 0), 1)

    # --- 8. Matplotlib 绘图 ---
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    ax = axes.ravel()

    # 图1: 原图
    ax[0].imshow(image_rgb)
    ax[0].set_title("1. Original Image")

    # 图2: 预处理后 (CLAHE)
    ax[1].imshow(enhanced, cmap='gray')
    ax[1].set_title("2. Preprocessed (CLAHE)")

    # 图3: 二值化掩码
    ax[2].imshow(thresh, cmap='gray')
    ax[2].set_title("3. Threshold (Binary)")

    # 图4: 距离变换图 (越亮代表越中心)
    # 使用 'jet' 伪彩色显示距离高低
    im4 = ax[3].imshow(distance, cmap='jet')
    ax[3].set_title("4. Distance Transform")
    plt.colorbar(im4, ax=ax[3], fraction=0.046, pad=0.04)

    # 图5: 分水岭结果 (彩色块)
    ax[4].imshow(image_label_overlay)
    ax[4].set_title(f"5. Watershed Labels (Count: {len(np.unique(labels)) - 1})")

    # 图6: 最终轮廓图
    ax[5].imshow(contour_img)
    ax[5].set_title("6. Final Contours")

    for a in ax:
        a.axis('off')

    plt.tight_layout()
    plt.show()


# --- 运行测试 ---
if __name__ == "__main__":
    # 请替换为您的图片路径
    img_path = "test_froth.jpg"

    # 如果没有图片，生成一个简单的模拟图
    import os

    if not os.path.exists(img_path):
        print("未找到图片，生成模拟泡沫图...")
        dummy = np.zeros((300, 300), dtype=np.uint8)
        # 画几个重叠的圆
        for i in range(15):
            center = np.random.randint(50, 250, 2)
            radius = np.random.randint(20, 50)
            cv2.circle(dummy, tuple(center), radius, 255, -1)
        # 加点噪点
        noise = np.random.randint(0, 50, (300, 300), dtype=np.uint8)
        dummy = cv2.add(dummy, noise)
        cv2.imwrite(img_path, dummy)

    visualize_bubble_segmentation(img_path)