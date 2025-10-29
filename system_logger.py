from datetime import datetime


class SystemLogger:
    """系统日志管理器"""

    def __init__(self):
        self.logs = {
            'monitoring': [],
            'control': [],
            'history': [],
            'settings': []
        }
        self.max_entries = 100  # 每个日志最大条目数

    def add_log(self, category, message, level="INFO"):
        """添加日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"

        if category in self.logs:
            self.logs[category].append(log_entry)
            # 保持日志条目数量不超过最大值
            if len(self.logs[category]) > self.max_entries:
                self.logs[category].pop(0)

    def get_logs(self, category):
        """获取指定类别的日志"""
        return self.logs.get(category, [])

    def clear_logs(self, category=None):
        """清空日志"""
        if category:
            if category in self.logs:
                self.logs[category].clear()
        else:
            for cat in self.logs:
                self.logs[cat].clear()
