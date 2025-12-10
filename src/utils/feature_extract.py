import cv2
import numpy as np
from PIL import Image
# 加载图像
import os
import cv2
import numpy as np
from PIL import Image
import pandas as pd
from tqdm import tqdm


def process_images_in_folder(folder_path):
    # 遍历文件夹中的所有子文件夹
    subfolders = [f.path for f in os.scandir(folder_path) if f.is_dir()]

    # 创建一个空的 DataFrame 来存储结果
    data = pd.DataFrame(
        columns=['Image', 'Red/Gray Ratio', 'Mean', 'Variance', 'Skewness', 'Kurtosis'])

    # 使用 tqdm 显示处理进度
    for subfolder in tqdm(subfolders, desc='Processing Subfolders', unit='folder'):
        image_files = [f.path for f in os.scandir(subfolder) if
                       f.is_file() and f.name.endswith(('.jpg', '.jpeg', '.png'))]

        for image_file in tqdm(image_files, desc='Processing Images', unit='image', leave=False):
            # 加载图像
            image = cv2.imread(image_file)
            target_size = (256, 256)
            image = cv2.resize(image, target_size)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray_pil = Image.fromarray(gray)
            # 提取红色通道
            red_channel = image[:, :, 2]  # OpenCV中颜色通道的顺序是BGR，因此红色通道对应索引2
            # 计算红色分量的均值
            red_mean = red_channel.mean()
            gray_image = 0.289 * image[:, :, 2] + 0.587 * image[:, :, 1] + 0.114 * image[:, :, 0]
            gray_image = gray_image.astype('uint8')
            # 计算灰度图像的均值
            gray_mean = gray_image.mean()
            # 计算红色分量与灰度图像均值的比值
            red_gray_ratio = red_mean / gray_mean

            # 计算灰度图像的统计特征
            width, height = gray_pil.size
            pixel_counts = np.zeros(256)
            total_pixels = width * height
            for y in range(height):
                for x in range(width):
                    pixel_value = gray_pil.getpixel((x, y))
                    pixel_counts[pixel_value] += 1
            pixel_probility = pixel_counts / total_pixels
            b = np.arange(256)
            mean = np.sum(b * pixel_probility)
            variance = np.sum(((b - mean) ** 2) * pixel_probility)
            skewness = np.sum(((b - mean) ** 3) * pixel_probility) / variance ** 3
            kurtosis = np.sum(((b - mean) ** 4) * pixel_probility) / variance ** 4

            # 将结果添加到 DataFrame 中
            data = pd.concat([data, pd.DataFrame({'Image': [os.path.basename(image_file)],

                                                  'Red/Gray Ratio': [red_gray_ratio],
                                                  'Mean': [mean],
                                                  'Variance': [variance],
                                                  'Skewness': [skewness],
                                                  'Kurtosis': [kurtosis]})])

    return data


# 文件夹路径
folder_path = "D:/JetBrains/sample/validation"

# 处理图像并获取结果
result = process_images_in_folder(folder_path)

# 保存结果到 Excel 文件
result.to_excel('image_statistics_val.xlsx', index=False)

image = cv2.imread("test3.jpg")
target_size = (256, 256)
image = cv2.resize(image, target_size)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
gray_pil = Image.fromarray(gray)
# 提取红色通道
red_channel = image[:, :, 2]  # OpenCV中颜色通道的顺序是BGR，因此红色通道对应索引2

# 计算红色分量的均值
red_mean = red_channel.mean()

gray_image = 0.289 * image[:, :, 2] + 0.587 * image[:, :, 1] + 0.114 * image[:, :, 0]
gray_image = gray_image.astype('uint8')
# 计算红色分量
gray_mean = gray_image.mean()
Rrelative = red_mean / gray_mean

print("红色分量比重:", Rrelative)

width = 256
height = 256

# 统计每个像素值的数量
pixel_counts = np.zeros(256)
total_pixels = width * height

# 遍历图像中的每个像素
for y in range(height):
    for x in range(width):
        pixel_value = gray_pil.getpixel((x, y))
        pixel_counts[pixel_value] += 1
pixel_probility = pixel_counts / total_pixels
b = np.arange(256)
mean = np.sum(b * pixel_probility)
varience = np.sum(((b - mean) ** 2) * pixel_probility)
skewness = np.sum(((b - mean) ** 3) * pixel_probility) / varience ** 3
kurtosis = np.sum(((b - mean) ** 4) * pixel_probility) / varience ** 4
print("均值：", mean)
print("方差：", varience)
print("偏度：", skewness)
print("峰度：", kurtosis)

import os


def rename_images(folder_path):
    # 遍历文件夹中的所有子文件夹
    subfolders = [f.path for f in os.scandir(folder_path) if f.is_dir()]

    for subfolder in subfolders:
        # 遍历子文件夹中的所有图片文件
        for file_name in os.listdir(subfolder):
            # 检查文件名是否符合要求
            if file_name.startswith("frame_") and file_name.endswith(".jpg"):
                # 获取文件名中的数字部分
                number = file_name.split("_")[1].split(".")[0]
                # 如果数字部分是个位数，则在前面加上一个 "0"
                if len(number) == 1:
                    new_name = "frame_0" + number + ".jpg"
                    # 重命名图片文件
                    os.rename(os.path.join(subfolder, file_name), os.path.join(subfolder, new_name))


# 文件夹路径
folder_path = "D:/JetBrains/sample/validation"

# 执行重命名操作
rename_images(folder_path)

# GLCM代码
# coding: utf-8
# The code is written by Linghui

import numpy as np
from skimage import data
from matplotlib import pyplot as plt
import get_glcm
import time
from PIL import Image
import cv2
from pathlib import Path


def main():
    pass


if __name__ == '__main__':

    main()

    start = time.time()

    print('---------------0. Parameter Setting-----------------')
    nbit = 8  # gray levels
    mi, ma = 0, 255  # max gray and min gray
    slide_window = 6  # sliding window
    step = [1, 2, 3, 4]  # step
    angle = [0, np.pi / 4, np.pi / 2, np.pi * 3 / 4]  # angle or direction

    print('-------------------1. Load Data---------------------')
    image = r"D:\JetBrains\sample\train\0.9999\frame_22.jpg"

    img = np.array(Image.open(image))  # If the image has multi-bands, it needs to be converted to grayscale image
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    print(img.shape)
    img = np.uint8(255.0 * (img - np.min(img)) / (np.max(img) - np.min(img)))  # normalization
    h, w = img.shape
    print('------------------2. Calcu GLCM---------------------')
    glcm = get_glcm.calcu_glcm(img, mi, ma, nbit, slide_window, step, angle)
    homogeneity = np.zeros((glcm.shape[2], glcm.shape[3], glcm.shape[4], glcm.shape[5]), dtype=np.float32)
    contrast = np.zeros((glcm.shape[2], glcm.shape[3], glcm.shape[4], glcm.shape[5]), dtype=np.float32)
    energy = np.zeros((glcm.shape[2], glcm.shape[3], glcm.shape[4], glcm.shape[5]), dtype=np.float32)
    correlation = np.zeros((glcm.shape[2], glcm.shape[3], glcm.shape[4], glcm.shape[5]), dtype=np.float32)

    print('-----------------3. Calcu Feature-------------------')
    # 
    for i in range(glcm.shape[2]):
        for j in range(glcm.shape[3]):
            glcm_cut = np.zeros((nbit, nbit, h, w), dtype=np.float32)
            glcm_cut = glcm[:, :, i, j, :, :]
            mean = get_glcm.calcu_glcm_mean(glcm_cut, nbit)
            variance = get_glcm.calcu_glcm_variance(glcm_cut, nbit)
            homogeneity[i, j, :, :] = get_glcm.calcu_glcm_homogeneity(glcm_cut, nbit)
            contrast[i, j, :, :] = get_glcm.calcu_glcm_contrast(glcm_cut, nbit)
            # dissimilarity = get_glcm.calcu_glcm_dissimilarity(glcm_cut, nbit)
            # entropy = get_glcm.calcu_glcm_entropy(glcm_cut, nbit)
            energy[i, j, :, :] = get_glcm.calcu_glcm_energy(glcm_cut, nbit)
            correlation[i, j, :, :] = get_glcm.calcu_glcm_correlation(glcm_cut, nbit)
            # Auto_correlation = get_glcm.calcu_glcm_Auto_correlation(glcm_cut, nbit)
    mean_homogeneity = np.mean(homogeneity, axis=(0, 1))
    mean_contrast = np.mean(contrast, axis=(0, 1))
    mean_energy = np.mean(energy, axis=(0, 1))
    mean_correlation = np.mean(correlation, axis=(0, 1))
    print('---------------4. Display and Result----------------')
    plt.figure(figsize=(6, 4.5))
    font = {'family': 'Times New Roman',
            'weight': 'normal',
            'size': 12,
            }

    plt.subplot(2, 3, 1)
    plt.tick_params(labelbottom=False, labelleft=False)
    plt.axis('off')
    plt.imshow(img, cmap='gray')
    plt.title('Original', font)

    plt.subplot(2, 3, 2)
    plt.tick_params(labelbottom=False, labelleft=False)
    plt.axis('off')
    plt.imshow(mean_homogeneity, cmap='gray')
    plt.title('Homogeneity', font)

    plt.subplot(2, 3, 3)
    plt.tick_params(labelbottom=False, labelleft=False)
    plt.axis('off')
    plt.imshow(mean_contrast, cmap='gray')
    plt.title('Contrast', font)

    plt.subplot(2, 3, 4)
    plt.tick_params(labelbottom=False, labelleft=False)
    plt.axis('off')
    plt.imshow(mean_energy, cmap='gray')
    plt.title('Energy', font)

    plt.subplot(2, 3, 5)
    plt.tick_params(labelbottom=False, labelleft=False)
    plt.axis('off')
    plt.imshow(mean_correlation, cmap='gray')
    plt.title('Correlation', font)
    save_dir = Path(r"C:\Users\23911\Desktop\paper\2025-07-28")
    save_dir.mkdir(parents=True, exist_ok=True)

    plt.imsave(str(save_dir / "original.png"), img, cmap='gray')
    plt.imsave(str(save_dir / "homogeneity.png"), mean_homogeneity, cmap='gray')
    plt.imsave(str(save_dir / "contrast.png"), mean_contrast, cmap='gray')
    plt.imsave(str(save_dir / "energy.png"), mean_energy, cmap='gray')
    plt.imsave(str(save_dir / "correlation.png"), mean_correlation, cmap='gray')

    plt.subplot(2, 5, 7)
    plt.tick_params(labelbottom=False, labelleft=False)
    plt.axis('off')
    plt.imshow(entropy, cmap='gray')
    plt.title('Entropy', font)

    plt.subplot(2, 5, 8)
    plt.tick_params(labelbottom=False, labelleft=False)
    plt.axis('off')
    plt.imshow(energy, cmap='gray')
    plt.title('Energy', font)

    plt.subplot(2, 5, 9)
    plt.tick_params(labelbottom=False, labelleft=False)
    plt.axis('off')
    plt.imshow(correlation, cmap='gray')
    plt.title('Correlation', font)

    plt.subplot(2, 5, 10)
    plt.tick_params(labelbottom=False, labelleft=False)
    plt.axis('off')
    plt.imshow(Auto_correlation, cmap='gray')
    plt.title('Auto Correlation', font)

    print(np.mean(mean_homogeneity))
    print(np.mean(mean_contrast))
    print(np.mean(mean_energy))
    print(np.mean(mean_correlation))
    plt.tight_layout(pad=0.5)
    plt.savefig('E:/Study/!Blibli/3.GLCM/GLCM/GLCM_Features.png'
                , format='png'
                , bbox_inches='tight'
                , pad_inches=0
                , dpi=300)
    plt.show()

    end = time.time()
print('Code run time:', end - start)
# coding: utf-8
# The code is written by Linghui

import numpy as np
import matplotlib.pyplot as plt
import cv2
import skimage
from PIL import Image
from skimage import data
from math import floor, ceil
from skimage.feature import graycomatrix, graycoprops


def main():
    pass


def image_patch(img2, slide_window, h, w):
    image = img2
    window_size = slide_window
    patch = np.zeros((slide_window, slide_window, h, w), dtype=np.uint8)

    for i in range(patch.shape[2]):
        for j in range(patch.shape[3]):
            patch[:, :, i, j] = img2[i: i + slide_window, j: j + slide_window]

    return patch


def calcu_glcm(img, vmin=0, vmax=255, nbit=64, slide_window=7, step=[2], angle=[0]):
    mi, ma = vmin, vmax
    h, w = img.shape

    # Compressed gray range：vmin: 0-->0, vmax: 256-1 -->nbit-1
    bins = np.linspace(mi, ma + 1, nbit + 1)
    img1 = np.digitize(img, bins) - 1

    # (512, 512) --> (slide_window, slide_window, 512, 512)
    img2 = cv2.copyMakeBorder(img1, floor(slide_window / 2), floor(slide_window / 2)
                              , floor(slide_window / 2), floor(slide_window / 2), cv2.BORDER_REPLICATE)  # 图像扩充

    patch = np.zeros((slide_window, slide_window, h, w), dtype=np.uint8)
    patch = image_patch(img2, slide_window, h, w)

    # Calculate GLCM (7, 7, 512, 512) --> (64, 64, 512, 512)
    # greycomatrix(image, distances, angles, levels=None, symmetric=False, normed=False)
    glcm = np.zeros((nbit, nbit, len(step), len(angle), h, w), dtype=np.uint8)
    for i in range(patch.shape[2]):
        for j in range(patch.shape[3]):
            glcm[:, :, :, :, i, j] = graycomatrix(patch[:, :, i, j], step, angle, levels=nbit)

    return glcm


def calcu_glcm_mean(glcm, nbit=64):
    '''
    calc glcm mean
    '''
    mean = np.zeros((glcm.shape[2], glcm.shape[3]), dtype=np.float32)
    for i in range(nbit):
        for j in range(nbit):
            mean += glcm[i, j] * i / (nbit) ** 2

    return mean


def calcu_glcm_variance(glcm, nbit=64):
    '''
    calc glcm variance
    '''
    mean = np.zeros((glcm.shape[2], glcm.shape[3]), dtype=np.float32)
    for i in range(nbit):
        for j in range(nbit):
            mean += glcm[i, j] * i / (nbit) ** 2

    variance = np.zeros((glcm.shape[2], glcm.shape[3]), dtype=np.float32)
    for i in range(nbit):
        for j in range(nbit):
            variance += glcm[i, j] * (i - mean) ** 2

    return variance


def calcu_glcm_homogeneity(glcm, nbit=64):
    '''
    calc glcm Homogeneity
    '''
    Homogeneity = np.zeros((glcm.shape[2], glcm.shape[3]), dtype=np.float32)
    for i in range(nbit):
        for j in range(nbit):
            Homogeneity += glcm[i, j] / (1. + (i - j) ** 2)

    return Homogeneity


def calcu_glcm_contrast(glcm, nbit=64):
    '''
    calc glcm contrast
    '''
    contrast = np.zeros((glcm.shape[2], glcm.shape[3]), dtype=np.float32)
    for i in range(nbit):
        for j in range(nbit):
            contrast += glcm[i, j] * (i - j) ** 2

    return contrast


def calcu_glcm_dissimilarity(glcm, nbit=64):
    '''
    calc glcm dissimilarity
    '''
    dissimilarity = np.zeros((glcm.shape[2], glcm.shape[3]), dtype=np.float32)
    for i in range(nbit):
        for j in range(nbit):
            dissimilarity += glcm[i, j] * np.abs(i - j)

    return dissimilarity


def calcu_glcm_entropy(glcm, nbit=64):
    '''
    calc glcm entropy 
    '''
    eps = 0.00001
    entropy = np.zeros((glcm.shape[2], glcm.shape[3]), dtype=np.float32)
    for i in range(nbit):
        for j in range(nbit):
            entropy -= glcm[i, j] * np.log10(glcm[i, j] + eps)

    return entropy


def calcu_glcm_energy(glcm, nbit=64):
    '''
    calc glcm energy or second moment
    '''
    energy = np.zeros((glcm.shape[2], glcm.shape[3]), dtype=np.float32)
    for i in range(nbit):
        for j in range(nbit):
            energy += glcm[i, j] ** 2

    return energy


def calcu_glcm_correlation(glcm, nbit=64):
    '''
    calc glcm correlation (Unverified result)
    '''

    x_mean = np.zeros((glcm.shape[2], glcm.shape[3]), dtype=np.float32)
    y_mean = np.zeros((glcm.shape[2], glcm.shape[3]), dtype=np.float32)
    for i in range(nbit):
        for j in range(nbit):
            x_mean += glcm[i, j] * i / (nbit) ** 2
            y_mean += glcm[i, j] * j / (nbit) ** 2

    x_variance = np.zeros((glcm.shape[2], glcm.shape[3]), dtype=np.float32)
    y_variance = np.zeros((glcm.shape[2], glcm.shape[3]), dtype=np.float32)
    Exy = np.zeros((glcm.shape[2], glcm.shape[3]), dtype=np.float32)
    for i in range(nbit):
        for j in range(nbit):
            x_variance += glcm[i, j] * (i - x_mean) ** 2
            y_variance += glcm[i, j] * (j - y_mean) ** 2
            Exy += i * j * glcm[i, j]
    x_variance += np.ones(x_variance.shape)
    y_variance += np.ones(y_variance.shape)
    correlation = (Exy - x_mean * y_mean) / (x_variance * y_variance)

    correlation = np.zeros((glcm.shape[2], glcm.shape[3]), dtype=np.float32)
    for i in range(nbit):
        for j in range(nbit):
            np.seterr(divide='ignore', invalid='ignore')
            correlation += ((i - mean) * (j - mean) * (glcm[i, j] ** 2)) / variance

    return correlation


def calcu_glcm_Auto_correlation(glcm, nbit=64):
    '''
    calc glcm auto correlation
    '''
    Auto_correlation = np.zeros((glcm.shape[2], glcm.shape[3]), dtype=np.float32)
    for i in range(nbit):
        for j in range(nbit):
            Auto_correlation += glcm[i, j] * i * j

    return Auto_correlation


if __name__ == '__main__':
    main()

# SURF主要核心代码：
import os
import cv2
import numpy as np
import math
import pandas as pd
from tqdm import tqdm

import os
import cv2
import numpy as np
import math
import pandas as pd
from tqdm import tqdm


def calculate_speed_variance(origin_points, next_points, t_stamp):
    # 计算每个点之间的平方差
    square_diff = np.sum((next_points - origin_points) ** 2, axis=1)
    # 计算平方差的平均值
    bubble_speed = np.sqrt(square_diff) / t_stamp
    # 计算平均速度
    bubble_speed_mean = bubble_speed.mean()
    # 计算速度方差
    bubble_speed_variance = np.mean((bubble_speed - bubble_speed_mean) ** 2)
    return bubble_speed_mean, bubble_speed_variance


def calculate_stability(good_matches, keypoints1, keypoints2):
    stability = len(good_matches) / (0.5 * (len(keypoints1) + len(keypoints2)))
    return stability


def process_folder(folder_path):
    files = sorted(os.listdir(folder_path))
    dynamic_features = []
    for i in tqdm(range(len(files) - 1), desc=f"Processing {folder_path}"):
        img1_path = os.path.join(folder_path, files[i])
        img2_path = os.path.join(folder_path, files[i + 1])

        img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
        img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)

        # 创建SURF对象
        surf = cv2.xfeatures2d_SURF.create(500)

        # 返回关键点信息和描述符
        keypoints1, descriptors1 = surf.detectAndCompute(img1, None)
        keypoints2, descriptors2 = surf.detectAndCompute(img2, None)

        # 初始化 Brute-Force 匹配器
        bf = cv2.BFMatcher()

        # 使用 Brute-Force 匹配器进行描述符的匹配
        matches = bf.knnMatch(descriptors1, descriptors2, k=2)

        # 只保留最佳匹配
        good_matche_points = []
        for m, n in matches:
            if m.distance < 0.5 * n.distance:  # 通过比率测试获取最佳匹配
                good_matche_points.append(m)

        # 从匹配中提取一一对应的特征点
        matched_keypoints1 = [keypoints1[m.queryIdx].pt for m in good_matche_points]
        matched_keypoints2 = [keypoints2[m.trainIdx].pt for m in good_matche_points]

        origin_points = np.array(matched_keypoints1)
        next_points = np.array(matched_keypoints2)

        bubble_speed_mean, bubble_speed_variance = calculate_speed_variance(origin_points, next_points, 0.2086)
        stability = calculate_stability(good_matche_points, keypoints1, keypoints2)

        dynamic_features.append((bubble_speed_mean, bubble_speed_variance, stability))

    return dynamic_features


# 处理文件夹中的所有子文件夹
root_folder = r'D:\JetBrains\images'
subfolders = [os.path.join(root_folder, folder) for folder in os.listdir(root_folder) if
              os.path.isdir(os.path.join(root_folder, folder))]

all_dynamic_features = []
for subfolder in subfolders:
    dynamic_features = process_folder(subfolder)
    all_dynamic_features.extend(dynamic_features)

# 将结果写入 Excel 表格
excel_file = 'dynamic_features_train.xlsx'
df = pd.DataFrame(all_dynamic_features, columns=["Speed Mean", "Speed Variance", "Stability"])
df.to_excel(excel_file, index=False)


def calculate_dynamic_features(folder_path_A, folder_path_B):
    # 获取文件夹 A 和文件夹 B 中的所有子文件夹路径
    subfolders_A = sorted([f.path for f in os.scandir(folder_path_A) if f.is_dir()])
    subfolders_B = sorted([f.path for f in os.scandir(folder_path_B) if f.is_dir()])

    # 创建一个列表来存储每组图像对的动态特征
    dynamic_features_list = []

    # 确保文件夹 A 和文件夹 B 中的子文件夹数目相同
    if len(subfolders_A) != len(subfolders_B):
        print("Error: The number of subfolders in folder A is not equal to the number of subfolders in folder B.")
        return dynamic_features_list

    # 遍历文件夹 A 和文件夹 B 中的每个子文件夹
    for subfolder_A, subfolder_B in tqdm(zip(subfolders_A, subfolders_B), desc='Processing Subfolders',
                                         total=len(subfolders_A)):
        # 获取子文件夹中的图像文件路径
        image_files_A = sorted(
            [f.path for f in os.scandir(subfolder_A) if f.is_file() and f.name.endswith(('.jpg', '.jpeg', '.png'))])
        image_files_B = sorted(
            [f.path for f in os.scandir(subfolder_B) if f.is_file() and f.name.endswith(('.jpg', '.jpeg', '.png'))])

        # 确保子文件夹中的图像文件数目相同
        if len(image_files_A) != len(image_files_B):
            print(
                f"Error: The number of images in subfolder {subfolder_A} is not equal to the number of images in subfolder {subfolder_B}.")
            continue

        # 遍历子文件夹中的每对图像文件
        for image_file_A, image_file_B in tqdm(zip(image_files_A, image_files_B), desc='Processing Images',
                                               total=len(image_files_A), leave=False):
            # 加载图像

            img1 = cv2.imread(image_file_A, cv2.IMREAD_GRAYSCALE)
            img2 = cv2.imread(image_file_B, cv2.IMREAD_GRAYSCALE)

            # 提取特征点
            surf = cv2.xfeatures2d_SURF.create(1000)  # 返回关键点信息和描述符
            image1 = img1.copy()
            image2 = img2.copy()
            keypoints1, descriptors1 = surf.detectAndCompute(image1, None)
            keypoints2, descriptors2 = surf.detectAndCompute(image2, None)
            # 在图像上绘制关键点（关键点利用Hessian算法找到）
            # DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS绘制特征点的时候绘制一个个带方向的圆

            # 特征点匹配
            bf = cv2.BFMatcher()

            # 使用 Brute-Force 匹配器进行描述符的匹配
            matches = bf.knnMatch(descriptors1, descriptors2, k=2)

            # 只保留最佳匹配
            goodMatchePoints = []
            for m, n in matches:
                if m.distance < 0.4 * n.distance:  # 通过比率测试获取最佳匹配
                    goodMatchePoints.append(m)
            matchedKeypoints1 = [keypoints1[m.queryIdx] for m in goodMatchePoints]
            matchedKeypoints2 = [keypoints2[m.trainIdx] for m in goodMatchePoints]
            # for i in range(len(matchePoints)):
            # print(matchePoints[i].queryIdx,matchePoints[i].trainIdx)#只是打印索引，无法寻找点
            # queryIdx为查询点索引，trainIdx为被查询点索引
            origin_x = np.zeros(len(goodMatchePoints))
            origin_y = np.zeros(len(goodMatchePoints))
            next_x = np.zeros(len(goodMatchePoints))
            next_y = np.zeros(len(goodMatchePoints))

            # 计算速度和方差
            for i in range(len(goodMatchePoints)):
                origin_x[i] = matchedKeypoints1[i].pt[0]
                origin_y[i] = matchedKeypoints1[i].pt[1]
                next_x[i] = matchedKeypoints2[i].pt[0]
                next_y[i] = matchedKeypoints2[i].pt[1]

            t_stamp = 0.15
            bubble_speed = np.zeros(len(goodMatchePoints))  # 得到速度
            for i in range(len(goodMatchePoints)):
                bubble_speed[i] = math.sqrt((next_x[i] - origin_x[i]) ** 2 + (next_y[i] - origin_y[i]) ** 2) / t_stamp
            bubble_speed_varience = 0
            bubble_speed_mean = bubble_speed.mean()

            # 计算稳定性
            stability = 1 - len(goodMatchePoints) / (0.5 * (len(keypoints1) + len(keypoints2)))

            # 将动态特征添加到列表中
            dynamic_features_df = pd.DataFrame(dynamic_features_list)

            # 然后拼接新的 DataFrame 对象
            new_features_df = pd.DataFrame({
                'Folder A': [os.path.basename(subfolder_A)],
                'Folder B': [os.path.basename(subfolder_B)],
                'Image A': [os.path.basename(image_file_A)],
                'Image B': [os.path.basename(image_file_B)],
                'Stability': [stability],
                'Speed Mean': [bubble_speed_mean],

            })

            dynamic_features_df = pd.concat([dynamic_features_df, new_features_df], ignore_index=True)

    return dynamic_features_df


# 文件夹 A 和文件夹 B 的路径
folder_path_A = "D:/JetBrains/sample/train"

# 计算图像动态特征
dynamic_features = calculate_dynamic_features(folder_path_A, folder_path_B)

# 打印结果
dynamic_features.to_excel('image_dynamic.xlsx', index=False)

import cv2
import numpy as np
import math
import logging as log

import glob

# img1=cv2.imread('D:/projects/video_flicker/video/result_45.jpg',cv2.IMREAD_GRAYSCALE)
# img2=cv2.imread('D:/projects/video_flicker/video/result_30.jpg',cv2.IMREAD_GRAYSCALE)
img1 = cv2.imread('test3.jpg', cv2.IMREAD_GRAYSCALE)
img2 = cv2.imread('test4.jpg', cv2.IMREAD_GRAYSCALE)
# 提取特征点
# 创建SURF对象
target_size = (256, 256)
img1 = cv2.resize(img1, target_size)
img2 = cv2.resize(img2, target_size)
surf = cv2.xfeatures2d_SURF.create(10000)  # 返回关键点信息和描述符
image1 = img1.copy()
image2 = img2.copy()
keypoint1, descriptor1 = surf.detectAndCompute(image1, None)
keypoint2, descriptor2 = surf.detectAndCompute(image2, None)
# 在图像上绘制关键点（关键点利用Hessian算法找到）
# DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS绘制特征点的时候绘制一个个带方向的圆
image1 = cv2.drawKeypoints(image=image1, keypoints=keypoint1, outImage=image1, color=(255, 0, 255),
                           flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
image2 = cv2.drawKeypoints(image=image2, keypoints=keypoint2, outImage=image2, color=(255, 0, 255),
                           flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

cv2.imshow('surf_keypoints1', image1)
cv2.imshow('surf_keypoints2', image2)

# 特征点匹配
matcher = cv2.FlannBasedMatcher()
matchePoints = matcher.match(descriptor1, descriptor2)
print(type(matchePoints), len(matchePoints), matchePoints[0])

# 提取最强匹配
minMatch = 1
maxMatch = 0

# for i in range(len(matchePoints)):
# print(matchePoints[i].queryIdx,matchePoints[i].trainIdx)#只是打印索引，无法寻找点
# queryIdx为查询点索引，trainIdx为被查询点索引
for i in range(len(matchePoints)):
    if minMatch > matchePoints[i].distance:
        minMatch = matchePoints[i].distance
    if maxMatch < matchePoints[i].distance:
        maxMatch = matchePoints[i].distance
print('最佳匹配值：', minMatch)
print('最差匹配值：', maxMatch)

goodMatchePoints = []
for i in range(len(matchePoints)):
    if matchePoints[i].distance < minMatch + (maxMatch - minMatch) / 4:
        goodMatchePoints.append(matchePoints[i])

outImg = None
outImg = cv2.drawMatches(img1, keypoint1, img2, keypoint2, goodMatchePoints, outImg, matchColor=(0, 0, 255),
                         flags=cv2.DRAW_MATCHES_FLAGS_NOT_DRAW_SINGLE_POINTS)
# 打印最匹配点
origin_x = np.zeros(len(goodMatchePoints))
origin_y = np.zeros(len(goodMatchePoints))
next_x = np.zeros(len(goodMatchePoints))
next_y = np.zeros(len(goodMatchePoints))
# 计算速度和方差
for i in range(len(goodMatchePoints)):
    print('goodMatch输出', goodMatchePoints[i].queryIdx)
    print('x坐标', keypoint2[goodMatchePoints[i].queryIdx].pt[0])
    print('y坐标', keypoint2[goodMatchePoints[i].queryIdx].pt[1])
    origin_x[i] = keypoint1[goodMatchePoints[i].queryIdx].pt[0]
    origin_y[i] = keypoint1[goodMatchePoints[i].queryIdx].pt[1]
    next_x[i] = keypoint2[goodMatchePoints[i].queryIdx].pt[0]
    next_y[i] = keypoint2[goodMatchePoints[i].queryIdx].pt[1]
    match = cv2.circle(image2, (int(keypoint2[goodMatchePoints[i].trainIdx].pt[0]),
                                int(keypoint2[goodMatchePoints[i].trainIdx].pt[1])), 4, (0, 255, 0), -1)
t_stamp = 0.15
bubble_speed = np.zeros(len(goodMatchePoints))  # 得到速度
for i in range(len(goodMatchePoints)):
    bubble_speed[i] = math.sqrt((next_x[i] - origin_x[i]) ** 2 + (next_y[i] - origin_y[i]) ** 2) / t_stamp
bubble_speed_varience = 0
bubble_speed_mean = bubble_speed.mean()
for i in range(len(goodMatchePoints)):
    bubble_speed_varience += (bubble_speed[i] - bubble_speed_mean) ** 2
bubble_speed_varience = bubble_speed_varience / len(goodMatchePoints)  # 得到方差

# 计算稳定性
stability = len(goodMatchePoints) / (0.5 * (len(keypoint1) + len(keypoint2)))

cv2.imshow('matche', outImg)
cv2.imshow('query', image2)  # 在image2上打印关键点位置
cv2.waitKey()
cv2.destroyAllWindows()

print(bubble_speed_mean)
print(bubble_speed_varience)
print()
