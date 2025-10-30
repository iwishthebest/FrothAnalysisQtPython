import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
from datetime import datetime
import time
import collections
from process_data import get_process_data

# 创建窗口和绘图对象
app = pg.mkQApp()  # 创建Qt应用
win = pg.GraphicsLayoutWidget(show=True)
plot = win.ci.addPlot()
curve = plot.plot(pen='y')

# 设置数据容器
data = collections.deque([0]*1000, maxlen=1000)
timestamps = collections.deque(range(1000), maxlen=1000)

def update():
    records = get_process_data()
    new_value = float(records[0][2])  # 获取新数据
    current_time = datetime.now()
    time_str = datetime.now().strftime('%H:%M:%S.%f')
    unix_timestamp = time.mktime(current_time.timetuple()) + current_time.microsecond / 1e6

    current_time = ...  # 获取当前时间戳

    data.append(new_value)
    timestamps.append(unix_timestamp)

    # 高效更新曲线数据
    curve.setData(list(timestamps), list(data))

# 创建定时器，每50毫秒触发一次update函数
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(50)  # 更新间隔50毫秒

# 启动Qt应用的事件循环
pg.exec()