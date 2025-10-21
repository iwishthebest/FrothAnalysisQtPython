import sys
from PySide6.QtWidgets import QApplication
from FoamMonitoringSystem import FoamMonitoringSystem


def main():
    """主函数"""
    try:
        app = QApplication(sys.argv)

        # 设置应用程序样式
        app.setStyle('Fusion')

        # 创建主窗口
        window = FoamMonitoringSystem()

        # 显示窗口并最大化
        window.showMaximized()

        print("铅浮选监测系统启动成功")
        return app.exec()

    except Exception as e:
        print(f"启动应用程序时出错: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
