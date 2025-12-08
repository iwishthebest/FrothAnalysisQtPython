import cv2
import numpy as np
from typing import Optional, List, Dict, Any
from config.config_system import config_manager, CameraConfig
from src.services.logging_service import get_logging_service
from src.common.constants import LogCategory
from src.utils.video_utils import RTSPStreamReader


class VideoService:
    """视频服务管理类"""

    def __init__(self):
        """初始化视频服务"""
        self.logger = get_logging_service()
        self.camera_configs = config_manager.get_camera_configs()
        self.rtsp_readers: Dict[int, RTSPStreamReader] = {}
        self.simulation_mode = False
        self._initialize_cameras()

    def _initialize_cameras(self):
        """初始化相机连接"""
        # 先清除现有连接
        self.cleanup()

        for i, config in enumerate(self.camera_configs):
            # 跳过未使用相机
            if not config.enabled:
                continue

            if not self.simulation_mode:
                # 尝试初始化真实相机
                reader = RTSPStreamReader(
                    rtsp_url=config.rtsp_url,
                    window_size=tuple(map(int, config.resolution.split('x'))),
                    reconnect_interval=config.reconnect_interval,
                    max_retries=config.max_retries
                )
                if reader.start():
                    self.rtsp_readers[i] = reader
                    self.logger.info(f"相机 {i} ({config.name}) 初始化成功", LogCategory.VIDEO)
                else:
                    self.logger.warning(f"相机 {i} ({config.name}) 初始化失败，切换到模拟模式", LogCategory.VIDEO)
                    self.simulation_mode = True
                    break
            else:
                self.logger.info(f"相机 {i} ({config.name}) 使用模拟模式", LogCategory.VIDEO)

    def capture_frame(self, camera_index: int, timeout: int = 2) -> Optional[np.ndarray]:
        """
        捕获指定相机的帧

        Args:
            camera_index: 相机索引
            timeout: 超时时间（秒）

        Returns:
            视频帧或None
        """

        if camera_index < 0 or camera_index >= len(self.camera_configs):
            self.logger.error(f"无效的相机索引: {camera_index}", LogCategory.VIDEO)
            return None

        try:
            camera_enabled = self.camera_configs[camera_index].enabled
            if not camera_enabled or camera_index not in self.rtsp_readers or self.simulation_mode:
                return self._capture_simulated_frame(camera_index)
            else:
                return self.rtsp_readers[camera_index].get_frame(timeout=timeout)

        except Exception as e:
            self.logger.error(f"捕获相机 {camera_index} 视频帧时出错: {e}", LogCategory.VIDEO)
            return self._capture_simulated_frame(camera_index)

    def _capture_simulated_frame(self, camera_index: int) -> np.ndarray:
        """模拟视频帧捕获"""
        config = self.camera_configs[camera_index]
        width, height = tuple(map(int, config.resolution.split('x')))

        # 创建基础图像
        frame = np.full((height, width, 3), config.simulation_color, dtype=np.uint8)

        # 添加噪声
        noise = np.random.randint(0, 30, (height, width, 3), dtype=np.uint8)
        frame = cv2.add(frame, noise)

        # 添加标签文本
        cv2.putText(frame, config.name, (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # 添加状态文本
        status_text = "模拟模式" if self.simulation_mode else "未连接"
        cv2.putText(frame, status_text, (50, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        # 添加泡沫气泡
        for _ in range(config.bubble_count if hasattr(config, 'bubble_count') else 50):
            x, y = np.random.randint(0, width), np.random.randint(0, height // 2)
            radius_range = getattr(config, 'bubble_radius_range', (8, 20))
            radius = np.random.randint(radius_range[0], radius_range[1])
            cv2.circle(frame, (x, y), radius, (255, 255, 255), -1)

        return frame

    def get_camera_status(self, camera_index: int) -> Dict[str, Any]:
        """
        获取相机状态信息

        Args:
            camera_index: 相机索引

        Returns:
            相机状态字典
        """
        if camera_index < 0 or camera_index >= len(self.camera_configs):
            return {"status": "invalid", "message": "无效的相机索引", "name": ""}

        config = self.camera_configs[camera_index]
        camera_enabled = config.enabled

        if self.simulation_mode:
            return {
                "status": "simulation",
                "name": config.name,
                "message": "模拟模式"
            }
        elif not camera_enabled:
            return {
                "status": "disabled",
                "name": config.name,
                "message": "已禁用"
            }
        elif camera_index in self.rtsp_readers:
            reader = self.rtsp_readers[camera_index]
            return {
                "status": "connected",
                "name": config.name,
                "message": "连接正常",
                "retry_count": reader.retry_count
            }
        else:
            return {
                "status": "disconnected",
                "name": config.name,
                "message": "连接断开"
            }

    def get_all_cameras_status(self) -> List[Dict[str, Any]]:
        """获取所有相机状态"""
        return [self.get_camera_status(i) for i in range(len(self.camera_configs))]

    def reconnect_camera(self, camera_index: int) -> bool:
        """
        重新连接指定相机

        Args:
            camera_index: 相机索引

        Returns:
            是否重新连接成功
        """
        if self.simulation_mode:
            self.logger.warning("模拟模式下无法重新连接真实相机", LogCategory.VIDEO)
            return False

        # 先断开现有连接
        self.disconnect_camera(camera_index)

        config = self.camera_configs[camera_index]
        reader = RTSPStreamReader(
            rtsp_url=config.rtsp_url,
            window_size=tuple(map(int, config.resolution.split('x'))),
            reconnect_interval=config.reconnect_interval,
            max_retries=config.max_retries
        )

        if reader.start():
            self.rtsp_readers[camera_index] = reader
            self.logger.info(f"相机 {camera_index} 重新连接成功", LogCategory.VIDEO)
            return True
        else:
            self.logger.error(f"相机 {camera_index} 重新连接失败", LogCategory.VIDEO)
            return False

    def disconnect_camera(self, camera_index: int) -> bool:
        """
        断开指定相机连接

        Args:
            camera_index: 相机索引

        Returns:
            是否断开成功
        """
        if camera_index in self.rtsp_readers:
            self.rtsp_readers[camera_index].stop()
            del self.rtsp_readers[camera_index]
            self.logger.info(f"相机 {camera_index} 已断开连接", LogCategory.VIDEO)
            return True
        return False

    def set_simulation_mode(self, enabled: bool):
        """
        设置模拟模式

        Args:
            enabled: 是否启用模拟模式
        """
        self.simulation_mode = enabled
        if enabled:
            # 关闭所有真实相机连接
            for reader in self.rtsp_readers.values():
                reader.stop()
            self.rtsp_readers.clear()
            self.logger.info("已切换到模拟模式", LogCategory.VIDEO)
        else:
            self.logger.info("已切换到真实相机模式", LogCategory.VIDEO)
            self._initialize_cameras()

    def set_camera_resolution(self, camera_index: int, width: int, height: int):
        """
        设置相机分辨率

        Args:
            camera_index: 相机索引
            width: 宽度
            height: 高度
        """
        if 0 <= camera_index < len(self.camera_configs):
            # 更新配置
            self.camera_configs[camera_index].resolution = f"{width}x{height}"
            config_manager.save_config()

            # 更新读取器
            if camera_index in self.rtsp_readers:
                self.rtsp_readers[camera_index].set_window_size(width, height)
                self.logger.info(f"相机 {camera_index} 分辨率设置为 {width}x{height}", LogCategory.VIDEO)

    def cleanup(self):
        """清理资源"""
        for reader in self.rtsp_readers.values():
            reader.stop()
        self.rtsp_readers.clear()
        self.logger.info("视频服务资源已清理", LogCategory.VIDEO)


# 单例模式实例
_video_service_instance = None


def get_video_service() -> VideoService:
    """获取视频服务单例实例"""
    global _video_service_instance
    if _video_service_instance is None:
        _video_service_instance = VideoService()
    return _video_service_instance


# 兼容性函数（为了保持原有代码的调用方式）
def capture_frame_simulate(camera_index: int) -> Optional[np.ndarray]:
    """
    模拟视频帧捕获（兼容性函数）

    Args:
        camera_index: 相机索引

    Returns:
        视频帧或None
    """
    service = get_video_service()
    service.set_simulation_mode(True)  # 确保使用模拟模式
    return service.capture_frame(camera_index)