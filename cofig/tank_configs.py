"""
浮选槽配置管理
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Tuple
from enum import Enum


class TankType(Enum):
    """浮选槽类型枚举"""
    ROUGH = "粗选"
    CLEAN_1 = "精选一"
    CLEAN_2 = "精选二"
    CLEAN_3 = "精选三"


@dataclass
class TankConfig:
    """浮选槽配置"""
    name: str
    type: TankType
    color: str
    level_range: Tuple[float, float] = (0.5, 2.5)
    dosing_range: Tuple[float, float] = (0, 200)
    default_level: float = 1.2
    default_dosing: float = 50

    def validate(self) -> bool:
        """验证配置有效性"""
        if not self.name.strip():
            return False
        if not self.color.startswith('#'):
            return False
        if self.level_range[0] >= self.level_range[1]:
            return False
        if self.dosing_range[0] >= self.dosing_range[1]:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['type'] = self.type.value
        # 转换tuple为list以便JSON序列化
        data['level_range'] = list(self.level_range)
        data['dosing_range'] = list(self.dosing_range)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TankConfig':
        """从字典创建实例"""
        data = data.copy()
        if isinstance(data.get('type'), str):
            for tank_type in TankType:
                if tank_type.value == data['type']:
                    data['type'] = tank_type
                    break
            else:
                data['type'] = TankType.ROUGH

        # 转换list为tuple
        if isinstance(data.get('level_range'), list):
            data['level_range'] = tuple(data['level_range'])
        if isinstance(data.get('dosing_range'), list):
            data['dosing_range'] = tuple(data['dosing_range'])

        return cls(**data)

    @classmethod
    def create_default_configs(cls) -> list:
        """创建默认浮选槽配置列表"""
        return [
            cls(
                name="铅快粗槽",
                type=TankType.ROUGH,
                color="#3498db",
                level_range=(0.5, 2.5),
                dosing_range=(0, 200)
            ),
            cls(
                name="铅精一槽",
                type=TankType.CLEAN_1,
                color="#2ecc71",
                level_range=(0.5, 2.5),
                dosing_range=(0, 200)
            ),
            cls(
                name="铅精二槽",
                type=TankType.CLEAN_2,
                color="#e74c3c",
                level_range=(0.5, 2.5),
                dosing_range=(0, 200)
            ),
            cls(
                name="铅精三槽",
                type=TankType.CLEAN_3,
                color="#9b59b6",
                level_range=(0.5, 2.5),
                dosing_range=(0, 200)
            )
        ]