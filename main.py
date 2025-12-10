# main.py
import sys
from datetime import datetime
from src.core.application import create_application
# [新增] 引入日志服务
from src.services.logging_service import get_logging_service
from src.common.constants import LogCategory


def main():
    """主函数"""
    logger = get_logging_service()  # [新增] 获取 logger
    # [新增] 打印日志文件的绝对路径，方便查找
    import os
    logger.info(f"当前日志文件路径: {os.path.abspath('logs/system_' + datetime.now().strftime('%Y%m%d') + '.log')}",
                LogCategory.SYSTEM)

    try:
        # 创建应用程序
        app = create_application()

        # [新增] 记录启动日志
        logger.info("系统正在启动...", LogCategory.SYSTEM)

        # 运行应用程序
        exit_code = app.run()

        # 关闭应用程序
        app.shutdown()

        # [新增] 记录退出日志
        logger.info(f"系统已退出，退出码: {exit_code}", LogCategory.SYSTEM)

        return exit_code

    except Exception as e:
        # [修改] print -> logger.critical
        # print(f"应用程序错误: {e}")
        logger.critical(f"应用程序发生未捕获异常: {e}", LogCategory.SYSTEM)
        return 1


if __name__ == '__main__':
    sys.exit(main())
