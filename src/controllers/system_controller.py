from PySide6.QtCore import QObject, Slot
from config.config_system import config_manager
from src.services.video_service import get_video_service
from src.services.analysis_service import get_analysis_service
from src.services.data_service import get_data_service
from src.services.opc_service import get_opc_service
from src.services.logging_service import get_logging_service


class SystemController(QObject):
    """
    系统总控制器：负责协调各服务之间的通信与业务流程
    """

    def __init__(self):
        super().__init__()
        # 获取各服务单例
        self.logger = get_logging_service()
        self.video_service = get_video_service()
        self.analysis_service = get_analysis_service()
        self.data_service = get_data_service()
        self.opc_service = get_opc_service()
        # 绑定配置管理器
        self.config_manager = config_manager

        # 连接信号
        self._connect_signals()

        # 初始化服务状态
        self.init_services()

    def init_services(self):
        """初始化并启动后台服务"""
        try:
            # 1. 启动其他核心服务 (如数据库、视频流等)
            # self.data_service.start() # DataService 通常在 Application 中启动
            # self.video_service.start()

            # 2. 根据配置决定是否启动 OPC 服务
            if self.config_manager.system_config.network.opc_enabled:
                self.logger.info("配置已启用 OPC 服务，正在启动...", "SYSTEM")
                self.opc_service.start()
            else:
                self.logger.info("配置已禁用 OPC 服务，跳过启动", "SYSTEM")

        except Exception as e:
            self.logger.error(f"服务启动异常: {e}", "SYSTEM")

    def handle_settings_changed(self, new_config_dict: dict):
        """
        处理设置变更信号
        该方法应连接到 SettingsPage.settings_changed 信号
        """
        self.logger.info("检测到配置变更，正在评估服务状态...", "SYSTEM")

        # 重新加载最新的网络配置
        net_config = self.config_manager.system_config.network

        # === OPC 服务动态启停逻辑 ===
        if net_config.opc_enabled:
            # 如果配置启用，且服务未运行，则启动
            if not self.opc_service.is_running():
                self.logger.info("OPC 服务被启用，正在启动...", "SYSTEM")
                self.opc_service.start()
            else:
                # 如果已经在运行，重启以应用可能的 URL/频率 变更
                self.logger.info("OPC 配置参数更新，重启服务...", "SYSTEM")
                self.opc_service.update_config(net_config)
        else:
            # 如果配置禁用，且服务正在运行，则停止
            if self.opc_service.is_running():
                self.logger.info("OPC 服务被禁用，正在停止...", "SYSTEM")
                self.opc_service.stop()

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
