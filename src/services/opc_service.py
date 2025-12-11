import csv
import re
import requests
import time
from typing import Dict, List, Optional, Any
from PySide6.QtCore import QObject, QThread, Signal, QMutex

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

        # 标签分组
        self._fast_tags: List[str] = []  # YJ
        self._slow_tags: List[str] = []  # KYFX

        # 本地全量数据缓存 (防止分频采集导致发出的数据不全)
        self._data_cache: Dict[str, Any] = {}

        self._timeout = 10
        self._poll_interval = 1.0  # 快频间隔 1s
        self._slow_interval = 600.0  # 慢频间隔 10分钟
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
        """加载并分类标签"""
        self._fast_tags = []
        self._slow_tags = []
        try:
            with open(self.tag_list_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row:
                        cleaned_line = re.sub(r'[\[\]]', '', row[0])
                        # 双重转义修复 # 号问题
                        if '#' in cleaned_line:
                            cleaned_line = cleaned_line.replace('#', '%23')

                        tag_name = self._add_prefix(cleaned_line.strip())

                        # === 分类逻辑 ===
                        if tag_name.startswith("KYFX."):
                            self._slow_tags.append(tag_name)
                        else:
                            # YJ 或其他默认为快频
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

                # 1. 始终添加快频标签
                tags_to_fetch.extend(self._fast_tags)

                # 2. 检查是否需要更新慢频标签 (10分钟一次)
                is_slow_update = False
                if (current_time - self._last_slow_update) >= self._slow_interval:
                    tags_to_fetch.extend(self._slow_tags)
                    self._last_slow_update = current_time
                    is_slow_update = True
                    # self.logger.info("触发 KYFX 慢频更新", LogCategory.OPC)

                # 3. 执行采集
                new_data = self._fetch_process_data(tags_to_fetch)

                if new_data:
                    # 更新本地缓存
                    self._data_cache.update(new_data)

                    # 发送全量缓存数据 (保证UI始终有所有数据)
                    self.data_updated.emit(self._data_cache.copy())

                    msg = "OPC在线"
                    if is_slow_update:
                        msg += " (全量刷新)"
                    self.status_changed.emit(True, msg)
                else:
                    # 如果采集失败且缓存为空，才报空
                    if not self._data_cache:
                        self.status_changed.emit(False, "数据为空")

            except Exception as e:
                self.logger.error(f"OPC 采集循环异常: {e}", LogCategory.OPC)
                self.status_changed.emit(False, f"错误: {str(e)[:20]}")

            elapsed = time.time() - loop_start
            sleep_time = max(0.1, self._poll_interval - elapsed)
            QThread.msleep(int(sleep_time * 1000))

    def _fetch_process_data(self, tags: List[str]) -> Dict[str, Any]:
        if not tags:
            return {}
        try:
            # 1. 手动拼接参数字符串
            # 我们在这里手动将 # 替换为 %23，这是标准的 URL 编码
            # requests 库如果不使用 params 参数，通常不会对已存在的 URL 字符串进行二次转义
            tag_string = ",".join(tags)

            # [核心技巧] 手动编码特殊字符
            # 将 # 替换为 %23。注意：不要替换 : (冒号)，因为OPC服务器似乎需要冒号
            tag_string_encoded = tag_string.replace("#", "%23")

            # 2. 构造完整 URL
            # 假设 self.opc_url 结尾没有 ?，如果有则需要判断
            delimiter = "&" if "?" in self.opc_url else "?"
            full_url = f"{self.opc_url}{delimiter}tagNameList={tag_string_encoded}"

            # [调试] 打印即将发送的绝对 URL，请与 Postman Console 中的 URL 对比
            # if "%23" in full_url:
            #     self.logger.info(f"发送URL: {full_url}", LogCategory.OPC)

            # 3. 发送请求 (不使用 params 参数)
            response = self.session.get(
                url=full_url,
                timeout=self._timeout
            )

            if response.status_code == 200:
                data = response.json()
                values = {}
                for item in data.get("data", []):
                    # 获取原始标签名 (去除前后空格)
                    tag_name = item['TagName'].strip()
                    try:
                        val = float(item['Value'])
                        values[tag_name] = {'value': val, 'timestamp': item['Time'], 'quality': 'Good'}
                    except:
                        values[tag_name] = {'value': 0.0, 'timestamp': item['Time'], 'quality': 'Bad'}
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

    def get_process_data(self) -> Dict[str, Any]:
        return {}

    def get_specific_tag_value(self, tag_name: str) -> Optional[float]:
        return None


_opc_service_instance = None


def get_opc_service() -> OPCService:
    global _opc_service_instance
    if _opc_service_instance is None:
        _opc_service_instance = OPCService()
    return _opc_service_instance