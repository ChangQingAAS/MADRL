# 时间 ： 2020/7/20 17:03
# 作者 ： Dixit
# 文件 ： bt_main_antiship.py
# 项目 ： moziAIBT
# 版权 ： 北京华戍防务技术有限公司
from actions import get_two_point_distance

from mozi_ai_sdk.test.bt_test.bt_env import Environment
from mozi_ai_sdk.test.bt_test import bt_etc_antiship as etc
from mozi_ai_sdk.test.bt_test.bt_agent import CAgent
from mozi_simu_sdk.aircraft import CAircraft
import sys


def run(env):
    """
       行为树运行的起始函数
       :param env: 墨子环境
       :return:
       """
    while True:
    # 连接服务器，产生mozi_server
        env.start()
        # 实例化智能体
        agent = CAgent()
        n = 0
        while True:
            # 重置函数，加载想定,拿到想定发送的数据
            env.reset()
            # 初始化行为树
            agent.init_bt(env, '红方', 0, '')
            i = 0
            while True:
                scenario = env.step()
                # 更新动作
                agent.update_bt(scenario)
                scenario.mozi_server.run_simulate()
                # side = env.scenario.get_side_by_name('红方')
                # score = side.get_score()
                # score_log = side.m_ScoringLogs
                # if score_log:
                #     score_log = side.m_ScoringLogs.split('。')[1]
                #     print('推演步数：%s,%s得分：%s,  %s：' % (i, '红方', score, score_log))
                # else:
                #     print('推演步数：%s,%s得分：%s' % (i, '红方', score))
                print('推演步数：%s,红方得分：%s' % (i, env.redside.iTotalScore))
                i += 1

                time = scenario.m_Duration.split('@')
                duration = int(time[0]) * 86400 + int(time[1]) * 3600 + int(time[2]) * 60
                if scenario.m_StartTime + duration <= scenario.m_Time:
                    print('第%s轮推演已结束！' % n)
                    n += 1
                    break
                    # sys.exit(0)
                else:
                    pass

            if n % 10 == 0:
                break




def main():
    env = Environment(etc.SERVER_IP, etc.SERVER_PORT, etc.PLATFORM, etc.SCENARIO_NAME, etc.SIMULATE_COMPRESSION,
                      etc.DURATION_INTERVAL,
                      etc.SYNCHRONOUS)
    run(env)


main()
