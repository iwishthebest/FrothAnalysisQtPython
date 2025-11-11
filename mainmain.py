# main.py - 重构后的主函数
import sys
from src.core.application import create_application


def main():
    """主函数"""
    try:
        # 创建应用程序
        app = create_application()

        # 运行应用程序
        exit_code = app.run()

        # 关闭应用程序
        app.shutdown()

        return exit_code

    except Exception as e:
        print(f"应用程序错误: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
