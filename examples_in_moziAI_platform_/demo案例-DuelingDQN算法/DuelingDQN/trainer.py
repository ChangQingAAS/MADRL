from __future__ import division

import datetime
import math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable

from . import buffer
from . import net


class Trainer:
    '''
    训练器:
        含net,noise,buffer，optimizer,loss_func
    '''
    def __init__(self,
                 write_loss,
                 action_lim,
                 dev,
                 model_save_path,
                ):
        self.gamma = 0.99  # 奖励随时间步的衰减因子
        self.epsilon = 0.9
        self.lr = 0.001
        self.n_actions = 3
        self.input_dims = 3
        self.batch_size = 32
        self.TARGET_REPLACE_ITER = 100
        self.eps_min = 0.01
        self.eps_dec = 1e-5
        self.action_space = [i for i in range(self.n_actions)]
        self.learn_step_counter = 0
        self.mem_size = 50000
        self.chkpt_dir='tmp/dueling_dqn'
        self.device = dev
        self.action_lim = action_lim  # 应该是最大值，TODO：验证一下
        self.iter = 0
        self.write_loss = write_loss

        self.ACTION_NUM = self.n_actions
        self.STATE_NUM = self.input_dims
        self.ENV_A_SHAPE = 0
        self.memory = buffer.ReplayBuffer(self.mem_size)
        self.network = net.DuelingDeepQNetwork(
            self.lr,
            self.n_actions,
            self.input_dims,
        )
        self.loss_func = nn.MSELoss()
        self.optimizer = torch.optim.Adam(self.network.eval_net.parameters(),
                                          lr=self.lr)

    # 存储转换状态
    def store_transition(self, state, action, reward, state_):
        self.memory.store_transition(state, action, reward, state_)

    # 抽样
    def sample_memory(self):
        state, action, reward, new_state = self.memory.sample_memory(
            self.batch_size)

        states = torch.tensor(state).to(self.q_eval.device)
        rewards = torch.tensor(reward).to(self.q_eval.device)
        actions = torch.tensor(action).to(self.q_eval.device)
        states_ = torch.tensor(new_state).to(self.q_eval.device)

        return states, actions, rewards, states_

    # 选择动作
    def choose_action(self, observation):  # epsilon-greedy策略：避免收敛在局部最优
        # print("observation[:3] is ", observation[:3])

        observation = torch.unsqueeze(torch.FloatTensor(observation), 0)
        EPSILON = 1
        # TODO： 动作的输出有问题
        if np.random.uniform() <= EPSILON:  # 以epsilon的概率利用
            actions_value = self.network.eval_net.forward(observation)
            print("actions_value is ", actions_value)
            action = torch.max(actions_value, 1)[1].data.numpy()
            print("action is ", action)
        else:  # 以1-epsilon的概率探索
            print("self.n_actions is ", self.n_actions)
            action = np.random.randint(0, self.n_actions)
        return action

    def optimize(self):
        if self.network.learn_step_counter % self.TARGET_REPLACE_ITER == 0:
            # TargetduelingdqnNet: 用eval_net来更改targetnet的参数
            self.network.target_net.load_state_dict(
                self.network.eval_net.state_dict())
        self.network.learn_step_counter += 1

        batch_state, batch_action, batch_reward, batch_next_state = self.memory.sample_memory(
            self.batch_size)

        batch_state = torch.from_numpy(batch_state).float()
        batch_action = torch.from_numpy(batch_action).long()
        batch_reward = torch.from_numpy(batch_reward).float()
        batch_next_state = torch.from_numpy(batch_next_state).float()

        print("batch_state.shape is ", batch_state.shape)
        print("batch_action.shape is ", batch_action.shape)
        print("batch_reward.shape is ", batch_reward.shape)
        # print("batch_next_state.shape is ", batch_next_state.shape)

        q_next = self.network.target_net(
            batch_next_state).detach()  # 切一段下来，避免反向传播
        print("q_next.shape is ", q_next.shape)

        # print("self.network.eval_net(batch_state) is ",self.network.eval_net(batch_state))
        q_eval = self.network.eval_net(batch_state)
        print("q_eval.shape is ", q_eval.shape)

        # 补丁
        batch_reward = torch.randn(q_eval.shape)

        q_target = batch_reward + self.gamma * q_next.max(1)[0].view(
            -1, 1)  # 使用target_net来推荐最大reward值
        print("q_target.shape is ", q_target.shape)

        loss = self.loss_func(q_eval, q_target)  # 计算loss

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
