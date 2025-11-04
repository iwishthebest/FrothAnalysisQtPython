import os
import cv2
import numpy as np


def calculate_max_gradient(image_path):
    """计算单个图像的最大梯度幅值"""
    # 读取图像并转换为灰度图
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"无法加载图像: {image_path}")

    # 计算梯度
    grad_x = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)
    grad_mag = np.sqrt(grad_x ** 2 + grad_y ** 2)

    # 找到最大梯度幅值
    max_grad_mag = np.max(grad_mag)
    return max_grad_mag


def batch_calculate_max_gradients(folder_path):
    """批量计算文件夹下所有图像的最大梯度幅值"""
    results = {}
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            image_path = os.path.join(folder_path, filename)
            try:
                max_grad_mag = calculate_max_gradient(image_path)
                results[filename] = max_grad_mag
                print(f"图像 {filename} 的最大梯度幅值: {max_grad_mag:.2f}")
            except Exception as e:
                print(f"处理图像 {filename} 时出错: {e}")

    return results


def calculate_brightness(image_path):
    """计算单个图像的亮度信息"""
    # 读取图像并转换为灰度图
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"无法加载图像: {image_path}")

    # 计算图像的平均亮度
    mean_brightness = np.mean(img)
    return mean_brightness


def batch_calculate_brightness(folder_path):
    """批量计算文件夹下所有图像的亮度信息"""
    results = {}
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            image_path = os.path.join(folder_path, filename)
            try:
                brightness = calculate_brightness(image_path)
                results[filename] = brightness
                print(f"图像 {filename} 的亮度: {brightness:.2f}")
            except Exception as e:
                print(f"处理图像 {filename} 时出错: {e}")

    return results


# 使用示例
if __name__ == "__main__":
    folder_path = r"D:\dataCollect\data\extracted_frames_check\20251029"  # 替换为您的图像文件夹路径
    max_gradients = batch_calculate_brightness(folder_path)
