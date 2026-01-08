from PySide6.QtCore import QObject, Slot
from src.services.video_service import get_video_service
from src.services.analysis_service import get_analysis_service
from src.services.data_service import get_data_service


# 如果有 OPC 服务，也可以引入
# from src.services.opc_service import get_opc_service

class SystemController(QObject):
    """
    系统总控制器：负责协调各服务之间的通信与业务流程
    """

    def __init__(self):
        super().__init__()
        # 获取各服务单例
        self.video_service = get_video_service()
        self.analysis_service = get_analysis_service()
        self.data_service = get_data_service()
        # self.opc_service = get_opc_service()

        # 连接信号
        self._connect_signals()

    def _connect_signals(self):
        """建立服务间的信号连接"""
        # 1. 视频 -> 分析
        # 遍历所有相机 Worker，将原始帧信号连接到分析服务的处理槽
        for cam_idx, worker in self.video_service.workers.items():
            # raw_frame_ready 携带 (camera_index, numpy_image)
            # process_frame 接收 (camera_index, numpy_image)
            worker.raw_frame_ready.connect(
                self.analysis_service.worker.process_frame
            )

        # 2. 分析 -> 控制器 (用于分发结果)
        self.analysis_service.worker.result_ready.connect(self.on_analysis_result)

    @Slot(dict)
    def on_analysis_result(self, data: dict):
        """
        处理分析结果的回调函数
        data 包含: timestamp, camera_index, bubble_mean_diam, speed_mean 等
        """
        # 1. 保存到数据库
        # DataService 会负责缓存并按策略写入 SQLite/CSV
        self.data_service.record_data(data)

        # 2. (可选) 发送到 PLC/OPC
        # if self.opc_service:
        #     # 假设 OPC 标签映射逻辑已在 OpcService 中处理
        #     self.opc_service.write_analysis_data(data)

        # 3. (可选) 这里可以发射信号给 UI 更新图表
        # self.ui_update_signal.emit(data)

        # 打印调试信息 (仅在调试模式)
        # print(f"[{data['camera_index']}] 粒径:{data.get('bubble_mean_diam',0):.2f} 速度:{data.get('speed_mean',0):.2f}")