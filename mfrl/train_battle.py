import argparse
import os
import tensorflow as tf
import numpy as np
import magent

from examples.battle_model.algo import spawn_ai
from examples.battle_model.algo import tools
from examples.battle_model.senario_battle import play

# 语法：os.path.dirname(path)
# 功能：去掉文件名，返回目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# 线性衰减
# linear_decay，使用线性函数，根据数值和给定的起始点之间的距离，计算其衰减程度
def linear_decay(epoch, x, y):
    min_v, max_v = y[0], y[-1]  # y是啥
    start, end = x[0], x[-1]  # x是啥

    if epoch == start:
        return min_v

    eps = min_v  # ？

    for i, x_i in enumerate(x):
        if epoch <= x_i:
            interval = (y[i] - y[i - 1]) / (x_i - x[i - 1])
            eps = interval * (epoch - x[i - 1]) + y[i - 1]
            break

    return eps


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # 选择算法
    parser.add_argument('--algo',
                        type=str,
                        choices={'ac', 'mfac', 'mfq', 'il'},
                        help='choose an algorithm from the preset',
                        required=True)
    # 更新间隔
    parser.add_argument('--save_every',
                        type=int,
                        default=10,
                        help='decide the self-play update interval')
    # Q-earning 更新间隔
    parser.add_argument(
        '--update_every',
        type=int,
        default=5,
        help='decide the udpate interval for q-learning, optional')
    # 训练回合
    parser.add_argument('--n_round',
                        type=int,
                        default=2000,
                        help='set the trainning round')
    # 是否渲染
    parser.add_argument('--render',
                        action='store_true',
                        help='render or not (if true, will render every save)')
    # 图片大小
    parser.add_argument(
        '--map_size', type=int, default=40,
        help='set the size of map')  # then the amount of agents is 64
    # 最大步数 不知道干什么的
    parser.add_argument('--max_steps',
                        type=int,
                        default=400,
                        help='set the max steps')

    # 获取参数
    args = parser.parse_args()

    # 初始化环境
    env = magent.GridWorld('battle', map_size=args.map_size)
    # 设置渲染文件夹
    env.set_render_dir(
        os.path.join(BASE_DIR, 'examples/battle_model', 'build/render'))
    # 句柄（Handle）是一个是用来标识对象或者项目的标识符，中间接口？？？
    handles = env.get_handles()

    # tf.ConfigProto()函数用在创建session的时候对session进行参数配置。
    # allow_soft_placement=True：如果是true，则允许tensorflow自动分配设备
    # log_device_placement=True：如果是true，记录每个节点分配到哪个设备上日志，用于方便调试
    tf_config = tf.ConfigProto(allow_soft_placement=True,
                               log_device_placement=False)
    # gpu_options.allow_growth：用于动态申请显存，从少到多慢慢增加gpu容量
    # gpu_options.per_process_gpu_memory_fraction：用于限制gpu使用率，拿出多少给进程使用
    # gpu_options.allow_growth 当使用GPU时候，Tensorflow运行自动慢慢达到最大GPU的内存
    tf_config.gpu_options.allow_growth = True

    # log文件夹和model文件夹
    log_dir = os.path.join(BASE_DIR, 'data/tmp'.format(args.algo))
    model_dir = os.path.join(BASE_DIR, 'data/models/{}'.format(args.algo))

    # use_mf表示是否使用平均场算法
    if args.algo in ['mfq', 'mfac']:
        use_mf = True
    else:
        use_mf = False

    start_from = 0

    sess = tf.Session(config=tf_config)
    # 用算法名+‘-me'或'-opponent’表示敌我双方
    models = [
        spawn_ai(args.algo, sess, env, handles[0], args.algo + '-me',
                 args.max_steps),
        spawn_ai(args.algo, sess, env, handles[1], args.algo + '-opponent',
                 args.max_steps)
    ]
    sess.run(tf.global_variables_initializer())
    runner = tools.Runner(sess,
                          env,
                          handles,
                          args.map_size,
                          args.max_steps,
                          models,
                          play,
                          render_every=args.save_every if args.render else 0,
                          save_every=args.save_every,
                          tau=0.01,
                          log_name=args.algo,
                          log_dir=log_dir,
                          model_dir=model_dir,
                          train=True)  # tau 是折扣率？？还是soft replacement？

    for k in range(start_from, start_from + args.n_round):
        # ???
        # 通常为了模型能更好的收敛,随着训练的进行,希望能够减小学习率,以使得模型能够更好地收敛,找到loss最低的那个点.
        # linear_deacy 可能是用来调整学习率的
        eps = linear_decay(k, [0, int(args.n_round * 0.8), args.n_round],
                           [1, 0.2, 0.1])
        runner.run(eps, k)
