import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import sqlite3  # 按实际数据库类型替换（如pymysql、psycopg2）

# 解决中文显示问题
plt.rcParams["font.family"] = ["SimHei"]  # 设置支持中文的字体
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# ----------------------
# 1. 从数据库读取数据
# ----------------------
# 连接数据库（替换为你的数据库信息）
conn = sqlite3.connect('data.db')  # SQLite示例
# 若为MySQL：
# import pymysql
# conn = pymysql.connect(host='localhost', user='用户名', password='密码', db='数据库名')

# 查询数据：获取KYFX.kyfx_gqxk_grade_Pb的时间戳和数值
tag_name = 'KYFX.kyfx_gqxk_grade_Pb'

# 定义要筛选的时间范围（根据实际时间格式调整）
start_time = '2025-10-28 16:00:00'
end_time = '2025-10-28 18:00:00'

query = f"""
    SELECT timestamp, numeric_value 
    FROM sensor_data 
    WHERE tag_name = ? AND timestamp BETWEEN ? AND ?
    ORDER BY timestamp  -- 按时间排序
"""
# 执行查询并转换为DataFrame
df = pd.read_sql(
    query,
    conn,
    params=(tag_name, start_time, end_time)  # 依次传入标签名、开始时间、结束时间
)

# 关闭数据库连接
conn.close()

# ----------------------
# 2. 处理时间戳（关键步骤）
# ----------------------
# 转换时间戳列（根据实际格式处理）
# 若为字符串格式（如'2023-10-01 08:00:00'）：
df['timestamp'] = pd.to_datetime(df['timestamp'])
# 若为Unix时间戳（单位秒）：
# df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
df_filtered = df[
    (df['numeric_value'] > 0)
]
# ----------------------
# 3. 绘图
# ----------------------
plt.figure(figsize=(12, 6))

# 绘制折线图（时间戳x轴，数值y轴）
plt.plot(
    df_filtered['timestamp'],
    df_filtered['numeric_value'],
    marker='o',  # 数据点标记
    linestyle='-',  # 线样式
    color='teal',
    alpha=0.8,  # 透明度
    label='KYFX.kyfx_gqxk_grade_Pb'
)

# 格式化x轴时间显示
plt.gca().xaxis.set_major_formatter(DateFormatter('%H:%M'))  # 时间格式
plt.gcf().autofmt_xdate()  # 自动旋转x轴标签，避免重叠

# 添加标签和标题
plt.xlabel('时间', fontsize=12)
plt.ylabel('数值', fontsize=12)
plt.title('KYFX.kyfx_gqxk_grade_Pb 随时间变化趋势', fontsize=14)
plt.legend()  # 显示图例
plt.grid(linestyle='--', alpha=0.5)  # 网格线

# 调整布局并显示
plt.tight_layout()
plt.show()