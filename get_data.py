import re
import csv
import requests
import time
import sqlite3
from datetime import datetime
from pathlib import Path

# 基础配置
base_url = "http://10.12.18.2:8081/open/realdata/snapshot/batchGet"
db_file = Path("./data/data.db")
db_name = str(db_file)
# 表名避免使用特殊字符
table_name = "sensor_data"
tagList_file = Path("./src/tagList.csv")

interval = 60  # 采集间隔（秒）


def init_database():
    """初始化数据库和数据表，优化字段类型和约束"""
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # 优化字段类型和约束
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            "id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "fetch_time" DATETIME NOT NULL, 
            "tag_name" TEXT NOT NULL,
            "numeric_value" REAL,
            "string_value" TEXT, 
            "timestamp" DATETIME,
            -- 唯一约束：同一时间同一标签的数据不重复
            UNIQUE("fetch_time", "tag_name")
        )
        ''')

        # 优化索引：适配常用查询场景
        cursor.execute(f'''
        CREATE INDEX IF NOT EXISTS "idx_tag_fetch_time" 
        ON "{table_name}" ("tag_name", "fetch_time")
        ''')
        cursor.execute(f'''
        CREATE INDEX IF NOT EXISTS "idx_tag_timestamp" 
        ON "{table_name}" ("tag_name", "timestamp")
        ''')

        conn.commit()
        conn.close()
        print("数据库初始化完成（优化后）")
    except Exception as e:
        print(f"数据库初始化失败: {e}")


def get_tag_list():
    """从CSV文件获取标签列表，增加特殊字符日志"""
    tag_list = []
    try:
        with open(tagList_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row_num, row in enumerate(reader, 1):
                if row:  # 跳过空行
                    cleaned_line = re.sub(r'[\[\]]', '', row[0])
                    withprefix = add_prefix(cleaned_line.strip())
                    # 记录包含特殊字符的标签，便于排查
                    if '#' in withprefix or '"' in withprefix or "'" in withprefix:
                        print(
                            f"注意: 标签包含特殊字符 - 行号: {row_num}, 标签: {withprefix}")
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
    """获取数据并按优化后的结构存储"""
    tag_list = get_tag_list()
    if not tag_list:
        print("没有可用标签，跳过本次采集")
        return False

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # fetch_time
    processed_tags = [tag.replace('#', '%23') for tag in tag_list]
    tag_param = ",".join(processed_tags)

    try:
        params = {"tagNameList": tag_param}
        response = requests.get(url=base_url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            records = []
            for item in data.get("data", []):
                tag_name = item['TagName'].strip()
                value = item['Value']
                raw_timestamp = format_time(item['Time'])

                # 区分数值型和字符串型数据
                numeric_val = None
                string_val = None
                try:
                    # 尝试转换为数值（支持整数、浮点数）
                    numeric_val = float(value) if '.' in str(
                        value) else int(value)
                except (ValueError, TypeError):
                    # 转换失败则视为字符串
                    string_val = str(value) if value is not None else None

                # 时间字段格式化（确保符合DATETIME格式）
                timestamp = raw_timestamp if raw_timestamp else None

                records.append((
                    current_time,
                    tag_name,
                    numeric_val,
                    string_val,
                    timestamp
                ))

            if records:
                conn = sqlite3.connect(db_name)
                cursor = conn.cursor()
                # 插入优化后的字段
                insert_sql = f'''
                INSERT OR IGNORE INTO "{table_name}" 
                ("fetch_time", "tag_name", "numeric_value", "string_value", "timestamp")
                VALUES (?, ?, ?, ?, ?)
                '''
                # INSERT OR IGNORE：遇到唯一约束冲突时跳过（避免重复插入）
                cursor.executemany(insert_sql, records)
                conn.commit()
                conn.close()
                print(f"{current_time} - 成功保存 {len(records)} 条数据（优化后）")
                return True
            else:
                print(f"{current_time} - 未获取到有效数据")
                return False

        else:
            print(f"{current_time} - 请求失败，状态码：{response.status_code}")
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
