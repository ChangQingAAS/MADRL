import configparser
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = str(BASE_DIR).replace("\\", "/")
config_ini_path = BASE_DIR + "/config.ini"

cf = configparser.ConfigParser()
cf.read(config_ini_path)  # 读取配置文件，如果写文件的绝对路径，就可以不用os模块

ips = eval(cf.get("Server-Info", "ips"))  # 获取[Server-Info]中ip对应的值
password = cf.get("Server-Info", "pwd")

print(ips)
print(password)
