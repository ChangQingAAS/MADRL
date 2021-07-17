import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))
import argparse
from examples.ising_model.multiagent.environment import IsingMultiAgentEnv
import examples.ising_model as ising_model
import numpy as np
import time

np.random.seed(13)

parser = argparse.ArgumentParser(description=None)
parser.add_argument('-n', '--num_agents', default=100, type=int)
parser.add_argument('-t', '--temperature', default=1, type=float)
parser.add_argument('-epi', '--episode', default=1, type=int)
parser.add_argument('-ts', '--time_steps', default=10000, type=int)# ？
parser.add_argument('-lr', '--learning_rate', default=0.1, type=float)
parser.add_argument('-dr', '--decay_rate', default=0.99, type=float) # 衰减率 温度下降的速度
parser.add_argument('-dg', '--decay_gap', default=2000, type=int) # ？
parser.add_argument('-ac', '--act_rate', default=1.0, type=float) # ？
parser.add_argument('-ns', '--neighbor_size', default=4, type=int)# 邻居为上下左右
parser.add_argument('-s',
                    '--scenario',
                    default='Ising.py',
                    help='Path of the scenario Python script.')
parser.add_argument('-p', '--plot', default=0, type=int)
args = parser.parse_args()

# 从脚本加载场景
ising_model = ising_model.load(args.scenario).Scenario()
# 创建多智能体环境
env = IsingMultiAgentEnv(world=ising_model.make_world(
    num_agents=args.num_agents, agent_view=1),
                         reset_callback=ising_model.reset_world,
                         reward_callback=ising_model.reward,
                         observation_callback=ising_model.observation,
                         done_callback=ising_model.done)# done是啥？

n_agents = env.n  # 多智能体数量
n_states = env.observation_space[0].n  # 状态数
n_actions = env.action_space[0].n  # 动作数
dim_Q_state = args.neighbor_size + 1  # 状态的数目
act_rate = args.act_rate  # ？
n_episode = args.episode  # 迭代次数
max_steps = args.time_steps  # ？
temperature = args.temperature  # 温度
if_plot = args.plot # 要不要画图
lr = args.learning_rate  # 学习率
decay_rate = args.decay_rate  # 衰变率 gmma？
decay_gap = args.decay_gap# ？

if if_plot:
    import matplotlib.pyplot as plt

# 选一个动作
def boltzman_explore(Q, temper, state, agent_index):
    action_probs_numes = []  # 行动_概率_数量
    denom = 0  # 分母
    for i in range(n_actions):
        try:
            val = np.exp(Q[agent_index, state, i] / temper)
        except OverflowError:
            return i
        action_probs_numes.append(val)
        denom += val
    # action_probs表示每种动作的概率
    action_probs = [x / denom for x in action_probs_numes]
    """
    def choice(a, size=None, replace=True, p=None)
    表示从a中随机选取size个数
    replacement 代表的意思是抽样之后还放不放回去，如果是False的话，那么通一次挑选出来的数都不一样，如果是True的话， 有可能会出现重复的，因为前面的抽的放回去了。
    p表示每个元素被抽取的概率，如果没有指定，a中所有元素被选取的概率是相等的。
    """
    # 随机选一个动作返回
    return np.random.choice(n_actions, 1, p=action_probs)


folder = "./ising_figs/" + time.strftime("%Y%m%d-%H%M%S") \
         + "-" + str(n_agents) + "-" + str(temperature) \
         + "-" + str(lr) + "-" + str(act_rate) + "/"
if not os.path.exists(folder):
    os.makedirs(folder)

# ？
epi_display = []
# 目标奖励
reward_target = np.array([[2, -2], [1, -1], [0, 0], [-1, 1], [-2, 2]])

# i_episode 用于做n_episode的counter
for i_episode in range(n_episode):

    # 观察环境
    obs = env.reset()
    # 堆叠？一般用来增加维度
    obs = np.stack(obs)

    # 序参数 = (num_up - num_down) / num_agents
    order_param = 0.0
    # 最大序。最大序号_步数？
    max_order, max_order_step = 0.0, 0
    # 上还是下
    o_up, o_down = 0, 0
    # 定义Q值，下标分别为agent的序号，当前状态，当前动作
    Q = np.zeros((n_agents, dim_Q_state, n_actions))

    if if_plot:
        # 创建自定义图像
        plt.figure(2)
        # # 打开交互模式
        plt.ion()
        ising_plot = np.zeros((int(np.sqrt(n_agents)), int(np.sqrt(n_agents))),
                              dtype=np.int32)
        # 默认情况下，imshow将数据标准化为最小和最大值。 
        # 您可以使用vmin和vmax参数或norm参数来控制（如果您想要非线性缩放）
        im = plt.imshow(ising_plot,
                        cmap='gray',
                        vmin=0,
                        vmax=1,
                        interpolation='none')
        im.set_data(ising_plot)

    # ？？？
    timestep_display = []
    done_ = 0
    current_t = 0.3
    
    # 我的理解是 max_steps是batchsize
    for t in range(max_steps):
        action = np.zeros(n_agents, dtype=np.int32)

        if t % decay_gap == 0:
            current_t *= decay_rate

        if current_t < temperature:
            current_t = temperature

        # i 表示agent的序号
        for i in range(n_agents):
            # 用于统计数组中非零元素的个数
            # 用这个代替状态？
            obs_flat = np.count_nonzero(obs[i] == 1)
            # def boltzman_explore(Q, temper, state, agent_index):
            # 表示第i个智能体采取的动作
            action[i] = boltzman_explore(Q, current_t, obs_flat, i)

        display = action.reshape((int(np.sqrt(n_agents)), -1))
        # notes: np.expand_dims:用于扩展数组的形状，axis表示在哪里插入1维的[]
        # 只插入空【】，不改变数据
        action_expand = np.expand_dims(action, axis=1)

        # take 这些动作（策略）
        obs_, reward, done, order_param, ups, downs = env.step(action_expand)
        obs_ = np.stack(obs_)

        # 均方误差
        mse = 0
        # 从numberf_agents里选出act_rate * number_agents个，形成一个策略组，名为act_group
        act_group = np.random.choice(n_agents,
                                     int(act_rate * n_agents),
                                     replace=False)
        # 遍历该策略组
        for i in act_group:
            # 为啥让obs_flat 表示状态
            obs_flat = np.count_nonzero(obs[i] == 1)
            # 更新Q值
            # 感觉和paper里的更新Q值的方法不一样
            Q[i, obs_flat, action[i]] = Q[i, obs_flat, action[i]] + lr * (reward[i] - Q[i, obs_flat, action[i]])
            # reward_target[obs_flat, action[i]] 为公式里的yj
            mse += np.power((Q[i, obs_flat, action[i]] -
                             reward_target[obs_flat, action[i]]), 2)

        mse /= n_agents
        obs = obs_

        timestep_display.append(display)

        # 如果自旋方向差异太大
        if order_param > max_order:
            # 则更新序参数，max_order_step和T是啥？，t是当前batch的counter吗？
            max_order, max_order_step = order_param, t
            o_up, o_down = ups, downs
            if if_plot:
                plt.figure(2)
                ising_plot = display
                im.set_data(ising_plot)
                plt.savefig(folder + '%d-%d-%d-%.3f-%s.png' %
                            (t, ups, downs, order_param,
                             time.strftime("%Y%m%d-%H%M%S")))
            print("+++++++++++++++++++++++++++++")

        if abs(max_order - order_param) < 0.001:
            done_ += 1
        else:
            done_ = 0

        if done_ == 500 or t > max_steps:  # or order_param == 1.0:
            # if the order param stop for 500 steps, then quit
            break

        print(
            'E: %d/%d, reward = %f, mse = %f, Order = %f, Up = %d, Down = %d' %
            (i_episode, t, sum(reward), mse, order_param, ups, downs))

    if if_plot:
        plt.figure(2)
        ising_plot = display
        im.set_data(ising_plot)
        plt.savefig(
            folder + '%d-%d-%d-%.3f-%s.png' %
            (t, ups, downs, order_param, time.strftime("%Y%m%d-%H%M%S")))

    print('Episode: %d, MaxO = %f at %d (%d/%d)' %
          (i_episode, max_order, max_order_step, o_up, o_down))
    epi_display.append(timestep_display)

np.save(folder + 'display', np.asarray(epi_display))
