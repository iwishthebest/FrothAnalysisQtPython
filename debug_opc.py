import sys
import os
import signal
from PySide6.QtCore import QCoreApplication, Slot, QTimer

# === 1. 环境配置 ===
# 将项目根目录加入 python 路径，确保能 import src 模块
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from src.services.opc_service import OPCService
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保你在项目根目录下运行此脚本: python debug_opc.py")
    sys.exit(1)

# 处理 Ctrl+C 中断，防止无法退出
signal.signal(signal.SIGINT, signal.SIG_DFL)


class OPCDebugger:
    def __init__(self):
        print(">>> 正在初始化 OPC 服务...")

        # 实例化服务
        # 注意：确保 'resources/tags/tagList.csv' 文件存在，或者传入绝对路径
        self.service = OPCService(
            opc_url="http://10.12.18.2:8081/open/realdata/snapshot/batchGet",  # 你的测试 URL
            tag_list_file="resources/tags/tagList.csv"
        )

        # 获取 Worker 实例以连接信号
        self.worker = self.service.get_worker()

        if not self.worker:
            print("错误: 无法获取 OPC Worker")
            return

        # === 2. 连接信号 ===
        self.worker.data_updated.connect(self.on_data_received)
        self.worker.status_changed.connect(self.on_status_changed)

        print(">>> OPC 服务已启动，正在等待数据 (按 Ctrl+C 退出)...")

    @Slot(dict)
    def on_data_received(self, data):
        """接收到数据时的回调"""
        print("-" * 50)
        print(f"[数据更新] 收到 {len(data)} 个标签的数据")

        # 打印前 5 个数据作为示例
        count = 0
        for tag, info in data.items():
            print(f"  {tag:<30} | 值: {info['value']:<10} | 质量: {info['quality']}")
            count += 1
            if count >= 5:
                print("  ... (更多数据已省略)")
                break

        # 获取原本请求的所有标签
        requested_tags = set(self.worker._fast_tags + self.worker._slow_tags)
        received_tags = set(data.keys())

        missing_tags = requested_tags - received_tags
        if missing_tags:
            print(f"⚠️ 警告：以下 {len(missing_tags)} 个标签未返回数据：")
            for tag in missing_tags:
                print(f"  - {tag}")

    @Slot(bool, str)
    def on_status_changed(self, connected, message):
        """状态变更时的回调"""
        status_icon = "🟢" if connected else "🔴"
        print(f"{status_icon} [状态变更] 连接: {connected}, 消息: {message}")

    def cleanup(self):
        print("\n>>> 正在清理资源...")
        self.service.cleanup()


def main():
    # 创建 Qt 核心应用 (非 GUI)
    app = QCoreApplication(sys.argv)

    debugger = OPCDebugger()

    # 运行事件循环
    try:
        sys.exit(app.exec())
    except Exception:
        debugger.cleanup()


if __name__ == "__main__":
    main()
