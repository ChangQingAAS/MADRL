# 引用Agent
from mozi_ai_sdk.agents import base_agent

import numpy as np

# 调用Agent算法：DuelingDQN
from DuelingDQN import trainer
from DuelingDQN import buffer
import etc
from utils.pic_utils import write_loss

class Agents_Uav_Avoid_Tank(base_agent.BaseAgent):
    """
    无人机攻击坦克案例的智能体
    """
    def __init__(self, env, start_epoch=0):
        super(Agents_Uav_Avoid_Tank, self).__init__()
        
        self.episodes = int(start_epoch)

        # 创建训练器 
        # TODO： 修改这里传入的参数
        self.trainer = trainer.Trainer(
            # None, 把loss写入文件的函数
            write_loss,
            # 看做class trainer中的action_lim
            env.action_max, 
            # CPU or GPU
            etc.device,
            etc.MODELS_PATH)
        self.env = env
        self.train_step = 0  # 当前决策步数

        # 设置状态空间维度及动作空间维度
        self.setup(env.state_space_dim, env.action_space_dim)

    def reset(self):
        """
        重置
        """
        # 保存一下已经训练的轮数
        # save_moedl还没有做好
        # self.trainer.save_model(self.episodes, etc.MODELS_PATH)

        # 回合数++
        self.episodes += 1

    def setup(self, state_space, action_space):
        """
        设置状态空间，动作空间
        """
        self.state_space = state_space
        self.action_space = action_space

    # TODO： 
    # 这个函数是从DDPG流传下来的，参数已经对不上了
    # 现在这个函数的功能是由choose_action代替的，后面需要升级一下
    def make_decision(self, state_now, reward_now):
        """
        功能说明：智能体的决策函数，该函数根据从环境所得的状态及回报值来决定下一步该执行什么动作。
        执行流程：训练器生成动作
        参数：state_now:当前状态空间 reward_now:当前的回报值
        """
        super(Agents_Uav_Avoid_Tank, self).step(state_now)
        state = np.float32(state_now)  # 强制转化为浮点类型

        # 1/3的动作随机生成，2/3的动作由模型生成
        if self.episodes % 3 == 0:
            action = self.trainer.get_exploration_action(
                state)  # 通过模型来生成动作，利用，
        else:
            action = self.trainer.get_exploitation_action(state)  # 随机生成动作。

        # “环境”的推进函数，其中包括让墨子服务器推进
        # new_observation, reward, done, info = self.env.step(action)

        # # 是否结束
        # if done:
        #     new_state = None
        # else:
        #     new_state = np.float32(new_observation)
        #     self.memory.add(state, action, reward, new_state)
        #
        # observation = new_observation
        # self.trainer.optimize(self.train_step)
        # self.train_step +=1

        # 返回动作
        return action
    
    def train(self, state_last, action_last, reward_now, state_new, cur_step):
        """
        功能说明：根据动作执行结果，训练一次智能体
        参数：state_now:当前状态空间 reward_now:当前的回报值
        """
        # 添加最新经验，并优化训练一把，再做决策
        self.trainer.store_transition(state_last, action_last, reward_now, state_new)
        # print("self.trainer is ", self.trainer.memory)
        self.trainer.optimize()
        self.train_step += 1

        # 返回动作
        return True

    def choose_action(self, observation, reward_now):
        print("observation[:3] is ", observation[:3])
        action = self.trainer.choose_action(observation[:3])
        print("action is ", action)
        return action
