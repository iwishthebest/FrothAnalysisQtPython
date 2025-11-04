import subprocess
import threading

def run_script(script_path, args):
    """执行给定路径下的Python脚本，并传递命令行参数"""
    cmd = ['python', script_path] + args
    subprocess.run(cmd)

# 定义要传递给各脚本的命令行参数
opc_data_args = [
    '--base-url', "http://10.12.18.2:8081/open/realdata/snapshot/batchGet",
    '--db-file', "../data/opc_data.db",
    '--table-name', "sensor_data",
    '--tag-list-file', "./src/tagList.csv",
    '--interval', "60"
]

images_filter_args = [
    '--rtsp-url', "rtsp://admin:fkqxk010@192.168.1.101:554/Streaming/Channels/101?tcp",
    '--save-interval', "5",
    '--base-save-dir', "../data/extracted_frames",
    '--max-grad-thresh', "1200",
    '--max-mean-brightness-thresh', "165",
    '--max-consecutive-bad-frames', "5",
    '--save-corrupted-for-analysis',
    '--corrupted-frames-dir', "../data/corrupted_frames",
    '--crop-enabled',
    '--crop-coords', "1200,300,1600,1200"
]

# 为每个脚本创建一个线程，并传递相应的命令行参数
thread1 = threading.Thread(target=run_script, args=('get_opc_data.py', opc_data_args))
thread2 = threading.Thread(target=run_script, args=('get_images_filter.py', images_filter_args))

# 启动线程
thread1.start()
thread2.start()

# 等待所有线程完成
thread1.join()
thread2.join()

print("两个脚本已全部完成运行。")