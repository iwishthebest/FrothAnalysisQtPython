from opcua import Client
import time

class OPCUA_Client:
    def __init__(self, server_url):
        self.server_url = server_url
        self.client = Client(server_url)
        self.connected = False

    def connect(self):
        """连接到OPC UA服务器"""
        try:
            self.client.connect()
            self.connected = True
            print(f"成功连接到OPC UA服务器: {self.server_url}")
            # 获取根节点和对象节点，便于后续浏览
            self.root = self.client.get_root_node()
            self.objects = self.client.get_objects_node()
            print("根节点是: ", self.root)
            print("对象节点是: ", self.objects)
        except Exception as e:
            print(f"连接失败: {e}")

    def browse_nodes(self, node=None, level=0):
        """递归浏览服务器上的节点结构（可选功能，用于探索）"""
        if node is None:
            node = self.objects
        try:
            children = node.get_children()
            print('  ' * level + f"{node.get_browse_name()} ({node.nodeid})")
            for child in children:
                self.browse_nodes(child, level+1)
        except Exception as e:
            # 可能有些节点无法访问，忽略即可
            pass

    def read_value(self, node_id):
        """读取指定节点的值"""
        if not self.connected:
            print("未连接到服务器")
            return None
        try:
            node = self.client.get_node(node_id)
            value = node.get_value()
            print(f"节点 {node_id} 的值为: {value}")
            return value
        except Exception as e:
            print(f"读取节点 {node_id} 时出错: {e}")
            return None

    def write_value(self, node_id, value):
        """向指定节点写入值"""
        if not self.connected:
            print("未连接到服务器")
            return False
        try:
            node = self.client.get_node(node_id)
            node.set_value(value)
            print(f"已成功将节点 {node_id} 的值设置为: {value}")
            return True
        except Exception as e:
            print(f"写入节点 {node_id} 时出错: {e}")
            return False

    def disconnect(self):
        """断开与服务器的连接"""
        if self.connected:
            self.client.disconnect()
            self.connected = False
            print("已断开与OPC UA服务器的连接。")

# 使用示例
if __name__ == "__main__":
    # 请将URL替换为你的实际OPC UA服务器地址
    # 例如，使用一个免费的公共测试服务器： "opc.tcp://opcua.demo-this.com:51210/UA/SampleServer"
    url = "opc.tcp://localhost:4840"
    opc_client = OPCUA_Client(url)
    
    # 连接到服务器
    opc_client.connect()
    
    if opc_client.connected:
        # 示例：读取服务器当前时间（一个标准的节点）
        current_time_node = "ns=0;i=2258"
        opc_client.read_value(current_time_node)
        
        # 你可以使用 browse_nodes 方法来探索服务器上可用的节点
        # opc_client.browse_nodes()
        
        # 示例：写入值（请确保你写入的节点是可写的，并且数据类型匹配）
        # 假设你知道一个可写的节点ID，例如 "ns=2;s=MyVariable"
        # opc_client.write_value("ns=2;s=MyVariable", 42.5)
        
        # 保持连接并定时读取（示例）
        # for i in range(5):
        #     time.sleep(2)
        #     opc_client.read_value(current_time_node)
        
        # 断开连接
        opc_client.disconnect()