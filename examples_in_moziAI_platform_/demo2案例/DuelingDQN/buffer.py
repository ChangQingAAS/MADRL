import numpy as np
import random
from collections import deque

class ReplayBuffer:
    # 初始化
    def __init__(self, size):
        # 初始化buffer唯一个双端队列（先进先出，即自带更新）
        self.buffer = deque(maxlen=size)
        self.mem_size = size
        self.len = 0

    # 抽样
    def sample_memory(self, batch_size):
        batch = []
        batch_size = min(batch_size, self.len)
        batch = random.sample(self.buffer, batch_size)

        s_arr = np.float32([arr[0] for arr in batch])
        a_arr = np.float32([arr[1] for arr in batch])
        r_arr = np.float32([arr[2] for arr in batch])
        s1_arr = np.float32([arr[3] for arr in batch])

        return s_arr, a_arr, r_arr, s1_arr

    # 返回buffer大小
    def len(self):
        return self.len

    def store_transition(self, state, action, reward, state_):
        trainsition = (state, action, reward, state_)
        self.len += 1
        if self.len > self.mem_size:
            self.len = self.mem_size
        self.buffer.append(trainsition)
