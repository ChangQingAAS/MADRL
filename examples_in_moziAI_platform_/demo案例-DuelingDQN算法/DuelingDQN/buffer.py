import numpy as np
import random
from collections import deque

class ReplayBuffer:

    def __init__(self, size):
        # 初始化buffer唯一个双端队列（先进先出，即自带更新，无需自己写函数处理多出来的部分）
        self.buffer = deque(maxlen=size)
        # buffer最大size
        self.mem_size = size
        # buffer当前大小
        self.len = 0

    # 抽样
    def sample_memory(self, batch_size):

        # 抽样
        batch = []
        batch_size = min(batch_size, self.len)
        batch = random.sample(self.buffer, batch_size)
        
        # 分开
        state_arr = np.float32([arr[0] for arr in batch])
        action_arr = np.float32([arr[1] for arr in batch])
        reward_arr = np.float32([arr[2] for arr in batch])
        state1_arr = np.float32([arr[3] for arr in batch])

        return state_arr, action_arr, reward_arr, state1_arr

    # 返回buffer当前大小
    def len(self):
        return self.len

    # 保存经验
    def store_transition(self, state, action, reward, state_):
        trainsition = (state, action, reward, state_)
        self.len += 1
        if self.len > self.mem_size:
            self.len = self.mem_size
        self.buffer.append(trainsition)
