"""
铅浮选过程工况智能监测与控制系统 - 主程序包

这是项目的根包，包含整个应用程序的主要模块和组件。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
_project_root = Path(__file__).parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# 版本信息
__version__ = "2.1.0"
__author__ = "智能监测技术团队"
__email__ = "support@intelligent-monitoring.com"
__description__ = "铅浮选过程工况智能监测与控制系统"
__license__ = "Proprietary"
__copyright__ = "Copyright 2024 智能监测技术团队"


# 项目配置
class ProjectConfig:
    """项目配置类"""

    # 项目根目录
    ROOT_DIR = _project_root

    # 数据目录
    DATA_DIR = ROOT_DIR / "data"
    LOGS_DIR = ROOT_DIR / "logs"
    CONFIG_DIR = ROOT_DIR / "config"
    RESOURCES_DIR = ROOT_DIR / "resources"

    # 子目录映射
    SUBDIRS = {
        'views': ROOT_DIR / "views",
        'models': ROOT_DIR / "models",
        'controllers': ROOT_DIR / "controllers",
        'utils': ROOT_DIR / "utils",
        'tests': ROOT_DIR / "tests"
    }

    @classmethod
    def setup_directories(cls):
        """创建必要的目录结构"""
        directories = [
            cls.DATA_DIR,
            cls.LOGS_DIR,
            cls.CONFIG_DIR,
            cls.RESOURCES_DIR / "icons",
            cls.RESOURCES_DIR / "styles",
            cls.RESOURCES_DIR / "images"
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_path(cls, path_type, *subpaths):
        """获取项目路径"""
        base_path = getattr(cls, path_type.upper() + '_DIR', cls.ROOT_DIR)
        return base_path.joinpath(*subpaths)


# 导出主要模块
try:

    # 工具模块
    from .utils.system_logger import SystemLogger
    from .utils.process_data import capture_frame_simulate, get_process_data

    # 模型模块
    from .models.rtsp_stream_reader import RTSPStreamReader

except ImportError as e:
    print(f"导入模块时出错: {e}")

# 导出主要类
__all__ = [
    'ProjectConfig'
]


# 应用程序状态
class AppState:
    """应用程序状态管理"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.is_running = False
            self.is_debug = False
            self.current_view = None
            self.settings = {}
            self._initialized = True

    def start(self):
        """启动应用程序"""
        self.is_running = True
        print("应用程序已启动")

    def stop(self):
        """停止应用程序"""
        self.is_running = False
        print("应用程序已停止")

    def set_debug_mode(self, debug=True):
        """设置调试模式"""
        self.is_debug = debug
        print(f"调试模式: {'开启' if debug else '关闭'}")

    def set_current_view(self, view_name):
        """设置当前视图"""
        self.current_view = view_name
        print(f"切换到视图: {view_name}")


# 全局应用程序实例
app_state = AppState()


# 工具函数
def get_version():
    """获取版本信息"""
    return __version__


def get_project_info():
    """获取项目信息"""
    return {
        'name': __description__,
        'version': __version__,
        'author': __author__,
        'email': __email__,
        'license': __license__
    }


def check_dependencies():
    """检查项目依赖"""
    required_packages = {
        'PySide6': '6.5.0',
        'numpy': '1.21.0',
        'opencv-python': '4.5.0',
        'pyqtgraph': '0.12.0'
    }

    missing_packages = []
    for package, min_version in required_packages.items():
        try:
            mod = __import__(package)
            if hasattr(mod, '__version__'):
                actual_version = mod.__version__
                if actual_version < min_version:
                    print(f"警告: {package} 版本 {actual_version} 低于要求 {min_version}")
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"缺少依赖包: {', '.join(missing_packages)}")
        return False
    return True


def initialize_application():
    """初始化应用程序"""
    print("=" * 60)
    print(f"{__description__} v{__version__}")
    print(f"作者: {__author__}")
    print("=" * 60)

    # 创建目录结构
    ProjectConfig.setup_directories()
    print("目录结构初始化完成")

    # 检查依赖
    if not check_dependencies():
        print("警告: 依赖检查未通过，应用程序可能无法正常运行")

    # 设置应用程序状态
    app_state.start()

    print("应用程序初始化完成")
    return True


def cleanup_application():
    """清理应用程序资源"""
    app_state.stop()
    print("应用程序资源清理完成")


# 异常类
class AppError(Exception):
    """应用程序基础异常类"""
    pass


class ConfigError(AppError):
    """配置错误"""
    pass


class CameraError(AppError):
    """相机错误"""
    pass


class DataError(AppError):
    """数据错误"""
    pass


# 上下文管理器用于应用程序生命周期管理
class ApplicationContext:
    """应用程序上下文管理器"""

    def __enter__(self):
        initialize_application()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        cleanup_application()
        if exc_type:
            print(f"应用程序异常退出: {exc_val}")
        return False  # 不捕获异常，继续传播


# 当包被导入时执行初始化
if __name__ != "__main__":
    # 自动初始化目录结构
    ProjectConfig.setup_directories()

# 测试代码
if __name__ == "__main__":
    # 直接运行此文件时的测试代码
    print("铅浮选监测系统 - 包测试")
    print(f"版本: {get_version()}")
    print(f"项目信息: {get_project_info()}")

    # 测试路径获取
    config = ProjectConfig()
    print(f"项目根目录: {config.ROOT_DIR}")
    print(f"数据目录: {config.DATA_DIR}")

    # 测试应用程序状态
    app_state.set_debug_mode(True)
    app_state.set_current_view("主界面")

    print("包测试完成")