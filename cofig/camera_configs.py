"""
相机配置管理
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any
from enum import Enum


class CameraPosition(Enum):
    """相机位置枚举"""
    LEAD_ROUGH = "铅快粗泡沫"
    LEAD_CLEAN_1 = "铅精一泡沫"
    LEAD_CLEAN_2 = "铅精二泡沫"
    LEAD_CLEAN_3 = "铅精三泡沫"


@dataclass
class CameraConfig:
    """相机配置"""
    name: str
    rtsp_url: str
    position: CameraPosition
    enabled: bool = True
    timeout: int = 10
    reconnect_interval: int = 5
    max_retries: int = 10

    def validate(self) -> bool:
        """验证配置有效性"""
        if not self.name.strip():
            return False
        if not self.rtsp_url.startswith('rtsp://'):
            return False
        if self.timeout <= 0:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['position'] = self.position.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CameraConfig':
        """从字典创建实例"""
        data = data.copy()
        if isinstance(data.get('position'), str):
            for position in CameraPosition:
                if position.value == data['position']:
                    data['position'] = position
                    break
            else:
                # 默认位置
                data['position'] = CameraPosition.LEAD_ROUGH
        return cls(**data)

    @classmethod
    def create_default_configs(cls) -> list:
        """创建默认相机配置列表"""
        return [
            cls(
                name="铅快粗泡沫相机",
                rtsp_url="rtsp://admin:fkqxk010@192.168.1.101:554/Streaming/Channels/101",
                position=CameraPosition.LEAD_ROUGH,
                enabled=True
            ),
            cls(
                name="铅精一泡沫相机",
                rtsp_url="rtsp://admin:fkqxk010@192.168.1.102:554/Streaming/Channels/101",
                position=CameraPosition.LEAD_CLEAN_1,
                enabled=True
            ),
            cls(
                name="铅精二泡沫相机",
                rtsp_url="rtsp://admin:fkqxk010@192.168.1.103:554/Streaming/Channels/101",
                position=CameraPosition.LEAD_CLEAN_2,
                enabled=True
            ),
            cls(
                name="铅精三泡沫相机",
                rtsp_url="rtsp://admin:fkqxk010@192.168.1.104:554/Streaming/Channels/101",
                position=CameraPosition.LEAD_CLEAN_3,
                enabled=True
            )
        ]
