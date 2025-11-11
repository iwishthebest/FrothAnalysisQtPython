"""
界面配置管理
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Tuple


@dataclass
class UIConfig:
    """界面配置"""
    refresh_rate: int = 100  # ms
    theme: str = "light"
    language: str = "zh-CN"
    max_data_points: int = 1000
    window_size: Tuple[int, int] = (1400, 900)

    def validate(self) -> bool:
        """验证配置有效性"""
        if self.refresh_rate <= 0:
            return False
        if self.max_data_points <= 0:
            return False
        if self.window_size[0] <= 0 or self.window_size[1] <= 0:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 转换tuple为list以便JSON序列化
        data['window_size'] = list(self.window_size)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UIConfig':
        """从字典创建实例"""
        data = data.copy()
        # 转换list为tuple
        if isinstance(data.get('window_size'), list):
            data['window_size'] = tuple(data['window_size'])
        return cls(**data)

    def get_theme_colors(self) -> Dict[str, str]:
        """获取主题颜色配置"""
        if self.theme == "dark":
            return {
                'background': '#2c3e50',
                'foreground': '#ecf0f1',
                'primary': '#3498db',
                'secondary': '#2980b9',
                'accent': '#e74c3c'
            }
        else:  # light theme
            return {
                'background': '#ecf0f1',
                'foreground': '#2c3e50',
                'primary': '#3498db',
                'secondary': '#2980b9',
                'accent': '#e74c3c'
            }
