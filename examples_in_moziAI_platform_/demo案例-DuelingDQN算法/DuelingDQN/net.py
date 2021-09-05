import os
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np

BATCH_SIZE = 32
LR = 0.01
EPSILON = 0.9
GAMMA = 0.9
TARGET_REPLACE_ITER = 100
MEMORY_CAPACITY = 2000
EPISODE_NUM = 400


class duelingdqnNet(nn.Module):
    def __init__(self, STATE_NUM, ACTION_NUM):
        super(duelingdqnNet, self).__init__()  # 使用了nn.Modules需要调用super以进行初始化

        self.ACTION_NUM = ACTION_NUM

        self.fc1_a = nn.Linear(in_features=STATE_NUM, out_features=512)   
        self.fc1_v = nn.Linear(in_features=STATE_NUM, out_features=512)   

        self.fc2_a = nn.Linear(in_features=512, out_features=ACTION_NUM)
        self.fc2_v = nn.Linear(in_features=512, out_features=1)

    def forward(self, x):
        print("x.shape is ", x.shape)
        a = F.relu(self.fc1_a(x))
        print("a.shape is ", a.shape)
        v = F.relu(self.fc1_v(x))
        print("v.shape is ", v.shape)

        a = self.fc2_a(a)
        print("a.shape is ", a.shape)
        v = self.fc2_v(v).expand(x.size(0), self.ACTION_NUM)
        print("v.shape is ", v.shape)

        x = a + v - a.mean(1).unsqueeze(1).expand(x.size(0), self.ACTION_NUM)
        print("x.shape is ", x.shape)
        return x


class DuelingDeepQNetwork(nn.Module):
    def __init__(self, lr, n_actions, input_dims):
        super(DuelingDeepQNetwork, self).__init__()

        self.ACTION_NUM = n_actions
        self.STATE_NUM = input_dims
        self.ENV_A_SHAPE = 0 

        self.eval_net = duelingdqnNet(self.STATE_NUM, self.ACTION_NUM)
        self.target_net = duelingdqnNet(self.STATE_NUM, self.ACTION_NUM)

        self.optimizer = torch.optim.Adam(self.eval_net.parameters(), lr=LR)
        self.learn_step_counter = 0

        self.loss_func = nn.MSELoss()

        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        self.to(self.device)
