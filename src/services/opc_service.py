import csv
import re
import requests
import time
from typing import Dict, List, Optional, Any
from PySide6.QtCore import QObject, QThread, Signal

from src.services.logging_service import get_logging_service
from src.common.constants import LogCategory


class OPCWorker(QObject):
    """OPC 数据采集工作线程"""
    data_updated = Signal(dict)
    status_changed = Signal(bool, str)

    def __init__(self, opc_url: str, tag_list_file: str):
        super().__init__()
        self.opc_url = opc_url
        self.tag_list_file = tag_list_file
        self.logger = get_logging_service()
        self.running = False
        self._tag_cache = None
        self._timeout = 10
        self._poll_interval = 1.0

        # [优化] 使用 Session 复用连接
        self.session = requests.Session()

    def start_work(self):
        self.running = True
        self.logger.info("OPC 采集线程已启动", LogCategory.OPC)
        self._load_tags()
        self._capture_loop()

    def stop_work(self):
        self.running = False
        try:
            self.session.close()
        except:
            pass

    def _load_tags(self):
        tag_list = []
        try:
            with open(self.tag_list_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row:
                        cleaned_line = re.sub(r'[\[\]]', '', row[0])
                        with_prefix = self._add_prefix(cleaned_line.strip())
                        tag_list.append(with_prefix)
            self._tag_cache = tag_list
            self.logger.info(f"已加载 {len(tag_list)} 个监测标签", LogCategory.OPC)
        except Exception as e:
            self.logger.error(f"读取标签列表失败: {e}", LogCategory.OPC)
            self._tag_cache = []

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
                data = self._fetch_process_data()
                if data:
                    self.data_updated.emit(data)
                    self.status_changed.emit(True, "OPC在线")
                else:
                    self.status_changed.emit(False, "数据为空")
            except Exception as e:
                self.logger.error(f"OPC 采集循环异常: {e}", LogCategory.OPC)
                self.status_changed.emit(False, f"错误: {str(e)[:20]}")

            elapsed = time.time() - loop_start
            sleep_time = max(0.1, self._poll_interval - elapsed)
            QThread.msleep(int(sleep_time * 1000))

    def _fetch_process_data(self) -> Dict[str, Any]:
        if not self._tag_cache:
            return {}
        try:
            tag_param = ",".join(self._tag_cache)
            # 构造参数字典
            payload = {"tagNameList": tag_param}

            # === [修改] 优先尝试 POST 请求 ===
            try:
                # 尝试以表单形式提交 (application/x-www-form-urlencoded)
                response = self.session.post(
                    url=self.opc_url,
                    data=payload,
                    timeout=self._timeout
                )
                # 如果服务器不支持 POST (返回 404 或 405)，会抛出错误，进入 except 块
                response.raise_for_status()

            except Exception:
                # === [回退] 如果 POST 失败，回退到 GET 并打印调试 URL ===
                response = self.session.get(
                    url=self.opc_url,
                    params=payload,
                    timeout=self._timeout
                )
                # [调试] 打印实际发送的 URL，检查 # 是否变成了 %23
                # 这一行会在日志中显示最终生成的 URL，请截图发给我分析
                if "#" in tag_param:
                    self.logger.warning(f"GET请求URL调试: {response.url}", LogCategory.OPC)

            if response.status_code == 200:
                data = response.json()
                values = {}
                for item in data.get("data", []):
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
