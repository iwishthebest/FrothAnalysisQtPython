import re
import csv
import requests
import time
import sqlite3
from datetime import datetime
from pathlib import Path

# 基础配置
base_url = "http://10.12.18.2:8081/open/realdata/snapshot/batchGet"
db_name = "data_records.db"
# 表名避免使用特殊字符
table_name = "sensor_data"  
interval = 60  # 采集间隔（秒）


def init_database():
    """初始化数据库和数据表，确保表名和字段名安全"""
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # 创建数据表，使用双引号包裹表名和字段名，防止特殊字符问题
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "fetch_time" TEXT NOT NULL,
            "tag_name" TEXT NOT NULL,
            "value" TEXT,
            "timestamp" TEXT,
            "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建索引时同样使用双引号
        cursor.execute(f'''
        CREATE INDEX IF NOT EXISTS "idx_tag_time" 
        ON "{table_name}" ("tag_name", "fetch_time")
        ''')
        
        conn.commit()
        conn.close()
        print("数据库初始化完成")
    except Exception as e:
        print(f"数据库初始化失败: {e}")


def get_tag_list():
    """从CSV文件获取标签列表，增加特殊字符日志"""
    tag_list = []
    try:
        with open('my_YJ.csv', 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row_num, row in enumerate(reader, 1):
                if row:  # 跳过空行
                    cleaned_line = re.sub(r'[\[\]]', '', row[0])
                    withprefix = add_prefix(cleaned_line.strip())
                    # 记录包含特殊字符的标签，便于排查
                    if '#' in withprefix or '"' in withprefix or "'" in withprefix:
                        print(f"注意: 标签包含特殊字符 - 行号: {row_num}, 标签: {withprefix}")
                    tag_list.append(withprefix)
        print(f"已加载 {len(tag_list)} 个标签")
    except Exception as e:
        print(f"读取标签列表失败: {e}")
    return tag_list


def add_prefix(tag_name):
    """为标签添加前缀"""
    if tag_name.startswith('yj_'):
        return f'YJ.{tag_name}'
    elif tag_name.startswith('kyfx_'):
        return f'KYFX.{tag_name}'
    return tag_name


def format_time(time_str):
    """格式化时间字符串"""
    if time_str and '.' in time_str:
        return time_str.split('.')[0]
    return time_str


def safe_escape(value):
    """安全转义特殊字符（作为额外保障）"""
    if value is None:
        return ""
    # 转换为字符串并进行基本转义
    str_val = str(value)
    # 仅作为额外保障，参数化查询已处理大部分情况
    return str_val.replace("'", "''").replace('"', '""')


def fetch_and_save_data():
    """获取数据并安全保存到数据库"""
    tag_list = get_tag_list()
    if not tag_list:
        print("没有可用标签，跳过本次采集")
        return False

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tag_param = ",".join(tag_list)

    try:
        # 发送请求获取数据
        params = {"tagNameList": tag_param}
        response = requests.get(url=base_url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            records = []
            
            # 处理获取到的数据
            for item in data.get("data", []):
                # 对可能包含特殊字符的字段进行处理
                tag_name = safe_escape(item['TagName'])
                value = safe_escape(item['Value'])
                timestamp = safe_escape(format_time(item['Time']))
                
                records.append((
                    current_time,
                    tag_name,
                    value,
                    timestamp
                ))

            # 使用参数化查询插入数据
            if records:
                conn = sqlite3.connect(db_name)
                cursor = conn.cursor()
                # 表名使用双引号包裹，字段名也使用双引号
                insert_sql = f'''
                INSERT INTO "{table_name}" ("fetch_time", "tag_name", "value", "timestamp")
                VALUES (?, ?, ?, ?)
                '''
                # 批量插入
                cursor.executemany(insert_sql, records)
                conn.commit()
                conn.close()
                print(f"{current_time} - 成功保存 {len(records)} 条数据到数据库")
                return True
            else:
                print(f"{current_time} - 未获取到有效数据")
                return False

        else:
            print(f"{current_time} - 请求失败，状态码：{response.status_code}")
            return False

    except sqlite3.OperationalError as e:
        print(f"{current_time} - SQL操作错误: {e}")
        # 打印导致错误的数据记录（前3条），便于排查
        if records:
            print(f"问题数据示例: {records[:3]}")
        return False
    except Exception as e:
        print(f"{current_time} - 采集异常：{e}")
        return False


def main():
    init_database()
    print("开始连续数据采集...")
    count = 0
    
    while True:
        fetch_and_save_data()
        count += 1
        print(f"已完成 {count} 次数据采集，等待下一次...")
        time.sleep(interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序已手动停止")
    except Exception as e:
        print(f"程序异常终止：{e}")
    