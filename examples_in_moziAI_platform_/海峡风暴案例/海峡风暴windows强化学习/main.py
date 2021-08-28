# !/usr/bin/python
# -*- coding: utf-8 -*-
######################################
# File name : main_uav_anti_tank.py
# Create date : 2019-10-20 19:37
# Modified date : 2020-04-28 19:35
# Author : liuzy
# Describe : not set
# Email : lzygzh@126.com
######################################
import os
import time

from env import IraqEnv as Environment
import etc
from agent import Agent

import psutil

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

    # 启动墨子
    if process_state == False:
        mozi_path = os.environ['MOZIPATH']
        mozi_p = mozi_path + '\\' + process_name
        os.popen(mozi_p)
        time.sleep(30)

    #创建环境对象
    env = Environment(etc.SERVER_IP, etc.SERVER_PORT, etc.SCENARIO_NAME, etc.SIMULATE_COMPRESSION, etc.DURATION_INTERVAL, etc.SERVER_PLAT)
    #启动环境
    env.start()
    #创建智能体对象
    agent = Agent(env)

    try:
        for _ep in range(0, etc.MAX_EPISODES):
            #设置智能体
            agent.setup(env.state_space, env.action_space)
            #重置环境
            timesteps = env.reset()
            #重置智能体
            agent.reset()
            for step in range(etc.MAX_STEPS):
                #运行一步
                print(timesteps)
                timesteps = agent.step(timesteps[0])
                if timesteps[2]:
                    break

    except KeyboardInterrupt:
        pass

main()
