#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from mozi_simu_sdk.mozi_server import MoziServer
from mozi_simu_sdk.scenario import CScenario


class BaseEnvironment:
    """
    环境
    """
    def __init__(self, IP, AIPort, platform, scenario_name, simulate_compression, duration_interval):
        self.server_ip = IP
        self.aiPort = AIPort
        self.platform = platform
        self.scenario_name = scenario_name
        self.mozi_server = None
        self.scenario = None

        self.simulate_compression = simulate_compression
        self.synchronous = True # True同步, False异步
        self.duration_interval = duration_interval
        self.steps = 0

        # 新建一个墨子仿真服务器，并进行相关设置
        self.mozi_server = MoziServer(
            IP,
            AIPort,
            platform,
            scenario_name,
            simulate_compression,
            True)
        self.mozi_server.set_run_mode(self.synchronous)
        self.mozi_server.set_decision_step_length(duration_interval)

    def reset(self, app_mode):
        """
        重置函数：加载想定
        """
        self.steps = 0
        self.mozi_server.load_scenario()
        self.scenario = CScenario(self.mozi_server)
        bInitSucess: bool = self.mozi_server.init_situation(self.scenario, app_mode)
        self.mozi_server.set_simulate_compression(self.simulate_compression)
        self.mozi_server.run_simulate()

    def step(self):
        self.steps += 1

    def create_scenario(self):
        """
        建立一个想定对象
        """
        self.scenario = CScenario(self.mozi_server)

    def connect_mozi_server(self):
        """
        连接墨子服务器
        """
        # 连接到墨子服务器
        self.mozi_server = MoziServer(
            self.server_ip,
            self.aiPort,
            self.platform,
            self.scenario_name,
            self.simulate_compression,
            self.synchronous)
        return True

    def start(self):
        """
        开始函数
        主要用途：
        1.连接服务器端
        2.设置决策时间
        3.设置智能体决策想定是否暂停
        """
        self.connect_mozi_server()
        # self.mozi_server.set_run_mode()
        self.mozi_server.set_decision_step_length(self.duration_interval)
