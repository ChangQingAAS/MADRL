# 时间 ： 2020/7/20 17:03
# 作者 ： Dixit
# 文件 ： bt_main_antiship.py
# 项目 ： moziAIBT
# 版权 ： 北京华戍防务技术有限公司

import os
import sys
# 针对cmd命令行把mozi_ai_sdk的工程目录添加到sys.path（pycharm运行，不需要）
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = curPath.partition('mozi_ai_sdk')[0]

sys.path.append(rootPath)

# 获取IP和Port
arg = sys.argv
# arg = ['C:/Users/qa/Desktop/moziAI/mozi_ai_sdk/test/bt_test/bt_main_antiship.py', '-IP', '192.168.1.41', '-Port',
# '3002','-Side','红方']
# IP = arg[2]
# PORT = arg[4]
# side_name = arg[-1]
print(arg)
from mozi_ai_sdk.test.bt_test.bt_env_remote import Environment
from mozi_ai_sdk.test.bt_test import bt_env as environment
from mozi_ai_sdk.test.bt_test import bt_etc_antiship as etc
from mozi_ai_sdk.test.bt_test.bt_agent_antiship import CAgent


def run(side_name, env):
    """
    行为树运行的起始函数
    :param env: 墨子环境
    :return:
    """
    # 连接服务器，产生mozi_server
    # pdb.set_trace()
    env.start()
    # 实例化智能体
    agent = CAgent()
    n = 0
    while True:
        # 重置函数，加载想定,拿到想定发送的数据
        env.reset()
        # 初始化行为树
        agent.init_bt(env, side_name, 0, '')
        i = 0
        while True:
            scenario = env.step()
            # 更新动作
            agent.update_bt(side_name, scenario)
            scenario.mozi_server.run_grpc_simulate()

            side = env.scenario.get_side_by_name(side_name)
            score = side.get_score()
            # score_log = side.m_ScoringLogs
            # if score_log:
            #     score_log = side.m_ScoringLogs.split('。')[1]
            # # print('推演步数：%s,%s得分：%s' % (i, side_name, env.redside.iTotalScore))
            #     print('推演步数：%s,%s得分：%s,  %s：' % (i, side_name, score, score_log))
            # else:
            print('推演步数：%s,%s得分：%s' % (i, side_name, score))
            i += 1

            # 判断response的状态，什么时候结束
            break_flag = False
            response_dic = scenario.get_responses()
            for _, v in response_dic.items():
                if v.Type == 'EndOfDeduction':
                    break_flag = True
                    print('打印出标记：EndOfDeduction')
                    break
            if break_flag:
                print('当前第%s轮推演已结束' % n)
                n += 1
                break


# SCENARIO_NAME 想定名称通过连接GRPC，给我
def main():
    side_name = '红方'
    if len(arg) != 1:
        IP = arg[2]
        PORT = arg[4]
        side_name = arg[-1]
        print(side_name)
        env = Environment(IP, PORT, etc.DURATION_INTERVAL)
    else:
        env = environment.Environment(etc.SERVER_IP, etc.SERVER_PORT, etc.PLATFORM, etc.SCENARIO_NAME,
                                      etc.SIMULATE_COMPRESSION,
                                      etc.DURATION_INTERVAL,
                                      etc.SYNCHRONOUS)

    run(side_name, env)


main()
