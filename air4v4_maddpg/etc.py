# File name : etc_uav_anti_tank.py

import torch
import os

app_abspath = os.path.dirname(__file__)
#USE_CUDA = torch.cuda.is_available()
USE_CUDA = False
device = torch.device("cuda" if USE_CUDA else "cpu")

#######################
SERVER_IP = "127.0.0.1"
SERVER_PORT = "6060"
SERVER_PLAT = "windows"  # windows linux
SCENARIO_NAME = "air4v4.scen"

SIMULATE_COMPRESSION = 4  #推演档位
DURATION_INTERVAL = 50

target_radius = 10000.0
target_name = "坦克排(T-72 MBT x 4)"

task_end_point = {}
task_end_point["latitude"] = 33.3610780570352
task_end_point["longitude"] = 44.3777800928825
#######################

#######################
MAX_EPISODES = 5000
MAX_BUFFER = 10000
MAX_STEPS = 30
#######################

#######################
TMP_PATH = "%s/%s/tmp" % (app_abspath, SCENARIO_NAME)
OUTPUT_PATH = "%s/%s/output" % (app_abspath, SCENARIO_NAME)

MODELS_PATH = "%s/Models/" % OUTPUT_PATH
#######################
