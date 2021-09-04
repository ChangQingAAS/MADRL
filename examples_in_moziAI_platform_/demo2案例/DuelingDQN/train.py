from __future__ import division

import datetime
import math
import numpy as np
import torch
import torch as T
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable

from . import utils

from .  import buffer
from .  import model

BATCH_SIZE = 128  #
LEARNING_RATE = 0.001  # 训练学习率
GAMMA = 0.99  # 奖励随时间步的衰减因子
TAU = 0.001  # model参数软更新系数


class Trainer:
    '''训练器'''
    def __init__(self,
                 write_loss,
                 action_lim,
                 dev,
                 model_save_path,
                 gamma=0.99,
                 epsilon=0.9,
                 lr=0.01,
                 n_actions=12,
                 input_dims=3,
                 mem_size=50000,
                 batch_size=32,
                 eps_min=0.01,
                 eps_dec=1e-5,
                 replace=10000,
                 algo='DuelingDQNAgent',
                 chkpt_dir='tmp/dqn'
                 ):
        self.gamma = gamma
        self.epsilon = epsilon
        self.lr = lr
        self.n_actions = n_actions
        self.input_dims = input_dims
        self.batch_size = batch_size
        self.eps_min = eps_min
        self.eps_dec = eps_dec
        self.replace_target_cnt = replace
        self.algo = algo
        self.chkpt_dir = chkpt_dir
        self.action_space = [i for i in range(n_actions)]
        self.learn_step_counter = 0

        self.memory = buffer.ReplayBuffer(mem_size)
        self.q_eval = model.DuelingDeepQNetwork(self.lr,
                                          self.n_actions,
                                          input_dims=self.input_dims,
                                          name= self.algo + '_q_eval',
                                          chkpt_dir=self.chkpt_dir)

        self.q_next = model.DuelingDeepQNetwork(self.lr,
                                          self.n_actions,
                                          input_dims=self.input_dims,
                                          name= self.algo + '_q_next',
                                          chkpt_dir=self.chkpt_dir)

        # self.action_dim = action_dim 即n_actions
        self.action_lim = action_lim
        self.iter = 0
        self.noise = utils.OrnsteinUhlenbeckActionNoise(self.n_actions)
        self.device = dev
        self.write_loss = write_loss

    # 存储转换状态
    def store_transition(self, state, action, reward, state_):
        self.memory.store_transition(state, action, reward, state_)

    # 抽样
    def sample_memory(self):
        state, action, reward, new_state= self.memory.sample_memory(
            self.batch_size)

        states = T.tensor(state).to(self.q_eval.device)
        rewards = T.tensor(reward).to(self.q_eval.device)
        # dones = T.tensor(done).to(self.q_eval.device)
        actions = T.tensor(action).to(self.q_eval.device)
        states_ = T.tensor(new_state).to(self.q_eval.device)

        return states, actions, rewards, states_ 

    # 选择动作，这里的选择动作放在了Class Agent里，考虑把它放入env里的可能
    def choose_action(self, observation, reward_now):
        if np.random.random() > self.epsilon:
            state = T.tensor([observation],
                             dtype=T.float).to(self.q_eval.device)
            _, advantage = self.q_eval.forward(state)
            action = T.argmax(advantage).item()
        else:
            action = np.random.choice(self.action_space)

        return action

    # 应该算是更新网络参数吧
    def replace_target_network(self):
        if self.replace_target_cnt is not None and \
           self.learn_step_counter % self.replace_target_cnt == 0:
            self.q_next.load_state_dict(self.q_eval.state_dict())

    def decrement_epsilon(self):
        self.epsilon = self.epsilon - self.eps_dec \
                         if self.epsilon > self.eps_min else self.eps_min

    # 训练网络参数
    def optimize(self):
        # if self.memory.mem_cntr < self.batch_size:
        #     return

        self.q_eval.optimizer.zero_grad()

        self.replace_target_network()

        states, actions, rewards, states_ = self.sample_memory()

        V_s, A_s = self.q_eval.forward(states)
        V_s_, A_s_ = self.q_next.forward(states_)

        indices = np.arange(self.batch_size)

        # q_pred = T.add(V_s, (A_s - A_s.mean(dim=1, keepdim=True)))[indices,
        #                                                            actions]

        q_pred = T.add(V_s, (A_s - A_s.mean(dim=1, keepdim=True)))[0]
        print("q_pred is ",q_pred)

        q_next = T.add(V_s_,
                       (A_s_ - A_s_.mean(dim=1, keepdim=True))).max(dim=1)[0]

        print("q_next is",q_next)
        print("rewards is ",rewards)
        rewards = torch.randn(1,3).type(torch.FloatTensor)
        print("rewards is ",rewards)


        # q_next[dones] = 0.0
        q_target = rewards + self.gamma * q_next

        print("q_target is ",q_target)
        print("q_target.shape is ",q_target.shape)

        loss = self.q_eval.loss(q_target, q_pred).to(self.q_eval.device)
        print("loss is ",loss)
        print("loss.shape is ",loss.shape)
        # loss = loss.reshape(-1,1)
        # print("loss.shape is ",loss.shape)

        loss.backward(loss.clone().detach())
        self.q_eval.optimizer.step()
        self.learn_step_counter += 1

        self.decrement_epsilon()

    def get_models_path(self):
        return "./Models"

    ## TODO：加载模型和建立模型
    # def save_model(self, episode_count, model_save_path=None):
    #     '''
    #     保存模型
    #     '''
    #     # torch.save(self.target_actor.state_dict(), './Models/' + str(episode_count) + '_actor.pt')
    #     if model_save_path == None:
    #         model_save_path = self.get_models_path()
    #     torch.save(self.target_actor.state_dict(),
    #                model_save_path + str(episode_count) + '_actor.pt') 
    #     print("%s：%s Models saved successfully" %
    #           (datetime.datetime.now(), episode_count))
    #     # print("%s：轮数:%s 决策步数:%s  Reward:%.2f" % (datetime.now(), _ep, step, reward_now))

    # def load_models(self, episode, model_save_path=None):
    #     '''
    #     载入以前训练过的模型, 包括策略网络和价值网络
    #     '''
    #     if model_save_path == None:
    #         model_save_path = self.get_models_path()
    #     # self.critic.load_state_dict(torch.load(self.get_models_path() + str(episode) + '_critic.pt'))
    #     self.critic.load_state_dict(
    #         torch.load(model_save_path + str(episode) + '_critic.pt'))
    #     # self.actor.load_state_dict(torch.load(self.get_models_path() + str(episode) + '_actor.pt'))
    #     self.actor.load_state_dict(
    #         torch.load(model_save_path + str(episode) + '_actor.pt'))
    #     utils.hard_update(self.target_actor, self.actor)
    #     utils.hard_update(self.target_critic, self.critic)
    #     print("Models loaded successfully")

        # 保存模型
    def save_models(self):
        self.q_eval.save_checkpoint()
        self.q_next.save_checkpoint()

    # 加载模型
    def load_models(self):
        self.q_eval.load_checkpoint()
        self.q_next.load_checkpoint()

    #############  ADD  ###################
    def choose_action(self, observation):
        if np.random.random() > self.epsilon:
            state = torch.tensor([observation],
                             dtype=T.float).to(self.q_eval.device)
            _, advantage = self.q_eval.forward(state)
            action = torch.argmax(advantage).item()
        else:
            action = np.random.choice(self.action_space)

        return action
