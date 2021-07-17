import tensorflow as tf
import numpy as np

from magent.gridworld import GridWorld


class ValueNet:
    def __init__(self, sess, env, handle, name, update_every=5, use_mf=False, learning_rate=1e-4, tau=0.005, gamma=0.95):
        # assert isinstance(env, GridWorld)
        self.env = env
        self.name = name
        self._saver = None
        self.sess = sess

        self.handle = handle
        # 观察
        self.view_space = env.get_view_space(handle)
        assert len(self.view_space) == 3
        # feat 观察？？
        self.feature_space = env.get_feature_space(handle)
        self.num_actions = env.get_action_space(handle)[0]

        self.update_every = update_every
        self.use_mf = use_mf  # 使用 平均场的 触发器
        self.temperature = 0.1 # 为啥battle_moddle 里也有温度？

        self.lr= learning_rate
        self.tau = tau
        self.gamma = gamma

        with tf.variable_scope(name or "ValueNet"):
            self.name_scope = tf.get_variable_scope().name
            # placeholder()函数是在神经网络构建graph的时候在模型中的占位，
            # 此时并没有把要输入的数据传入模型，它只会分配必要的内存。
            # 等建立session，在会话中，运行模型的时候通过feed_dict()函数向占位符喂入数据。
            self.obs_input = tf.placeholder(tf.float32, (None,) + self.view_space, name="Obs-Input")
            self.feat_input = tf.placeholder(tf.float32, (None,) + self.feature_space, name="Feat-Input")
            self.mask = tf.placeholder(tf.float32, shape=(None,), name='Terminate-Mask')

            if self.use_mf:
                self.act_prob_input = tf.placeholder(tf.float32, (None, self.num_actions), name="Act-Prob-Input")

            # TODO: 为了计算 Q-value, 使用 softmax
            self.act_input = tf.placeholder(tf.int32, (None,), name="Act")
            self.act_one_hot = tf.one_hot(self.act_input, depth=self.num_actions, on_value=1.0, off_value=0.0)

            # 计算的Q网络（估值？
            with tf.variable_scope("Eval-Net"):
                self.eval_name = tf.get_variable_scope().name
                # 估计Q值， 激活函数为relu
                self.e_q = self._construct_net(active_func=tf.nn.relu)
                # 预测啥?
                self.predict = tf.nn.softmax(self.e_q / self.temperature)
                # notes: tf.get_collection(key, scope=None
                # 该函数可以用来获取key集合中的所有元素，返回一个列表。列表的顺序依变量放入集合中的先后而定。
                # scope为可选参数，表示的是名称空间（名称域），
                # 如果指定，就返回名称域中所有放入‘key’的变量的列表，不指定则返回所有变量。
                self.e_variables = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope=self.eval_name)

            # 目标Q网络？
            with tf.variable_scope("Target-Net"):
                self.target_name = tf.get_variable_scope().name
                self.t_q = self._construct_net(active_func=tf.nn.relu)
                self.t_variables = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope=self.target_name)

            # 更新
            with tf.variable_scope("Update"):
                # 好像是这个式子：
                # https://www.zhihu.com/equation?tex=Q_%7Bj%2Ct%2B1%7D%28s%2Ca_j%2C%5Coverline+a_j%29%3D%281-%5Calpha%29Q_%7Bj%2Ct%7D%28s%2Ca_j%2C%5Coverline+a_j%29%2B%5Calpha%5Br_j%2B%5Cgamma+v_%7Bj%2Ct%7D%28s%27%29%5D%5Cqquad+%287%29
                self.update_op = [tf.assign(self.t_variables[i],
                                            self.tau * self.e_variables[i] + (1. - self.tau) * self.t_variables[i])
                                    for i in range(len(self.t_variables))]

            # 优化参数
            with tf.variable_scope("Optimization"):
                self.target_q_input = tf.placeholder(tf.float32, (None,), name="Q-Input")
                # 求Q值的max,不知道为啥e_q * act_独热
                self.e_q_max = tf.reduce_sum(tf.multiply(self.act_one_hot, self.e_q), axis=1)
                # 定义损失函数，可以推测mask中为1的个数为邻居个数
                self.loss = tf.reduce_sum(tf.square(self.target_q_input - self.e_q_max) * self.mask) / tf.reduce_sum(self.mask)
                # 优化参数：利用反向传播算法对权重和偏置项进行修正，也在运行中不断修正学习率。
                # 根据其损失量学习自适应，损失量大则学习率大，进行修正的角度越大，损失量小，修正的幅度也小，学习率就小，
                # 但是不会超过自己所设定的学习率。
                # 你自己定义的lr是不变的，但作用到具体运算中是lr乘一个系数，这个系数是变得，
                # 所谓自适应是adam通过改变这个系数实现实际学习率变化，而不是改变你定义的lr
                self.train_op = tf.train.AdamOptimizer(self.lr).minimize(self.loss)

    def _construct_net(self, active_func=None, reuse=False):# reuse ？
        # 2D卷积层(例如,图像上的空间卷积).
        # filters：整数,输出空间的维数(即卷积中的滤波器数).
        # kernel_size：2个整数的整数或元组/列表,指定2D卷积窗口的高度和宽度.可以是单个整数,以指定所有空间维度的相同值.
        conv1 = tf.layers.conv2d(self.obs_input, filters=32, kernel_size=3,
                                 activation=active_func, name="Conv1")# 输入层
        conv2 = tf.layers.conv2d(conv1, filters=32, kernel_size=3, activation=active_func,
                                 name="Conv2")# 隐藏层
        # tf.reshape改变数组形状
        # np,prod 计算数组乘积
        flatten_obs = tf.reshape(conv2, [-1, np.prod([v.value for v in conv2.shape[1:]])])# 输出层 ？
        
        # h是啥意思？
        # tf.layers.dense() dense ：把数组最后一维改为units
        # tf.layers.dense( input, units=k )会在内部自动生成一个权矩阵kernel和偏移项bias，
        # 各变量具体尺寸如下：
        #   对于尺寸为[m, n]的二维张量input， 
        #   tf.layers.dense()会生成：
        #       尺寸为[n, k]的权矩阵kernel，和尺寸为[m, k]的偏移项bias。
        #       内部的计算过程为y = input * kernel + bias，输出值y的维度为[m, k]。
        h_obs = tf.layers.dense(flatten_obs, units=256, activation=active_func,
                                name="Dense-Obs")
        h_emb = tf.layers.dense(self.feat_input, units=32, activation=active_func,
                                name="Dense-Emb", reuse=reuse)
        # 连接层（连接h_obs，h_emb
        concat_layer = tf.concat([h_obs, h_emb], axis=1)

        # 如果使用平均场算法
        if self.use_mf:
            prob_emb = tf.layers.dense(self.act_prob_input, units=64, activation=active_func, name='Prob-Emb')
            h_act_prob = tf.layers.dense(prob_emb, units=32, activation=active_func, name="Dense-Act-Prob")
            concat_layer = tf.concat([concat_layer, h_act_prob], axis=1)

        dense2 = tf.layers.dense(concat_layer, units=128, activation=active_func, name="Dense2")
        out = tf.layers.dense(dense2, units=64, activation=active_func, name="Dense-Out")

        q = tf.layers.dense(out, units=self.num_actions, name="Q-Value")

        return q

    # 这个函数返回的是啥啊？
    @property
    def vars(self):
        return tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope=self.name_scope)

    def calc_target_q(self, **kwargs):
        """计算目标Q值
        kwargs: {'obs', 'feature', 'prob', 'dones', 'rewards'}
        """
        feed_dict = {
            self.obs_input: kwargs['obs'],
            self.feat_input: kwargs['feature']
        }

        # prob应该是邻居的意思
        if self.use_mf:
            assert kwargs.get('prob', None) is not None
            feed_dict[self.act_prob_input] = kwargs['prob']

        t_q, e_q = self.sess.run([self.t_q, self.e_q], feed_dict=feed_dict)
        # notes:numpy.argmax(array, axis) 用于返回一个numpy数组中最大值的索引值。
        # 当一组中同时出现几个最大值时，返回第一个最大值的索引值。
        act_idx = np.argmax(e_q, axis=1)
        # notes:
        # 参数个数情况： np.arange()函数分为一个参数，两个参数，三个参数三种情况
        # 1）一个参数时，参数值为终点，起点取默认值0，步长取默认值1。
        # 2）两个参数时，第一个参数为起点，第二个参数为终点，步长取默认值1。
        # 3）三个参数时，第一个参数为起点，第二个参数为终点，第三个参数为步长。其中步长支持小数
        q_values = t_q[np.arange(len(t_q)), act_idx]

        # 好像是这个式子：
        # https://www.zhihu.com/equation?tex=y_j%3Dr_j%2B%5Cgamma+v_%7B%5Coverline+%5Cphi_j%7D%5E%7BMF%7D%28s%27%29
        target_q_value = kwargs['rewards'] + (1. - kwargs['dones']) * q_values.reshape(-1) * self.gamma

        return target_q_value

    def update(self):
        """Q-learning update"""
        self.sess.run(self.update_op)

    def act(self, **kwargs):
        """Act
        kwargs: {'obs', 'feature', 'prob', 'eps'}
        """
        feed_dict = {
            self.obs_input: kwargs['state'][0],
            self.feat_input: kwargs['state'][1]
        }
        # 为什么这个模型也有温度？
        self.temperature = kwargs['eps']

        if self.use_mf:
            assert kwargs.get('prob', None) is not None
            # 邻居数为什么要等于状态数？
            assert len(kwargs['prob']) == len(kwargs['state'][0])
            feed_dict[self.act_prob_input] = kwargs['prob']

        # take actions?
        actions = self.sess.run(self.predict, feed_dict=feed_dict)
        # 选出概率最大的动作
        actions = np.argmax(actions, axis=1).astype(np.int32)
        return actions

    def train(self, **kwargs):
        """训练模型
        kwargs: {'state': [obs, feature], 'target_q', 'prob', 'acts'}
        """
        feed_dict = {
            self.obs_input: kwargs['state'][0],
            self.feat_input: kwargs['state'][1],
            self.target_q_input: kwargs['target_q'],
            self.mask: kwargs['masks']
        }

        if self.use_mf:
            assert kwargs.get('prob', None) is not None
            feed_dict[self.act_prob_input] = kwargs['prob']

        feed_dict[self.act_input] = kwargs['acts']
        _, loss, e_q = self.sess.run([self.train_op, self.loss, self.e_q_max], feed_dict=feed_dict)
        # np.round 返回四舍五入的浮点数
        return loss, {'Eval-Q': np.round(np.mean(e_q), 6), 'Target-Q': np.round(np.mean(kwargs['target_q']), 6)}
