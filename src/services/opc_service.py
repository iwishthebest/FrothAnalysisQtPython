import csv
import re
import requests
import time
from typing import Dict, List, Optional, Any
from PySide6.QtCore import QObject, QThread, Signal

from src.services.logging_service import get_logging_service
from src.common.constants import LogCategory


class OPCWorker(QObject):
    """
    OPC 数据采集工作线程 (支持分频采集)
    - YJ开头的标签: 实时更新 (1秒)
    - KYFX开头的标签: 低频更新 (10分钟)
    """
    data_updated = Signal(dict)
    status_changed = Signal(bool, str)

    def __init__(self, opc_url: str, tag_list_file: str):
        super().__init__()
        self.opc_url = opc_url
        self.tag_list_file = tag_list_file
        self.logger = get_logging_service()
        self.running = False

        self._fast_tags: List[str] = []  # YJ
        self._slow_tags: List[str] = []  # KYFX
        self._data_cache: Dict[str, Any] = {}  # 全量缓存

        self._timeout = 10
        self._poll_interval = 1.0  # 快频间隔
        self._slow_interval = 600.0  # 慢频间隔 (10分钟)
        self._last_slow_update = 0.0

        self.session = requests.Session()

    def start_work(self):
        self.running = True
        self.logger.info("OPC 采集线程已启动 (分频模式)", LogCategory.OPC)
        self._load_tags()
        self._capture_loop()

    def stop_work(self):
        self.running = False
        try:
            self.session.close()
        except:
            pass

    def _load_tags(self):
        """加载并分类标签 (修复脏数据和#号问题)"""
        self._fast_tags = []
        self._slow_tags = []
        try:
            with open(self.tag_list_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if not row: continue

                    raw_str = row[0]
                    # 1. 清洗 等杂质
                    if "source:" in raw_str:
                        raw_str = raw_str.split(']')[-1]  # 取最后一个]后面的内容

                    # 2. 移除方括号
                    cleaned_line = re.sub(r'[\[\]]', '', raw_str).strip()

                    # 3. 添加前缀 (YJ./KYFX.)
                    tag_name = self._add_prefix(cleaned_line)

                    # 4. 存入原始名称 (不要在这里替换#，保持原样!)
                    if tag_name.startswith("KYFX."):
                        self._slow_tags.append(tag_name)
                    else:
                        self._fast_tags.append(tag_name)

            self.logger.info(f"标签加载完成: 快频(YJ) {len(self._fast_tags)}个, 慢频(KYFX) {len(self._slow_tags)}个",
                             LogCategory.OPC)
        except Exception as e:
            self.logger.error(f"读取标签列表失败: {e}", LogCategory.OPC)

    @staticmethod
    def _add_prefix(tag_name: str) -> str:
        if tag_name.startswith('yj_'):
            return f'YJ.{tag_name}'
        elif tag_name.startswith('kyfx_'):
            return f'KYFX.{tag_name}'
        return tag_name

    def _capture_loop(self):
        while self.running:
            loop_start = time.time()
            try:
                current_time = time.time()
                tags_to_fetch = []

                # 1. 始终包含快频标签 (YJ)
                tags_to_fetch.extend(self._fast_tags)

                # 2. 定时包含慢频标签 (KYFX - 10分钟一次)
                is_slow_update = False
                if (current_time - self._last_slow_update) >= self._slow_interval:
                    tags_to_fetch.extend(self._slow_tags)
                    self._last_slow_update = current_time
                    is_slow_update = True
                    # self.logger.info("触发 KYFX 慢频更新", LogCategory.OPC)

                # 3. 执行采集
                new_data = self._fetch_process_data(tags_to_fetch)

                if new_data:
                    self._data_cache.update(new_data)
                    # 发送全量数据给界面和存储服务
                    self.data_updated.emit(self._data_cache.copy())

                    msg = "OPC在线" + (" (全量)" if is_slow_update else "")
                    self.status_changed.emit(True, msg)
                elif not self._data_cache:
                    self.status_changed.emit(False, "数据为空")

            except Exception as e:
                self.logger.error(f"OPC 采集异常: {e}", LogCategory.OPC)
                self.status_changed.emit(False, "采集错误")

            elapsed = time.time() - loop_start
            sleep_time = max(0.1, self._poll_interval - elapsed)
            QThread.msleep(int(sleep_time * 1000))

    def _fetch_process_data(self, tags: List[str]) -> Dict[str, Any]:
        if not tags:
            return {}
        try:
            tag_param = ",".join(tags)
            params = {"tagNameList": tag_param}

            # 使用 GET (双重转义已在 _load_tags 处理)
            response = self.session.get(
                url=self.opc_url,
                params=params,
                timeout=self._timeout
            )

            if response.status_code == 200:
                try:
                    data = response.json()
                except:
                    self.logger.error(f"JSON解析失败: {response.text}", LogCategory.OPC)
                    return {}

                # 检查数据有效性
                data_list = data.get("data", [])
                if not data_list:
                    # 如果返回 200 但 data 为空，说明标签名不对
                    self.logger.warning(f"⚠️ 请求成功但无数据! 响应: {data}", LogCategory.OPC)
                    return {}

                values = {}
                for item in data_list:
                    tag_name = item.get('TagName', '').strip()
                    try:
                        val = float(item['Value'])
                        values[tag_name] = {'value': val, 'timestamp': item['Time'], 'quality': 'Good'}
                    except:
                        values[tag_name] = {'value': 0.0, 'timestamp': item.get('Time'), 'quality': 'Bad'}

                self.logger.info(f"✅ 成功解析 {len(values)} 个标签", LogCategory.OPC)
                return values
            else:
                self.logger.warning(f"OPC请求返回状态码: {response.status_code}", LogCategory.OPC)
                return {}
        except requests.exceptions.RequestException:
            return {}
        except Exception as e:
            self.logger.error(f"获取数据异常: {e}", LogCategory.OPC)
            return {}


class OPCService(QObject):
    def __init__(self, opc_url: str = "http://10.12.18.2:8081/open/realdata/snapshot/batchGet",
                 tag_list_file: str = "resources/tags/tagList.csv"):
        super().__init__()
        self.logger = get_logging_service()
        self.opc_url = opc_url
        self.tag_list_file = tag_list_file
        self.thread: Optional[QThread] = None
        self.worker: Optional[OPCWorker] = None
        self._init_worker()

    def _init_worker(self):
        self.thread = QThread()
        self.worker = OPCWorker(self.opc_url, self.tag_list_file)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.start_work)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def get_worker(self) -> OPCWorker:
        return self.worker

    def cleanup(self):
        if self.worker: self.worker.stop_work()
        if self.thread:
            self.thread.quit()
            self.thread.wait(1000)
        self.logger.info("OPC服务已停止", LogCategory.OPC)


_opc_service_instance = None


def get_opc_service() -> OPCService:
    global _opc_service_instance
    if _opc_service_instance is None:
        _opc_service_instance = OPCService()
    return _opc_service_instance
