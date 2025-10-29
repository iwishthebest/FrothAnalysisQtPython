from datetime import datetime


class SystemLogger:
    """系统日志管理器"""

    def __init__(self):
        self.logs = []
        self.max_entries = 100  # 日志最大条目数

    def info(self, message):
        self.add_log(message, level="INFO")

    def debug(self, message):
        self.add_log(message, level="DEBUG")

    def error(self, message):
        self.add_log(message, level="ERROR")

    def add_log(self, message, level="INFO"):
        """添加日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"

        self.logs.append(log_entry)
        # 保持日志条目数量不超过最大值
        if len(self.logs) > self.max_entries:
            self.logs.pop(0)

    def get_logs(self):
        """获取所有日志"""
        return self.logs

    def clear_logs(self):
        """清空日志"""
        self.logs.clear()
