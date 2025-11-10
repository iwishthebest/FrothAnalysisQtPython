# 主类简化后核心代码
from video_handler import VideoHandler
from log_manager import LogManager
from data_provider import DataProvider
from gui_components import TankWidget, RealtimeChart

class FoamMonitoringSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始化子模块（依赖注入，便于测试和替换）
        self.video_handler = VideoHandler(camera_count=4)  # 相机数量可配置
        self.log_manager = LogManager()
        self.data_provider = DataProvider()  # 可替换为真实数据实现
        
        # 初始化GUI（仅串联布局，组件创建委托给gui_components）
        self.setup_main_layout()
        self.setup_timers()  # 仅管理定时器，数据更新委托给data_provider
    
    def setup_main_layout(self):
        # 左侧堆叠窗口（视频预览/控制参数）
        self.left_stack = QStackedWidget()
        self.left_stack.addWidget(self._create_video_preview_page())  # 调用gui_components创建
        self.left_stack.addWidget(self._create_control_page())       # 调用gui_components创建
        
        # 右侧控制面板（标签页）
        self.right_tab = self._create_right_tabs()
        
        # 主布局串联
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.addWidget(self.left_stack, 70)
        main_layout.addWidget(self.right_tab, 30)
        self.setCentralWidget(central_widget)