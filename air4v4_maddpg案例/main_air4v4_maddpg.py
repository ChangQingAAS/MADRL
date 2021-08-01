# File name : main_uav_anti_tank.py
import os
import time

from env import Air4v4Env as Environment
import etc
from agent import Agent

import psutil

from mozi_utils.pyfile import read_start_epoch
from mozi_utils.pyfile import read_start_epoch_file
from mozi_utils.pyfile import write_start_epoch_file


def main():
    # 判断墨子是否已经启动
    process_name = 'MoziServer.exe'
    process_state = False
    for i in psutil.process_iter():
        if i.name() == process_name:
            str_tmp = str(i.name()) + "-" + str(i.pid) + "-" + str(i.status())
            print("墨子已启动:" + str_tmp)
            process_state = True
            break

    # 如果墨子还没有启动，则启动之
    if process_state == False:
        mozi_path = os.environ['MOZIPATH']
        mozi_p = mozi_path + '\\' + process_name
        os.popen(mozi_p)
        time.sleep(30)

    #创建环境对象 ，并启动之
    env = Environment(etc.SERVER_IP, etc.SERVER_PORT, etc.SCENARIO_NAME,
                      etc.SIMULATE_COMPRESSION, etc.DURATION_INTERVAL,
                      etc.SERVER_PLAT)
    env.start()
    epoch_file_path = "%s/epoch.txt" % etc.OUTPUT_PATH
    start_epoch = read_start_epoch(epoch_file_path)

    #创建智能体对象
    agent = Agent(env)

    try:
        for _ep in range(start_epoch, etc.MAX_EPISODES):
            #设置智能体
            agent.setup(env.state_space, env.action_space)
            #重置环境
            timesteps = env.reset()
            #重置智能体
            agent.reset()
            for step in range(etc.MAX_STEPS):
                #运行一步，获取单步数据
                timesteps = agent.step(timesteps[0])
                print(" ")
                print("轮数:%s 决策步数:%s" % (_ep, step))
                print("reward:%.2f" % (timesteps[1]))
                # 如果done则退出循环
                if timesteps[2]:
                    break
            write_start_epoch_file(epoch_file_path, str(_ep))

    except KeyboardInterrupt:
        pass


main()
