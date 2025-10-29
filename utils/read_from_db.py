
import sqlite3
import pandas as pd

conn = sqlite3.connect("data_records.db")
# 查询最近10条数据
df = pd.read_sql("SELECT * FROM sensor_data ORDER BY id DESC LIMIT 100", conn)
print(df)
conn.close()