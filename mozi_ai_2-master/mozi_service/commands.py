# 时间 ： 2021/1/22 9:44
# 作者 ： Shizhun Xiao
# 文件 ： commands.py
# 项目 ： moziAI_nlz
# 版权 ： 北京华戍防务技术有限公司

import subprocess
from json import load
import urllib.request as Ur
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
# TensorBoard_File_Path="/home/event/tune_experiment/tune_experiment" #tenordboard 创建的文件路径

import os
test_report = '/root/ray_results/hyper_hxfb_train'
def get_new_dir(test_report):
    lists = os.listdir(test_report)                                    #列出目录的下所有文件和文件夹保存到lists
    lists.sort(key=lambda fn:os.path.getmtime(test_report + "/" + fn))#按时间排序
    for i in range(len(lists)-1):
        if os.path.isdir(os.path.join(test_report,lists[-1-i])):
            file_new = os.path.join(test_report,lists[-1-i])                     #获取最新的文件保存到file_new
            print(file_new)
            break
    return file_new

def Create_Tensorboad(test_report=test_report):
    TensorBoard_File_Path = get_new_dir(test_report)
    Public_Ip = load(Ur.urlopen('https://api.ipify.org/?format=json'))['ip'] #获取公网IP
    Com_Port="6006" #指定端口
    Command_Tensorboard="tensorboard --logdir=%s  --bind_all --port %s"%(TensorBoard_File_Path,Com_Port) #创建开启tensorboard 服务命令
    Achieve_tensorboard_pid="netstat -anp|grep %s|awk '{printf $7}'|cut -d/ -f1"%Com_Port#获取6006 对应端口的进程PID 命令

    PID=subprocess.getoutput(Achieve_tensorboard_pid) #获取6006 对应端口的进程PID

    kill_pid=subprocess.getoutput("kill -s 9 %s"%(PID))#杀死该进程
    subprocess.getoutput("killall tensorboard")#杀死tensorboard 所有进程
    Process=subprocess.Popen(Command_Tensorboard,shell=True,stdout=subprocess.PIPE,universal_newlines=True)#开启tensorboard 服务

    Return_Port=Public_Ip+":"+Com_Port
    return Return_Port

# print(Create_Tensorboad(TensorBoard_File_Path))
if __name__ == '__main__':
    hyperlink = Create_Tensorboad(test_report)
    print(hyperlink)
