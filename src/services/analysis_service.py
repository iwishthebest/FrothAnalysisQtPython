import numpy as np
import cv2
import time
import logging
from PySide6.QtCore import QObject, Signal, QThread, Slot

# 引用您提供的算法库
from src.utils.feature_extract import FrothFeatureExtractor
from src.common.constants import LogCategory  # 假设存在
from src.services.logging_service import get_logging_service


class AnalysisWorker(QObject):
    """
    分析工作线程：负责在后台运行耗时的图像处理算法
    """
    result_ready = Signal(dict)  # 发送分析结果
    finished = Signal()

    def __init__(self):
        super().__init__()
        self.logger = get_logging_service()
        self.prev_frame = None  # 用于动态特征：存储上一帧
        self.last_process_time = 0  # 用于计算时间间隔
        self.processing = False  # 防重入标志

    @Slot(int, object) # 接收相机索引和图像数据
    def process_frame(self, camera_index: int, image):
        if self.processing:
            return  # 如果上一帧还在处理，直接丢弃当前帧（防止积压）

        self.processing = True
        try:
            current_time = time.time()
            results = {
                "timestamp": current_time,
                "camera_index": camera_index
            }

            # 1. 提取静态特征 (颜色, 纹理, 形态学)
            # 直接调用您 utils 中的静态方法
            static_feats = FrothFeatureExtractor.extract_all_static_features(image)
            results.update(static_feats)

            # 2. 提取动态特征 (需要前后两帧)
            if self.prev_frame is not None:
                interval = current_time - self.last_process_time
                dynamic_feats = FrothFeatureExtractor.extract_dynamic_features(
                    self.prev_frame, image, time_interval=interval
                )
                results.update(dynamic_feats)
            else:
                # 第一帧无法计算动态特征，给默认值
                results.update({'speed_mean': 0.0, 'stability': 0.0})

            # 更新状态
            self.prev_frame = image.copy()
            self.last_process_time = current_time

            # 发送结果
            self.result_ready.emit(results)

        except Exception as e:
            self.logger.error(f"分析线程异常: {e}", LogCategory.SYSTEM)
        finally:
            self.processing = False


class AnalysisService(QObject):
    """
    服务管理类：管理分析线程的生命周期
    """

    def __init__(self):
        super().__init__()
        self.thread = QThread()
        self.worker = AnalysisWorker()
        self.worker.moveToThread(self.thread)
        self.thread.start()

    def handle_frame(self, camera_idx, q_image):
        """
        接收来自 VideoService 的 QImage，转换为 numpy 并传给 Worker
        注意：这里需要将 QImage 转回 numpy (cv2格式)，因为算法层用的是 numpy
        """
        # QImage -> numpy转换逻辑
        # 注意：为了性能，这一步转换最好在 VideoService 发出信号前做，
        # 或者 VideoService 发出两种信号：一种给UI(QImage)，一种给算法(numpy)
        # 这里演示在 Service 层转换：

        ptr = q_image.bits()
        ptr.setsize(q_image.byteCount())
        # 假设是 RGB888
        arr = np.array(ptr).reshape(q_image.height(), q_image.width(), 3)
        # 算法层通常需要 BGR (OpenCV默认) 或 RGB，需确认 feature_extract.py 的预期
        # feature_extract.py 中主要用 split 或 cvtColor，通常兼容，但建议统一
        img_np = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

        # 通过 Qt 的信号槽机制调用子线程方法，实现线程安全
        # 这里需要利用 QMetaObject.invokeMethod 或 信号连接
        # 最简单的方式是 AnalysisService 定义一个信号连接到 Worker 的 Slot
        pass

    def cleanup(self):
        self.thread.quit()
        self.thread.wait()


# 单例模式获取
_analysis_service = None


def get_analysis_service():
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = AnalysisService()
    return _analysis_service