import csv
import re
import requests
import time
import threading
from typing import Dict, List, Optional, Any
from PySide6.QtCore import QObject, QThread, Signal, QMutex

from src.services.logging_service import get_logging_service
from src.common.constants import LogCategory


class OPCWorker(QObject):
    """
    OPC 数据采集工作线程
    负责：在后台循环请求 OPC 数据 -> 解析 -> 发送信号
    """
    # 信号：发送最新采集的数据字典
    data_updated = Signal(dict)
    # 信号：发送连接状态 (是否连接, 状态消息)
    status_changed = Signal(bool, str)

    def __init__(self, opc_url: str, tag_list_file: str):
        super().__init__()
        self.opc_url = opc_url
        self.tag_list_file = tag_list_file
        self.logger = get_logging_service()
        self.running = False
        self._tag_cache = None
        self._timeout = 10
        self._poll_interval = 1.0  # 采集间隔(秒)

        # === [新增] 创建 Session 对象 ===
        self.session = requests.Session()

    def start_work(self):
        """线程启动入口"""
        self.running = True
        self.logger.info("OPC 采集线程已启动", LogCategory.OPC)
        self._load_tags()
        self._capture_loop()

    def stop_work(self):
        """停止工作"""
        self.running = False
        # === [新增] 关闭 Session ===
        try:
            self.session.close()
        except:
            pass

    def _load_tags(self):
        """加载标签列表"""
        tag_list = []
        try:
            with open(self.tag_list_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row_num, row in enumerate(reader, 1):
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
        """为标签添加前缀 (保持原有逻辑)"""
        if tag_name.startswith('yj_'):
            return f'YJ.{tag_name}'
        elif tag_name.startswith('kyfx_'):
            return f'KYFX.{tag_name}'
        return tag_name

    def _capture_loop(self):
        """主采集循环"""
        while self.running:
            loop_start = time.time()

            try:
                # 执行采集
                data = self._fetch_process_data()

                # 发送数据
                if data:
                    self.data_updated.emit(data)
                    self.status_changed.emit(True, "OPC在线")
                else:
                    self.status_changed.emit(False, "数据为空")

            except Exception as e:
                self.logger.error(f"OPC 采集循环异常: {e}", LogCategory.OPC)
                self.status_changed.emit(False, f"错误: {str(e)[:20]}")

            # 控制采集频率 (默认1秒一次)
            elapsed = time.time() - loop_start
            sleep_time = max(0.1, self._poll_interval - elapsed)

            # 使用 QThread.msleep 避免阻塞事件循环，但在这里 time.sleep 也可以，
            # 因为我们在子线程中。为了响应 stop_work 更快，可以用分段 sleep。
            QThread.msleep(int(sleep_time * 1000))

    def _fetch_process_data(self) -> Dict[str, Any]:
        """执行一次 HTTP 请求获取数据"""
        if not self._tag_cache:
            return {}

        try:
            tag_param = ",".join(self._tag_cache)
            params = {"tagNameList": tag_param}

            # === [修改] 使用 self.session.get 而不是 requests.get ===
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
                        values[tag_name] = {
                            'value': val,
                            'timestamp': item['Time'],
                            'quality': 'Good'
                        }
                    except (ValueError, TypeError):
                        # 转换失败记录为 None 或 0
                        values[tag_name] = {
                            'value': 0.0,
                            'timestamp': item['Time'],
                            'quality': 'Bad'
                        }
                return values
            else:
                self.logger.warning(f"OPC请求返回状态码: {response.status_code}", LogCategory.OPC)
                return {}

        except requests.exceptions.RequestException:
            # 网络错误不需要打印堆栈，以免刷屏
            return {}
        except Exception as e:
            self.logger.error(f"获取数据异常: {e}", LogCategory.OPC)
            return {}


class OPCService(QObject):
    """
    OPC服务管理类 (重构版 - 管理 Worker 线程)
    """

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
        """初始化工作线程"""
        self.thread = QThread()
        self.worker = OPCWorker(self.opc_url, self.tag_list_file)
        self.worker.moveToThread(self.thread)

        # 连接生命周期信号
        self.thread.started.connect(self.worker.start_work)
        self.thread.finished.connect(self.thread.deleteLater)

        # 启动
        self.thread.start()

    def get_worker(self) -> OPCWorker:
        """获取 Worker 实例以便连接信号"""
        return self.worker

    def cleanup(self):
        """清理资源"""
        if self.worker:
            self.worker.stop_work()
        if self.thread:
            self.thread.quit()
            self.thread.wait(1000)
        self.logger.info("OPC服务已停止", LogCategory.OPC)

    # === 为了兼容旧代码保留的方法 (从缓存或直接返回空) ===
    # 注意：为了最佳性能，UI层应该改为连接 worker.data_updated 信号，
    # 而不是调用这些同步方法。但保留它们可以防止报错。

    def get_process_data(self) -> Dict[str, Any]:
        """已弃用：请使用信号机制"""
        return {}

    def get_specific_tag_value(self, tag_name: str) -> Optional[float]:
        """已弃用：请使用信号机制"""
        return None


# 单例模式实例
_opc_service_instance = None


def get_opc_service() -> OPCService:
    """获取OPC服务单例实例"""
    global _opc_service_instance
    if _opc_service_instance is None:
        _opc_service_instance = OPCService()
    return _opc_service_instance