# 时间 ： 2020/7/20 17:13
# 作者 ： Dixit
# 文件 ： bt_etc_antiship.py
# 项目 ： moziAIBT
# 版权 ： 北京华戍防务技术有限公司

import os

APP_ABSPATH = os.path.dirname(__file__)

#######################
# SERVER_IP = "127.0.0.1"
SERVER_IP = "172.17.0.2"  # docker0
SERVER_PORT = "6060"
PLATFORM = 'linux'
SCENARIO_NAME = "hxfb"
# SCENARIO_NAME = "fanqian12"
SIMULATE_COMPRESSION = 8
DURATION_INTERVAL = 8
SYNCHRONOUS = True
#######################
MAX_EPISODES = 5000
MAX_BUFFER = 1000000
MAX_STEPS = 30
#######################

#######################
TMP_PATH = "%s/%s/tmp" % (APP_ABSPATH, SCENARIO_NAME)
OUTPUT_PATH = "%s/%s/output" % (APP_ABSPATH, SCENARIO_NAME)

CMD_LUA = "%s/cmd_lua" % TMP_PATH
PATH_CSV = "%s/path_csv" % OUTPUT_PATH
MODELS_PATH = "%s/Models/" % OUTPUT_PATH
EPOCH_FILE = "%s/epochs.txt" % OUTPUT_PATH
#######################

TRANS_DATA = True