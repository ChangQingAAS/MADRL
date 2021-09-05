import psutil
import datetime
import numpy as np

# 调用Agent算法：DuelingDQN  
from DuelingDQN import train
from DuelingDQN import buffer
from env import Env_Uav_Avoid_Tank
import etc
from agents import Agents_Uav_Avoid_Tank
from pic_utils import show_pic
from file_utils import file

#  设置墨子安装目录下bin目录为MOZIPATH，程序会自动启动墨子
# os.environ['MOZIPATH'] = 'D:\\MoZiSystem\\Mozi\\MoziServer\\bin'


def main():
    """
    主函数，用于构建训练环境及智能体，并进行训练
    """

    # 创建环境对象, 并启动之。仿真服务器是环境的一部分，它也在环境中启动了
    env = Env_Uav_Avoid_Tank(etc.SERVER_IP, etc.SERVER_PORT, etc.SCENARIO_NAME,
                             etc.SIMULATE_COMPRESSION, etc.DURATION_INTERVAL,
                             etc.SERVER_PLAT)

    # 创建输出文件类，并进行文件初始化
    out_file = file()
    start_epoch, start_step, current_step = out_file.initialize()

    # 创建智能体对象
    agent = Agents_Uav_Avoid_Tank(env, start_epoch)

    # 启动训练
    try:
        for epoch_counter in range(start_epoch, etc.MAX_EPISODES):
            print("\n%s：第%s轮训练开始======================================" %
                  (datetime.datetime.now(), epoch_counter))

            # 重置智能体、环境、训练器
            state_now, reward_now = env.reset()
            agent.reset()

            # 智能体作决策，产生动作，动作影响环境，智能体根据动作的效果进行训练优化
            for step in range(etc.MAX_STEPS):
                # 智能体根据当前的状态及回报值，进行决策，生成下一步的动作
                action_new = agent.choose_action(np.float32(state_now),
                                                 reward_now)

                # 环境执行动作，生成下一步的状态及回报值
                state_new, reward_new = env.execute_action(action_new)

                # 根据推演结果，训练一次智能体
                agent.train(np.float32(state_now), action_new, reward_new,
                            np.float32(state_new), current_step)

                current_step += 1
                out_file.write_step(current_step)

                # 更新状态、回报值
                state_now = state_new
                reward_now = reward_new

                # 打印infO
                print("\n%s：轮数:%s 决策步数:%s  Reward:%.2f" %
                      (datetime.datetime.now(), epoch_counter, step, reward_now))

                # 检查是否结束本轮推演
                if env.check_done(action_new):
                    break

                # if current_step % 100 == 0:
                #     show_pic()

            out_file.write_epoch(epoch_counter)

    except KeyboardInterrupt:
        pass


main()