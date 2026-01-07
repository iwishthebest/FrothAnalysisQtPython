Froth Analysis System (Qt + Python)
📖 项目简介 (Introduction)
FrothAnalysisQtPython 是一个基于 Python 和 Qt (PySide6) 开发的工业级浮选泡沫图像分析与监控系统。该系统集成了工业相机视频采集、实时图像处理（特征提取）、OPC UA/DA 通讯以及历史数据管理功能，主要用于浮选工况的实时监测与数字化分析。

✨ 核心功能 (Key Features)
📺 实时视频监控 (Real-time Monitoring)

支持多路工业相机同时连接与显示。

实时视频流展示与状态监测。

🔍 泡沫特征分析 (Froth Analysis)

基于计算机视觉（OpenCV）的泡沫特征提取算法。

核心指标计算（推测）：气泡大小分布、移动速度、颜色/灰度特征、泡沫稳定性等。

🏭 OPC 工业通讯 (OPC Communication)

内置 OPC 客户端服务，支持与 PLC/DCS 系统进行数据交互。

支持读写工业标签（Tags），实现闭环控制或状态同步。

📊 历史数据与趋势 (History & Trending)

集成 SQLite 数据库，自动记录分析数据与系统日志。

提供历史数据查询、趋势图表展示及导出功能。

⚙️ 灵活配置 (Flexible Configuration)

支持相机参数、槽体（Tank）配置、算法参数及 UI 样式的自定义。

JSON 格式的配置文件管理。

🛠️ 技术栈 (Tech Stack)
编程语言: Python 3.10+

图形界面: PySide6 (Qt for Python)

计算机视觉: OpenCV (opencv-python)

工业通讯: OPC UA / OpenOPC (具体依赖视 opc_service.py 而定)

数据存储: SQLite

数据处理: NumPy, Pandas

📂 项目结构 (Project Structure)
Plaintext

FrothAnalysisQtPython/
├── config/                 # 系统配置文件 (相机, 槽体, UI配置)
├── data/                   # 数据存储 (SQLite 数据库文件)
├── logs/                   # 系统运行日志
├── resources/              # 静态资源 (图标, QSS样式表, 标签列表)
├── src/                    # 源代码目录
│   ├── common/             # 通用常量与异常定义
│   ├── controllers/        # 控制器层 (连接 UI 与 Service)
│   ├── core/               # 核心逻辑 (Application, EventBus)
│   ├── services/           # 后端服务 (OPC, 视频流, 数据存储, 日志)
│   ├── utils/              # 工具类 (图像算法, 视频处理)
│   └── views/              # UI 视图层 (主窗口, 监控页, 设置页等)
├── main.py                 # 程序启动入口
├── requirements.txt        # 项目依赖列表
└── debug_opc.py            # OPC 通讯调试脚本
🚀 快速开始 (Getting Started)
1. 环境准备
确保已安装 Python 3.10 或更高版本。

2. 安装依赖
建议使用虚拟环境（Virtualenv/Conda）管理依赖。

Bash

# 创建虚拟环境
python -m venv venv
# 激活虚拟环境 (Windows)
venv\Scripts\activate
# 激活虚拟环境 (Linux/Mac)
source venv/bin/activate

# 安装项目依赖
pip install -r requirements.txt
3. 配置系统
在运行前，请检查 config/ 目录下的配置文件：

camera_configs.py: 配置相机 IP、RTSP 地址或 ID。

tank_configs.py: 配置浮选槽的相关参数。

system_settings.json: 一般系统设置。

4. 运行程序
Bash

python main.py
🔌 工业通讯配置 (OPC Configuration)
项目使用 CSV 文件管理 OPC 标签，文件位于 resources/tags/。

配置方式: 修改 tagList.csv 或对应的 CSV 文件以映射 PLC 地址。

调试: 运行 python debug_opc.py 可单独测试 OPC 连接状态。

📝 开发指南 (Development)
UI 修改: 主要文件在 src/views/，样式文件在 resources/styles/。

算法优化: 泡沫特征提取算法位于 src/utils/feature_extract.py。

服务逻辑: 若需修改数据采集频率或通讯逻辑，请查看 src/services/。
