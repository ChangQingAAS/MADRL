import os
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np


class DuelingDeepQNetwork(nn.Module):
    def __init__(self, lr, n_actions, name, input_dims, chkpt_dir):
        super(DuelingDeepQNetwork, self).__init__()

        # self.checkpoint_dir = chkpt_dir
        # self.checkpoint_file = os.path.join(self.checkpoint_dir, name)

        self.conv1 = nn.Conv2d(input_dims, 32, 8, stride=4)
        self.conv2 = nn.Conv2d(32, 64, 4, stride=2)
        self.conv3 = nn.Conv2d(64, 64, 3, stride=1)

        # fc_input_dims = self.calculate_conv_output_dims(input_dims)
        fc_input_dims = input_dims

        self.fc1 = nn.Linear(fc_input_dims, 1024)
        self.fc2 = nn.Linear(1024, 512)
        self.V = nn.Linear(512, 1)
        self.A = nn.Linear(512, n_actions)

        self.optimizer = optim.RMSprop(self.parameters(), lr=lr)
        self.loss = nn.MSELoss()
        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        self.to(self.device)


    def calculate_conv_output_dims(self, input_dims):
        state = torch.zeros(1, input_dims)
        dims = self.conv1(state)
        dims = self.conv2(dims)
        dims = self.conv3(dims)
        return int(np.prod(dims.size()))

    def forward(self, state):
        # # 这一行是额外添加的，等到代码跑起来再修改
        # state = torch.ones(3, 3, 32,32)

        # conv1 = F.relu(self.conv1(state))
        # conv2 = F.relu(self.conv2(conv1))
        # conv3 = F.relu(self.conv3(conv2))
        # conv_state = conv3.view(conv3.size()[0], -1)
        # flat1 = F.relu(self.fc1(conv_state))
        # flat2 = F.relu(self.fc2(flat1))

        # V = self.V(flat2)
        # A = self.A(flat2)

        # return V, A
        V = torch.rand(3,3).type(torch.FloatTensor)
        A = torch.rand(3,3).type(torch.FloatTensor)
        V.requires_grad_()
        A.requires_grad_()
        print("V is ",V)

        return V,A

    def save_checkpoint(self):
        print('... saving checkpoint ...')
        T.save(self.state_dict(), self.checkpoint_file)

    def load_checkpoint(self):
        print('... loading checkpoint ...')
        self.load_state_dict(T.load(self.checkpoint_file))