# HNU Shuttle - 湖南大学场馆自动预约助手

**HNU Shuttle** 是一个基于 Python 和 Selenium 开发的自动化脚本，专为湖南大学师生设计，用于自动预约南校区羽毛球馆场地。它集成了自动登录、验证码识别（对接打码平台）、多线程并发抢票、状态检测以及邮件通知功能。

## 🚀 主要功能

* **多线程预约**：支持多账号、多场地并发抢票，提高成功率。
* **验证码自动识别**：
* 模拟前端 AES 加密流程，生成合法的验证码校验数据。
* 对接 **超级鹰 (Chaojiying)** API，自动识别点选验证码坐标。


* **精准定时**：基于服务器时间校准的毫秒级倒计时，支持自定义提前量（如 21:59:20 启动验证码识别）。
* **智能防检测**：通过 Selenium 配置（移除 `navigator.webdriver` 等）规避反爬虫检测。
* **状态检查与签到**：自动检查预约状态，并在规定时间内自动完成网页签到。
* **邮件通知**：预约结果和签到状态会通过邮件实时推送。
* **跨平台配置**：代码中内置了针对 Windows 和 Linux 环境的自动路径配置。

## 📂 项目结构

```text
HNU_Shuttle/
├── main.py                 # 程序主入口 (支持 book 和 check 模式)
├── config.py               # 全局配置文件 (路径、URL、时间表)
├── utils.py                # 核心工具集 (登录、时间同步、邮件发送、多线程启动)
├── checker.py              # 状态检查与签到逻辑 (HNUChecker 类)
├── captcha_simulator.py    # 验证码模拟器 (处理 AES 加密与坐标缩放)
├── captcha_solver.py       # 验证码解算器 (对接超级鹰 API)
├── logging_config.py       # 日志配置
├── data/
│   ├── data.json           # 缓存的场馆数据
│   └── dict_list.json      # 生成的预约任务列表
├── logs/                   # 运行日志目录
└── requirements.txt        # (需自行生成) 依赖列表

```

## 🛠️ 环境准备

1. **Python 环境**：推荐 Python 3.8+。
2. **安装依赖库**：
```bash
pip install selenium requests openpyxl pillow pycryptodome

```


3. **浏览器驱动**：
* 下载与您 Chrome 浏览器版本匹配的 `chromedriver`。
* 在 `config.py` 中配置 `CHROME_DRIVER_PATH`。



## ⚙️ 配置指南

在使用前，请务必修改以下配置信息：

### 1. 用户信息 (`students.xlsx`)

脚本通过读取 Excel 文件获取预约账号。请确保文件路径在 `config.py` 的 `DATA_FILES` 中配置正确。Excel 表头通常包含：

* `username`: 门户账号
* `password`: 门户密码
* `status`: 预约开关 (推荐设置为 `1` 或 `11` 开启)
* `first_floor`: 是否一楼 (`TRUE`/`FALSE`)
* `tomorrow`: 是否预约明天 (`TRUE`/`FALSE`)
* `id_time`: 时间段 ID (对应 `config.py` 中的 `TIMES` 字典，如 12 代表 12:00-13:00)
* `two_hour`: 是否连订两小时
* `exclude_id`: 指定场地号 (如 "3号场")

### 2. 打码平台配置 (`captcha_solver.py`)

本项目使用 **超级鹰** 进行验证码识别。请在 `captcha_solver.py` 的 `__init__` 方法中填入您的账号信息：

```python
self.cj_username = 'your_username'
self.cj_password = 'your_password'
self.cj_soft_id = '96001'  # 软件ID

```

### 3. 邮件通知配置 (`utils.py`)

在 `utils.py` 的 `send_simple_email` 函数中配置发件人信息：

```python
sender = "your_email@163.com"
password = "your_auth_code"  # 邮箱授权码
receivers = ["receiver@example.com"]

```

## 🖥️ 使用说明

### 1. 执行预约 (`book`)

该模式会读取 Excel 配置，生成任务并在指定时间（通常是晚上 22:00 前）开始倒计时抢票。

```bash
python main.py book

```

### 2. 执行状态检查与签到 (`check`)

该模式用于检查已预约的场地状态，或在规定时间内（如开始前 1 小时）执行自动签到。

```bash
python main.py check

```

* **可选参数**：
* `-id`: 指定检查特定的学生 ID。
* `-s`: 筛选特定状态的账号进行检查。



## ⚠️ 免责声明

* 本项目仅供学习交流使用，请勿用于商业用途或恶意攻击学校服务器。
* 使用自动化工具可能违反学校相关规定，请使用者自行承担风险。
* 代码中涉及的加密逻辑和 API 可能会随学校系统更新而失效。

---

*Last Updated: 2026-01-07*
