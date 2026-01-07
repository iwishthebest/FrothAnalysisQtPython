# 🌊 FrothAnalysisQtPython - 浮选泡沫图像分析与监控系统

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-green.svg)](https://wiki.qt.io/Qt_for_Python)
[![OpenCV](https://img.shields.io/badge/CV-OpenCV-red.svg)](https://opencv.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**FrothAnalysisQtPython** 是一款专为**铅锌浮选工艺**设计的工业级桌面应用程序。系统基于 PySide6
构建，深度集成了机器视觉算法与工业控制逻辑，能够实时监测**铅快粗、铅精一/二/三**等关键工序的泡沫状态，并结合 OPC 数据实现闭环控制。

---

## ✨ 核心功能 (Key Features)

### 1. 👁️ 智能机器视觉分析

* **多工序监测**: 支持同时连接 4 路工业相机，覆盖铅快粗 (Rougher) 及铅精选 (Cleaner 1-3) 各级工序。
* **特征提取 (Feature Extraction)**:
    * **动态特征**: 基于 **SURF** 算法计算泡沫流速、速度方差及流动稳定性。
    * **纹理特征**: 基于 **GLCM (灰度共生矩阵)** 计算能量、对比度、相关性等纹理指标。
    * **统计特征**: 实时分析红灰比 (Red/Gray Ratio)、灰度直方图 (偏度/峰度)。

### 2. 📊 实时工艺监控 (Monitoring)

* **KPI 仪表盘**: 实时显示 **原矿铅品位 (Feed)**、**高铅精矿品位 (Conc)** 及 **铅回收率 (Recovery)**。
* **趋势追踪**: 内置高性能绘图组件 (PyQtGraph)，以 10 分钟为周期动态展示品位变化趋势。
* **状态指示**: 采用美化的 StatCard 组件，直观展示各指标的实时数值与健康状态。

### 3. 🎛️ 过程智能控制 (Control)

* **双模式切换**: 支持 **自动 (Auto)** 与 **手动 (Manual)** 控制模式无缝切换。
* **液位控制**: 针对 4 个浮选槽独立配置 PID 参数 ($K_p, K_i, K_d$)，实现液位精准调节。
* **精准加药**:
    * 覆盖捕收剂、起泡剂、抑制剂等多种药剂类型。
    * 实时监控加药流量 (ml/min) 与设备运行状态。
* **效能评估**: 实时计算系统的**控制效果**、**稳定性指标**及**能耗效率**。

### 4. 📈 历史数据与报表 (History)

* **全参数记录**: 自动记录品位数据及详细的药剂消耗量（丁黄药、乙硫氮、石灰、2#油、DS1/DS2等）。
* **灵活查询**: 支持按日期范围筛选，提供数据可视化统计（平均品位、最高值、运行时长）。
* **一键导出**: 支持将查询结果导出为 CSV 格式，便于二次分析。

---

## 🛠️ 环境依赖 (Requirements)

本项目基于 **Python 3.10+** 开发。主要依赖库如下：

* **GUI**: `PySide6==6.10.0`, `pyqtgraph==0.13.7`
* **图像处理**: `opencv-python==4.12.0.88`, `numpy==2.2.6`, `matplotlib==3.10.7`
* **通讯与网络**: `requests==2.32.5`, `opcua==0.98.13`, `python-snap7==2.0.2`
* **数据处理**: `pandas==2.3.3`
* **其他**: `cryptography`

---

## 🚀 快速开始 (Quick Start)

### 1. 克隆仓库

```bash
git clone [https://github.com/YourUsername/FrothAnalysisQtPython.git](https://github.com/YourUsername/FrothAnalysisQtPython.git)
cd FrothAnalysisQtPython
```

### 2. 创建并激活虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置文件

在运行前，请确保 config/ 和 resources/tags/ 目录下的配置正确：

- OPC 标签表: 编辑 resources/tags/tagList.csv，添加需要采集的标签名称。

- 系统配置: 检查 config/config.json 或相关 Python 配置文件中的相机 IP 和服务器地址。

### 5. 启动系统

```bash
python main.py
```

## 📂 项目结构 (Project Structure)

```text
FrothAnalysisQtPython/
├── config/                 # 配置中心
│   ├── camera_configs.py   # 相机节点与RTSP配置
│   ├── system_settings.json# 全局系统参数
│   └── tank_configs.py     # 槽体参数配置
├── data/                   # 数据持久化 (SQLite数据库/自动备份)
├── logs/                   # 系统运行日志 (按日期归档)
├── resources/              # 静态资源
│   ├── styles/             # QSS 界面样式表
│   └── tags/               # OPC/PLC 点位映射表
├── src/                    # 源代码
│   ├── core/               # 核心架构 (Application, EventBus)
│   ├── services/           # 后端服务
│   │   ├── opc_service.py  # OPC/HTTP 数据采集与断线重连
│   │   ├── data_service.py # SQLite 数据存储服务
│   │   └── video_service.py# 视频流采集与分发
│   ├── utils/              # 算法工具
│   │   └── feature_extract.py # SURF, GLCM 特征提取算法
│   └── views/              # UI 视图层
│       ├── components/     # 复用组件 (StatCard, TankWidget)
│       ├── pages/          # 主要页面
│       │   ├── monitoring_page.py # 实时监控 (KPI, 趋势图)
│       │   ├── control_page.py    # 智能控制 (PID, 加药)
│       │   └── history_page.py    # 历史报表 (查询, 导出)
│       └── main_window.py  # 主窗口框架
└── main.py                 # 程序入口
```

## ⚙️ 核心算法说明

### 泡沫流速计算 (SURF)

系统利用 cv2.xfeatures2d_SURF 检测前后两帧图像的特征点，通过 Brute-Force Matcher
进行匹配，计算特征点位移向量： $$ v = \frac{\sqrt{(x_2-x_1)^2 + (y_2-y_1)^2}}{\Delta t} $$

### 纹理分析 (GLCM)

通过构建灰度共生矩阵，量化泡沫表面的物理特征：

- Homogeneity (同质性): 反映气泡大小分布的均匀程度。

- Contrast (对比度): 反映气泡边缘的清晰度与沟槽深度。

### 闭环控制策略

- 液位控制: 采用增量式 PID 算法，实时调节排矿阀开度。

- 药剂配比: 根据实时品位反馈（Feed/Conc Grade）动态调整丁黄药与乙硫氮的添加比例。