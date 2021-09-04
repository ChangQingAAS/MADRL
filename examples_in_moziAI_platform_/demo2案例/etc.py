import torch
import os


USE_CUDA = torch.cuda.is_available()
device = torch.device("cuda" if USE_CUDA else "cpu")

SERVER_IP = "127.0.0.1"  # 仿真服务器IP地址
SERVER_PORT = "6060"  # 仿真服务器端口号
SERVER_PLAT = "windows"  # windows linux
SCENARIO_NAME = "demo.scen"  # 想定名称
SIMULATE_COMPRESSION = 4  # 推演档位:即推演速度
# todo: 测试这个参数是什么
SYNCHRONOUS = False  # True同步, False异步

# 这个参数是不是能做成false，但是还是要连墨子AI啊
SHOW_FIGURE = False

# 这个参数从20000改到1000
target_radius = 1000.0
target_name = "障碍物"

#  终点
task_end_point = {}
task_end_point["latitude"] = 44.44
task_end_point["longitude"] = 33.33

# todo: 这几个mode也要试一下
# app_mode:
# 1--local windows train mode
# 2--local linux train mode
# 3--remote windows evaluate mode
# 4--local windows evaluate mode
app_mode = 1

# 训练回合 step buffer_size 定义
MAX_EPISODES = 5000  # 一共训练多少回合
MAX_BUFFER = 10000
MAX_STEPS = 30  # 每回合一共做多少次决策
DURATION_INTERVAL = 120  # 仿真时间多长做一次决策。（单位：秒）# 这个应该和想定文件里给的推演速度有关

# 路径定义
app_abspath = os.path.dirname(__file__)
TMP_PATH = "%s/%s/tmp" % (app_abspath, SCENARIO_NAME)
OUTPUT_PATH = "%s/output" % app_abspath   
MODELS_PATH = "%s/Models/" % app_abspath    # 模型输出路径
