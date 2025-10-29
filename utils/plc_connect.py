import snap7
from snap7 import util

# 创建客户端并连接
plc = snap7.client.Client()
plc.set_connection_type(3)  # 对于200SMART，必须设置连接类型为3[2,3](@ref)

try:
    plc.connect('192.168.0.21', 0, 1)  # 参数：IP地址, 机架号, 槽号
    print("PLC连接成功")
except Exception as e:
    print(f"连接失败: {e}")


# 假设已成功连接PLC

# 1. 读取布尔值（例如 V0.0）
bool_data = plc.db_read(1, 0, 1)  # 读取DB1，起始地址0，长度为1字节
value_bool = util.get_bool(bool_data, 0, 0)  # 从第0字节的第0位解析出布尔值
print(f"V0.0的状态: {value_bool}")

bool_data = plc.db_read(1, 0, 1)  # 读取DB1，起始地址0，长度为1字节
value_bool = util.get_bool(bool_data, 0, 1)  # 从第0字节的第0位解析出布尔值
print(f"V0.1的状态: {value_bool}")

bool_data = plc.db_read(1, 0, 1)  # 读取DB1，起始地址0，长度为1字节
value_bool = util.get_bool(bool_data, 0, 2)  # 从第0字节的第0位解析出布尔值
print(f"V0.2的状态: {value_bool}")

# 2. 写入布尔值（例如将 V0.1 设置为True）
# bool_data = plc.db_read(1, 0, 1)
# util.set_bool(bool_data, 0, 1, True)  # 设置第0字节的第1位为True
# plc.db_write(1, 0, bool_data)

# 读取过程输入映像区（Area ID=0x81）从偏移量34开始的一个字（2字节）
data = plc.read_area(snap7.type.Areas.PE, 0, 34, 2)

# 将读取到的字节数据转换为整数
# 注意：PLC中字（Word）的字节序可能是大端序，需要转换
value = int.from_bytes(data, byteorder='big') # 可能需要根据实际情况调整字节序
# 或者使用snap7的util库进行转换
# value = util.get_int(data, 0)

print(f"AIW34的原始值为: {value}")