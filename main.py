import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import Qt
from FoamMonitoringSystem import FoamMonitoringSystem


def main():
    """主函数"""
    try:
        app = QApplication(sys.argv)

        # 设置应用程序样式
        app.setStyle('Fusion')
        # 关键：手动设置颜色方案为浅色，覆盖系统设置
        app.styleHints().setColorScheme(Qt.ColorScheme.Light)  # 固定为浅色[3](@ref)
        # 创建主窗口
        window = FoamMonitoringSystem()
        window.show()
        # 显示窗口并最大化
        # window.showMaximized()
        window.logger.add_log("铅浮选监测系统启动成功", "INFO")
        # print("铅浮选监测系统启动成功")
        return app.exec()

    except Exception as e:
        # window.logger.add_log("monitoring", f"启动应用程序时出错: {e}", "ERROR")
        print(f"启动应用程序时出错: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
