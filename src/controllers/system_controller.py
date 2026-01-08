from src.services.video_service import get_video_service
from src.services.analysis_service import get_analysis_service


class SystemController:
    def __init__(self):
        self.video_service = get_video_service()
        self.analysis_service = get_analysis_service()

        # 连接信号
        self._connect_signals()

    def _connect_signals(self):
        # 遍历所有相机 worker
        for cam_idx, worker in self.video_service.workers.items():
            # 将 VideoService 的原始帧信号 连接到 AnalysisService 的处理槽
            # 注意：需确保 AnalysisService 暴露了对应的 signal 用于跨线程通信
            worker.raw_frame_ready.connect(
                self.analysis_service.worker.process_frame
            )

        # 处理分析结果
        self.analysis_service.worker.result_ready.connect(self.on_analysis_result)

    def on_analysis_result(self, data):
        # 1. 更新 UI 上的图表
        # 2. 调用 DataService 保存到数据库
        # 3. 调用 OpcService 发送给 PLC
        print(f"收到分析结果: 气泡尺寸={data.get('bubble_mean_diam', 0):.2f}")