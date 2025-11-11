import csv
import re
import requests
from typing import Dict, List, Optional, Any
from logging_service import get_logging_service
from ..common.constants import LogCategory


class OPCService:
    """OPC数据服务类"""

    def __init__(self, opc_url: str = "http://10.12.18.2:8081/open/realdata/snapshot/batchGet",
                 tag_list_file: str = "resources/tags/tagList.csv"):
        """
        初始化OPC服务

        Args:
            opc_url: OPC服务器URL
            tag_list_file: 标签列表文件路径
        """
        self.opc_url = opc_url
        self.tag_list_file = tag_list_file
        self.logger = get_logging_service()
        self._tag_cache = None
        self._timeout = 10

    def get_tag_list(self) -> List[str]:
        """从CSV文件获取标签列表"""
        if self._tag_cache is not None:
            return self._tag_cache

        tag_list = []
        try:
            with open(self.tag_list_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row_num, row in enumerate(reader, 1):
                    if row:  # 跳过空行
                        cleaned_line = re.sub(r'[\[\]]', '', row[0])
                        with_prefix = self._add_prefix(cleaned_line.strip())
                        tag_list.append(with_prefix)

            self._tag_cache = tag_list
            self.logger.info(f"已加载 {len(tag_list)} 个标签", LogCategory.OPC)
            return tag_list

        except FileNotFoundError:
            self.logger.error(f"标签文件不存在: {self.tag_list_file}", LogCategory.OPC)
            return []
        except Exception as e:
            self.logger.error(f"读取标签列表失败: {e}", LogCategory.OPC)
            return []

    @staticmethod
    def _add_prefix(tag_name: str) -> str:
        """为标签添加前缀"""
        if tag_name.startswith('yj_'):
            return f'YJ.{tag_name}'
        elif tag_name.startswith('kyfx_'):
            return f'KYFX.{tag_name}'
        return tag_name

    def get_process_data(self, custom_tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        获取工艺过程数据

        Args:
            custom_tags: 自定义标签列表，如果为None则使用默认标签

        Returns:
            包含标签数据的字典
        """
        try:
            # 使用自定义标签或默认标签
            if custom_tags:
                tag_list = custom_tags
            else:
                tag_list = self.get_tag_list()

            if not tag_list:
                self.logger.error("标签列表为空，无法获取数据", "WARNING")
                return {}

            tag_param = ",".join(tag_list)
            params = {"tagNameList": tag_param}

            response = requests.get(url=self.opc_url, params=params, timeout=self._timeout)

            if response.status_code == 200:
                data = response.json()
                values = {}

                for item in data.get("data", []):
                    tag_name = item['TagName'].strip()
                    try:
                        value = float(item['Value'])
                        values[tag_name] = {
                            'value': value,
                            'timestamp': item['Time'],
                            'quality': 'Good'
                        }
                    except (ValueError, TypeError):
                        values[tag_name] = {
                            'value': None,
                            'timestamp': item['Time'],
                            'quality': 'Bad'
                        }

                self.logger.debug(f"成功获取 {len(values)} 个数据点", LogCategory.OPC)
                return values

            else:
                self.logger.error(f"OPC请求失败，状态码：{response.status_code}", LogCategory.OPC)
                return {}

        except requests.exceptions.Timeout:
            self.logger.error("OPC请求超时", LogCategory.OPC)
            return {}
        except requests.exceptions.ConnectionError:
            self.logger.error("无法连接到OPC服务器", LogCategory.OPC)
            return {}
        except Exception as e:
            self.logger.error(f"获取工艺数据时异常：{e}", LogCategory.OPC)
            return {}

    def get_specific_tag_value(self, tag_name: str) -> Optional[float]:
        """获取特定标签的数值"""
        data = self.get_process_data([tag_name])
        if tag_name in data and data[tag_name]['value'] is not None:
            return float(data[tag_name]['value'])
        return None

    def get_lead_grade_data(self) -> Dict[str, Any]:
        """获取铅品位相关数据"""
        lead_tags = [tag for tag in self.get_tag_list() if 'grade_Pb' in tag]
        return self.get_process_data(lead_tags)

    def get_zinc_grade_data(self) -> Dict[str, Any]:
        """获取锌品位相关数据"""
        zinc_tags = [tag for tag in self.get_tag_list() if 'grade_Zn' in tag]
        return self.get_process_data(zinc_tags)

    def test_connection(self) -> bool:
        """测试OPC服务器连接"""
        try:
            # 使用一个简单的标签进行测试
            test_tags = ["KYFX.kyfx_gqxk_grade_Pb"]
            data = self.get_process_data(test_tags)
            return len(data) > 0
        except Exception:
            return False

    def set_timeout(self, timeout: int):
        """设置请求超时时间"""
        self._timeout = timeout
        self.logger.info(f"设置OPC请求超时为 {timeout} 秒", LogCategory.OPC)


# 单例模式实例
_opc_service_instance = None


def get_opc_service() -> OPCService:
    """获取OPC服务单例实例"""
    global _opc_service_instance
    if _opc_service_instance is None:
        _opc_service_instance = OPCService()
    return _opc_service_instance