import snap7
from snap7.util import get_bool, get_int, get_real, get_dword, get_dint
from snap7.type import Areas

# 创建客户端并连接
plc = snap7.client.Client()
plc.set_connection_type(3)  # 对于200SMART，必须设置连接类型为3[2,3](@ref)

try:
    plc.connect('192.168.0.21', 0, 1)  # 参数：IP地址, 机架号, 槽号
    print("PLC连接成功")
except Exception as e:
    print(f"连接失败: {e}")


def read_i_bit(plc, byte_offset, bit_offset):
    """
    读取I区一个特定位的通用函数

    :param plc: 已建立连接的PLC客户端对象
    :param byte_offset: 字节偏移量 (例如，I0.0的字节偏移是0，I1.5的字节偏移是1)
    :param bit_offset: 位偏移量 (0-7，例如I0.0的位偏移是0，I1.5的位偏移是5)
    :return: 该位的布尔状态 (True/False)
    """
    # 使用 Areas.Pe 表示I输入区，比硬编码0x81更规范
    data = plc.read_area(Areas.PE, 0, byte_offset, 1)
    bool_value = get_bool(data, 0, bit_offset)
    return bool_value


def read_q_bit(plc, byte_offset, bit_offset):
    """
    读取Q区一个特定位的通用函数

    :param plc: 已连接的PLC客户端对象
    :param byte_offset: 字节偏移量（例如，Q0.0的字节偏移是0）
    :param bit_offset: 位偏移量（0-7，例如Q0.0的位偏移是0）
    :return: 该位的布尔状态
    """
    # 使用 Areas.PA 表示Q输出区，比硬编码0x82更规范
    data = plc.read_area(Areas.PA, 0, byte_offset, 1)
    bool_value = get_bool(data, 0, bit_offset)
    return bool_value


def read_vd(plc, vd_offset, data_type='real'):
    """
    通用V存储区双字读取函数

    :param plc: 已连接的PLC客户端对象
    :param vd_offset: VD地址的偏移量
    :param data_type: 数据类型 ('real', 'dword', 'dint')
    :return: 对应数据类型的值
    """
    try:
        data = plc.read_area(Areas.DB, 1, vd_offset, 4)

        if data_type == 'real':
            return get_real(data, 0)
        elif data_type == 'dword':
            return get_dword(data, 0)
        elif data_type == 'dint':
            return get_dint(data, 0)
        else:
            print(f"不支持的数据类型: {data_type}")
            return 0
    except Exception as e:
        print(f"读取VD{vd_offset}失败: {e}")
        return 0


try:
    # 批量读取VD
    for vd in [56, 60, 68, 88, 240, 192, 196]:
        vdint = read_vd(plc, vd, data_type='dword')
        print(f"VD{vd}的值是{vdint}")

    # 读取VD344为长整数
    vd344_dint = read_vd(plc, 344, 'dint')
    print(f"VD344长整数: {vd344_dint}")

    for i in range(8):
        # 使用示例：读取I0.0
        i0_i_status = read_i_bit(plc, 0, i)
        print(f"I0.{i}的状态是：{i0_i_status}")

    for i in range(8):
        # 使用示例：读取Q0.0
        q0_i_status = read_q_bit(plc, 0, i)
        print(f"Q0.{i}的状态是：{q0_i_status}")
except Exception as e:
    print(f"连接或读取失败: {e}")
finally:
    plc.disconnect()
