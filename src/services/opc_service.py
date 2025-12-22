"""
src/services/opc_service.py
OPC 服务 - 增强版 (防网络中断/自动重连/日志降噪)
"""
import csv
import re
import requests
import time
from typing import Dict, List, Optional, Any
from PySide6.QtCore import QObject, QThread, Signal, QMutex

from src.services.logging_service import get_logging_service
from src.common.constants import LogCategory
from config.config_system import config_manager


class OPCWorker(QObject):
    """
    OPC 数据采集工作线程 (支持分频采集 + 智能重连)
    """
    data_updated = Signal(dict)
    status_changed = Signal(bool, str)

    def __init__(self, opc_url: str, tag_list_file: str):
        super().__init__()
        self.opc_url = opc_url
        self.tag_list_file = tag_list_file
        self.logger = get_logging_service()
        self.running = False

        self._fast_tags: List[str] = []
        self._slow_tags: List[str] = []
        self._data_cache: Dict[str, Any] = {}

        # 配置参数
        net_config = config_manager.get_network_config()
        self._timeout = net_config.timeout
        self._normal_interval = net_config.fast_tag_interval # 正常间隔
        self._slow_interval = net_config.slow_tag_interval

        # [新增] 错误退避机制参数
        self._current_interval = self._normal_interval
        self._error_count = 0
        self._max_interval = 30.0 # 最大等待30秒

        self._last_slow_update = 0.0
        self.session = None # 延迟初始化

    def start_work(self):
        self.running = True
        self._recreate_session()
        self.logger.info(f"OPC 采集线程已启动", LogCategory.OPC)
        self._load_tags()
        self._capture_loop()

    def stop_work(self):
        self.running = False
        self._close_session()

    def _recreate_session(self):
        """[新增] 重置 HTTP 会话"""
        self._close_session()
        self.session = requests.Session()
        # 设置重试策略 (可选)
        adapter = requests.adapters.HTTPAdapter(max_retries=3)
        self.session.mount('http://', adapter)

    def _close_session(self):
        if self.session:
            try:
                self.session.close()
            except:
                pass
            self.session = None

    def _load_tags(self):
        """加载并分类标签"""
        self._fast_tags = []
        self._slow_tags = []
        try:
            with open(self.tag_list_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if not row: continue
                    raw = row[0]
                    if "source:" in raw: raw = raw.split(']')[-1]
                    cleaned = re.sub(r'[\[\]]', '', raw).strip()
                    tag_name = self._add_prefix(cleaned)

                    if tag_name.startswith("KYFX."):
                        self._slow_tags.append(tag_name)
                    else:
                        self._fast_tags.append(tag_name)

            self.logger.info(f"标签加载: 快频 {len(self._fast_tags)} / 慢频 {len(self._slow_tags)}", LogCategory.OPC)
        except Exception as e:
            self.logger.error(f"读取标签列表失败: {e}", LogCategory.OPC)

    @staticmethod
    def _add_prefix(tag_name: str) -> str:
        if tag_name.startswith('yj_'): return f'YJ.{tag_name}'
        elif tag_name.startswith('kyfx_'): return f'KYFX.{tag_name}'
        return tag_name

    def _capture_loop(self):
        while self.running:
            loop_start = time.time()

            try:
                current_time = time.time()
                tags_to_fetch = []
                tags_to_fetch.extend(self._fast_tags)

                is_slow_update = False
                if (current_time - self._last_slow_update) >= self._slow_interval:
                    tags_to_fetch.extend(self._slow_tags)
                    self._last_slow_update = current_time
                    is_slow_update = True

                # 执行采集
                new_data = self._fetch_process_data(tags_to_fetch)

                if new_data:
                    # === 成功逻辑 ===
                    self._data_cache.update(new_data)
                    self.data_updated.emit(self._data_cache.copy())

                    msg = "OPC在线" + (" (全量)" if is_slow_update else "")
                    self.status_changed.emit(True, msg)

                    # [新增] 成功后重置错误计数和间隔
                    if self._error_count > 0:
                        self.logger.info("OPC 连接已恢复", LogCategory.OPC)
                        self._error_count = 0
                        self._current_interval = self._normal_interval

                else:
                    # 业务层面的空数据
                    if not self._data_cache:
                        self.status_changed.emit(False, "数据为空")

            except Exception as e:
                # === 失败逻辑 ===
                self._error_count += 1

                # 错误退避：每多错一次，等待时间加长，直到30秒
                self._current_interval = min(self._max_interval, self._current_interval * 2)

                # 仅在初次错误或长时间错误时打印日志，防止刷屏
                if self._error_count == 1 or self._error_count % 10 == 0:
                    self.logger.error(f"OPC 采集失败({self._error_count}次): {e}", LogCategory.OPC)
                    # [关键] 遇到网络错误，主动重置 Session
                    self._recreate_session()

                self.status_changed.emit(False, f"网络错误 {self._error_count}")

            # 动态休眠
            elapsed = time.time() - loop_start
            sleep_time = max(0.1, self._current_interval - elapsed)

            # 分段休眠以便快速响应退出
            steps = int(sleep_time * 10)
            for _ in range(steps):
                if not self.running: break
                QThread.msleep(100)


    def _fetch_process_data(self, tags: List[str]) -> Dict[str, Any]:
        if not tags or not self.session: return {}
        try:
            tag_string = ",".join(tags)
            # 保持 params 方式，让 requests 处理编码
            params = {"tagNameList": tag_string}

            # 优先使用配置的 URL
            if self.opc_url is None:
                return {}

            response = self.session.get(
                url=self.opc_url,
                params=params,
                timeout=self._timeout
            )

            if response.status_code == 200:
                data = response.json()
                values = {}
                for item in data.get("data", []):
                    tag_name = item['TagName'].strip()
                    try:
                        val = float(item['Value'])
                        if val == -9999.0:
                            values[tag_name] = {'value': val, 'timestamp': item['Time'], 'quality': 'Bad'}
                        else:
                            values[tag_name] = {'value': val, 'timestamp': item['Time'], 'quality': 'Good'}
                    except:
                        values[tag_name] = {'value': 0.0, 'timestamp': item.get('Time', ''), 'quality': 'Bad'}
                return values
            else:
                self.logger.warning(f"OPC状态码: {response.status_code}", LogCategory.OPC)
                return {}
        except requests.exceptions.RequestException as e:
            # 抛出异常给外层处理（触发退避逻辑）
            raise e
        except Exception as e:
            self.logger.error(f"解析异常: {e}", LogCategory.OPC)
            return {}


class OPCService(QObject):
    def __init__(self, opc_url: str = None, tag_list_file: str = "resources/tags/tagList.csv"):
        super().__init__()
        # 优先从配置读取
        if opc_url is None:
            opc_url = config_manager.get_network_config().opc_server_url

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