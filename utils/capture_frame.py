import numpy as np
import cv2

def capture_frame(camera_index):
    """模拟视频帧捕获 - 根据相机索引生成不同的泡沫图像"""
    try:
        width, height = 640, 480
        # 创建不同相机的基础图像
        base_colors = [
            (100, 150, 200),  # 蓝色调 - 铅快粗泡沫
            (200, 200, 100),  # 黄色调 - 铅精一泡沫
            (150, 100, 100),  # 红色调 - 铅精二泡沫
            (100, 200, 150)  # 绿色调 - 铅精三泡沫
        ]

        # 创建基础图像
        frame = np.full((height, width, 3), base_colors[camera_index], dtype=np.uint8)

        # 添加一些随机噪声模拟真实图像
        noise = np.random.randint(0, 30, (height, width, 3), dtype=np.uint8)
        frame = cv2.add(frame, noise)

        # 根据泡沫类型添加不同的模拟内容
        if camera_index == 0:  # 铅快粗泡沫
            cv2.putText(frame, "铅快粗泡沫", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            # 添加大泡沫模拟
            for _ in range(30):
                x, y = np.random.randint(0, width), np.random.randint(0, height // 2)
                radius = np.random.randint(15, 30)  # 较大的气泡
                cv2.circle(frame, (x, y), radius, (255, 255, 255), -1)

        elif camera_index == 1:  # 铅精一泡沫
            cv2.putText(frame, "铅精一泡沫", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            # 添加中等泡沫模拟
            for _ in range(50):
                x, y = np.random.randint(0, width), np.random.randint(0, height // 2)
                radius = np.random.randint(8, 20)  # 中等气泡
                cv2.circle(frame, (x, y), radius, (255, 255, 255), -1)

        elif camera_index == 2:  # 铅精二泡沫
            cv2.putText(frame, "铅精二泡沫", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            # 添加小泡沫模拟
            for _ in range(70):
                x, y = np.random.randint(0, width), np.random.randint(0, height // 2)
                radius = np.random.randint(5, 15)  # 较小的气泡
                cv2.circle(frame, (x, y), radius, (255, 255, 255), -1)

        elif camera_index == 3:  # 铅精三泡沫
            cv2.putText(frame, "铅精三泡沫", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            # 添加精细泡沫模拟
            for _ in range(100):
                x, y = np.random.randint(0, width), np.random.randint(0, height // 2)
                radius = np.random.randint(3, 10)  # 精细气泡
                cv2.circle(frame, (x, y), radius, (255, 255, 255), -1)

        return True, frame
    except Exception as e:
        print(f"捕获相机 {camera_index} 视频帧时出错: {e}")
        return False, None

