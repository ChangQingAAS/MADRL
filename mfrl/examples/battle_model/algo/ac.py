import os
import numpy as np
import tensorflow as tf

from . import tools


class ActorCritic:
    def __init__(self, sess, name, handle, env, value_coef=0.1, ent_coef=0.08, gamma=0.95, batch_size=64, learning_rate=1e-4):
        self.sess = sess
        self.env = env

        self.name = name
        self.view_space = env.get_view_space(handle)
        self.feature_space = env.get_feature_space(handle)
        self.num_actions = env.get_action_space(handle)[0]
        # 伽玛 折扣因子？
        self.gamma = gamma

        self.batch_size = batch_size
        self.learning_rate = learning_rate

        # 总损失中的价值系数 
        self.value_coef = value_coef  # coefficient of value in the total loss
        # 总损失中的熵系数
        self.ent_coef = ent_coef  # coefficient of entropy in the total loss

        # 初始化训练缓冲区
        self.view_buf = np.empty((1,) + self.view_space)
        self.feature_buf = np.empty((1,) + self.feature_space)
        self.action_buf = np.empty(1, dtype=np.int32)
        self.reward_buf = np.empty(1, dtype=np.float32)
        self.replay_buffer = tools.EpisodesBuffer()

        # 创建网络（观察网络和特征网络
        # notes:tf.get_variable()函数，它不受name_scope约束，已经声明过的变量就不能再声明了。
        with tf.variable_scope(name):
            self.name_scope = tf.get_variable_scope().name
            self._create_network(self.view_space, self.feature_space)
    
    @property
    def vars(self):
        # notes: @property装饰器会将方法转换为相同名称的只读属性,可以与所定义的属性配合使用，这样可以防止属性被修改。
        # 差别就是使用的时候是vars还是vars()，加不加括号而已
        # get_collection(key, scope=None)
        # 该函数的作用是从一个collection中取出全部变量，形成列个列表，key参数中输入的是collection的名称
        return tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope=self.name_scope)
    
    def flush_buffer(self, **kwargs):
        self.replay_buffer.push(**kwargs)

    def act(self, **kwargs):
        action = self.sess.run(self.calc_action, {
            self.input_view: kwargs['state'][0],
            self.input_feature: kwargs['state'][1]
        })
        # notes: reshape就是变成m*n的数组，astype是数据类型转换
        return action.astype(np.int32).reshape((-1,))

    def _create_network(self, view_space, feature_space):
        # notes:所以placeholder()函数是在神经网络构建graph的时候在模型中的占位，
        # 此时并没有把要输入的数据传入模型，它只会分配必要的内存。
        ''' tf.placeholder(
            dtype,
            shape=None,
            name=None
            )
        参数：
        dtype：数据类型。常用的是tf.float32,tf.float64等数值类型
        shape：数据形状。默认是None，就是一维值，也可以是多维（比如[2,3], [None, 3]表示列是3，行不定）
        name：名称
        # 等建立session，在会话中，运行模型的时候通过feed_dict()函数向占位符喂入数据。
        '''
        input_view = tf.placeholder(tf.float32, (None,) + view_space)
        input_feature = tf.placeholder(tf.float32, (None,) + feature_space)
        action = tf.placeholder(tf.int32, [None])
        reward = tf.placeholder(tf.float32, [None])

        hidden_size = [256]

        # fully connected
        # notes: numpy.prod(a, axis=None, dtype=None, out=None, ) 返回给定轴上的数组元素的乘积。
        # tf.shapes() 输入数组，输出该数组的维度
        flatten_view = tf.reshape(input_view, [-1, np.prod([v.value for v in input_view.shape[1:]])])
        '''
        tf.layers.dense()部分参数解释:
            inputs：输入该网络层的数据
            units：输出的维度大小，改变inputs的最后一维
            activation：激活函数，即神经网络的非线性变化
            输出结果的最后一维度就等于神经元的个数，即units的数值（神经元的个数）
        '''
        h_view = tf.layers.dense(flatten_view, units=hidden_size[0], activation=tf.nn.relu)
        h_emb = tf.layers.dense(input_feature,  units=hidden_size[0], activation=tf.nn.relu)

        """
        axis=0     代表在第0个维度拼接

        axis=1     代表在第1个维度拼接 

        对于一个二维矩阵，第0个维度代表最外层方括号所框下的子集，第1个维度代表内部方括号所框下的子集。维度越高，括号越小。
        """
        dense = tf.concat([h_view, h_emb], axis=1)
        dense = tf.layers.dense(dense, units=hidden_size[0] * 2, activation=tf.nn.relu)

        policy = tf.layers.dense(dense / 0.1, units=self.num_actions, activation=tf.nn.softmax)
        """
        tf.clip_by_value(y,1e-10,1.0)， 
        功能：可以将一个张量中的数值限制在一个范围之内。
        （可以避免一些运算错误:可以保证在进行log运算时，不会出现log0这样的错误或者大于1的概率）
        参数：
        当y小于1e-10时，输出1e-10；
        当y大于1e-10小于1.0时，输出原值；
        当y大于1.0时，输出1.0
        """
        policy = tf.clip_by_value(policy, 1e-10, 1-1e-10)

        """
        tf.multinomial(logits, num_samples, seed=None, name=None)
        从multinomial分布中采样，样本个数是num_samples，每个样本被采样的概率由logits给出
        """
        self.calc_action = tf.multinomial(tf.log(policy), 1)

        value = tf.layers.dense(dense, units=1)
        value = tf.reshape(value, (-1,))

        action_mask = tf.one_hot(action, self.num_actions)
        advantage = tf.stop_gradient(reward - value)

        log_policy = tf.log(policy + 1e-6)
        log_prob = tf.reduce_sum(log_policy * action_mask, axis=1)

        pg_loss = -tf.reduce_mean(advantage * log_prob)
        vf_loss = self.value_coef * tf.reduce_mean(tf.square(reward - value))
        neg_entropy = self.ent_coef * tf.reduce_mean(tf.reduce_sum(policy * log_policy, axis=1))
        total_loss = pg_loss + vf_loss + neg_entropy

        # train op (clip gradient)
        optimizer = tf.train.AdamOptimizer(learning_rate=self.learning_rate)
        gradients, variables = zip(*optimizer.compute_gradients(total_loss))
        gradients, _ = tf.clip_by_global_norm(gradients, 5.0)
        self.train_op = optimizer.apply_gradients(zip(gradients, variables))

        train_op = tf.train.AdamOptimizer(learning_rate=self.learning_rate).minimize(total_loss)

        self.input_view = input_view
        self.input_feature = input_feature
        self.action = action
        self.reward = reward

        self.policy, self.value = policy, value
        self.train_op = train_op
        self.pg_loss, self.vf_loss, self.reg_loss = pg_loss, vf_loss, neg_entropy
        self.total_loss = total_loss

    def train(self):
        # calc buffer size
        n = 0
        # batch_data = sample_buffer.episodes()
        batch_data = self.replay_buffer.episodes()
        self.replay_buffer = tools.EpisodesBuffer()

        for episode in batch_data:
            n += len(episode.rewards)

        self.view_buf.resize((n,) + self.view_space)
        self.feature_buf.resize((n,) + self.feature_space)
        self.action_buf.resize(n)
        self.reward_buf.resize(n)
        view, feature = self.view_buf, self.feature_buf
        action, reward = self.action_buf, self.reward_buf

        ct = 0
        gamma = self.gamma
        # collect episodes from multiple separate buffers to a continuous buffer
        for episode in batch_data:
            v, f, a, r = episode.views, episode.features, episode.actions, episode.rewards
            m = len(episode.rewards)

            r = np.array(r)

            keep = self.sess.run(self.value, feed_dict={
                self.input_view: [v[-1]],
                self.input_feature: [f[-1]],
            })[0]

            for i in reversed(range(m)):
                keep = keep * gamma + r[i]
                r[i] = keep

            view[ct:ct + m] = v
            feature[ct:ct + m] = f
            action[ct:ct + m] = a
            reward[ct:ct + m] = r
            ct += m

        assert n == ct

        # train
        _, pg_loss, vf_loss, ent_loss, state_value = self.sess.run(
            [self.train_op, self.pg_loss, self.vf_loss, self.reg_loss, self.value], feed_dict={
                self.input_view: view,
                self.input_feature: feature,
                self.action: action,
                self.reward: reward,
            })

        print('[*] PG_LOSS:', np.round(pg_loss, 6), '/ VF_LOSS:', np.round(vf_loss, 6), '/ ENT_LOSS:', np.round(ent_loss), '/ Value:', np.mean(state_value))

    def save(self, dir_path, step=0):
        model_vars = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, self.name_scope)
        saver = tf.train.Saver(model_vars)

        file_path = os.path.join(dir_path, "ac_{}".format(step))
        saver.save(self.sess, file_path)

        print("[*] Model saved at: {}".format(file_path))

    def load(self, dir_path, step=0):
        model_vars = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, self.name_scope)
        saver = tf.train.Saver(model_vars)

        file_path = os.path.join(dir_path, "ac_{}".format(step))

        saver.restore(self.sess, file_path)
        print("[*] Loaded model from {}".format(file_path))


class MFAC:
    def __init__(self, sess, name, handle, env, value_coef=0.1, ent_coef=0.08, gamma=0.95, batch_size=64, learning_rate=1e-4):
        self.sess = sess
        self.env = env
        self.name = name

        self.view_space = env.get_view_space(handle)
        self.feature_space = env.get_feature_space(handle)
        self.num_actions = env.get_action_space(handle)[0]
        self.reward_decay = gamma

        self.batch_size = batch_size
        self.learning_rate = learning_rate

        self.value_coef = value_coef  # coefficient of value in the total loss
        self.ent_coef = ent_coef  # coefficient of entropy in the total loss

        # init training buffers
        self.view_buf = np.empty((1,) + self.view_space)
        self.feature_buf = np.empty((1,) + self.feature_space)
        self.action_buf = np.empty(1, dtype=np.int32)
        self.reward_buf = np.empty(1, dtype=np.float32)
        self.replay_buffer = tools.EpisodesBuffer(use_mean=True)

        with tf.variable_scope(name):
            self.name_scope = tf.get_variable_scope().name
            self._create_network(self.view_space, self.feature_space, )
    
    @property
    def vars(self):
        return tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope=self.name_scope)
    
    def flush_buffer(self, **kwargs):
        self.replay_buffer.push(**kwargs)

    def act(self, **kwargs):
        action = self.sess.run(self.calc_action, {
            self.input_view: kwargs['state'][0],
            self.input_feature: kwargs['state'][1]
        })
        return action.astype(np.int32).reshape((-1,))

    def _create_network(self, view_space, feature_space):
        # input
        input_view = tf.placeholder(tf.float32, (None,) + view_space)
        input_feature = tf.placeholder(tf.float32, (None,) + feature_space)
        input_act_prob = tf.placeholder(tf.float32, (None, self.num_actions))
        action = tf.placeholder(tf.int32, [None])

        reward = tf.placeholder(tf.float32, [None])

        hidden_size = [256]

        # fully connected
        flatten_view = tf.reshape(input_view, [-1, np.prod([v.value for v in input_view.shape[1:]])])
        h_view = tf.layers.dense(flatten_view, units=hidden_size[0], activation=tf.nn.relu)

        h_emb = tf.layers.dense(input_feature,  units=hidden_size[0], activation=tf.nn.relu)

        concat_layer = tf.concat([h_view, h_emb], axis=1)
        dense = tf.layers.dense(concat_layer, units=hidden_size[0] * 2, activation=tf.nn.relu)

        policy = tf.layers.dense(dense / 0.1, units=self.num_actions, activation=tf.nn.softmax)
        policy = tf.clip_by_value(policy, 1e-10, 1-1e-10)

        self.calc_action = tf.multinomial(tf.log(policy), 1)

        # for value obtain
        emb_prob = tf.layers.dense(input_act_prob, units=64, activation=tf.nn.relu)
        dense_prob = tf.layers.dense(emb_prob, units=32, activation=tf.nn.relu)
        concat_layer = tf.concat([concat_layer, dense_prob], axis=1)
        dense = tf.layers.dense(concat_layer, units=hidden_size[0], activation=tf.nn.relu)
        value = tf.layers.dense(dense, units=1)
        value = tf.reshape(value, (-1,))

        action_mask = tf.one_hot(action, self.num_actions)
        advantage = tf.stop_gradient(reward - value)

        log_policy = tf.log(policy + 1e-6)
        log_prob = tf.reduce_sum(log_policy * action_mask, axis=1)

        pg_loss = -tf.reduce_mean(advantage * log_prob)
        vf_loss = self.value_coef * tf.reduce_mean(tf.square(reward - value))
        neg_entropy = self.ent_coef * tf.reduce_mean(tf.reduce_sum(policy * log_policy, axis=1))
        total_loss = pg_loss + vf_loss + neg_entropy

        # train op (clip gradient)
        optimizer = tf.train.AdamOptimizer(learning_rate=self.learning_rate)
        gradients, variables = zip(*optimizer.compute_gradients(total_loss))
        gradients, _ = tf.clip_by_global_norm(gradients, 5.0)
        self.train_op = optimizer.apply_gradients(zip(gradients, variables))

        train_op = tf.train.AdamOptimizer(learning_rate=self.learning_rate).minimize(total_loss)

        self.input_view = input_view
        self.input_feature = input_feature
        self.input_act_prob = input_act_prob
        self.action = action
        self.reward = reward

        self.policy, self.value = policy, value
        self.train_op = train_op
        self.pg_loss, self.vf_loss, self.reg_loss = pg_loss, vf_loss, neg_entropy
        self.total_loss = total_loss

    def train(self):
        # calc buffer size
        n = 0
        # batch_data = sample_buffer.episodes()
        batch_data = self.replay_buffer.episodes()
        self.replay_buffer = tools.EpisodesBuffer(use_mean=True)

        for episode in batch_data:
            n += len(episode.rewards)

        self.view_buf.resize((n,) + self.view_space)
        self.feature_buf.resize((n,) + self.feature_space)
        self.action_buf.resize(n)
        self.reward_buf.resize(n)
        view, feature = self.view_buf, self.feature_buf
        action, reward = self.action_buf, self.reward_buf
        act_prob_buff = np.zeros((n, self.num_actions), dtype=np.float32)

        ct = 0
        gamma = self.reward_decay
        # collect episodes from multiple separate buffers to a continuous buffer
        for k, episode in enumerate(batch_data):
            v, f, a, r, prob = episode.views, episode.features, episode.actions, episode.rewards, episode.probs
            m = len(episode.rewards)

            assert len(prob) > 0 

            r = np.array(r)

            keep = self.sess.run(self.value, feed_dict={
                self.input_view: [v[-1]],
                self.input_feature: [f[-1]],
                self.input_act_prob: [prob[-1]]
            })[0]

            for i in reversed(range(m)):
                keep = keep * gamma + r[i]
                r[i] = keep

            view[ct:ct + m] = v
            feature[ct:ct + m] = f
            action[ct:ct + m] = a
            reward[ct:ct + m] = r
            act_prob_buff[ct:ct + m] = prob
            ct += m

        assert n == ct

        # train
        _, pg_loss, vf_loss, ent_loss, state_value = self.sess.run(
            [self.train_op, self.pg_loss, self.vf_loss, self.reg_loss, self.value], feed_dict={
                self.input_view: view,
                self.input_feature: feature,
                self.input_act_prob: act_prob_buff,
                self.action: action,
                self.reward: reward,
            })

        # print("sample", n, pg_loss, vf_loss, ent_loss)

        print('[*] PG_LOSS:', np.round(pg_loss, 6), '/ VF_LOSS:', np.round(vf_loss, 6), '/ ENT_LOSS:', np.round(ent_loss, 6), '/ VALUE:', np.mean(state_value))

    def save(self, dir_path, step=0):
        model_vars = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, self.name_scope)
        saver = tf.train.Saver(model_vars)

        file_path = os.path.join(dir_path, "mfac_{}".format(step))
        saver.save(self.sess, file_path)

        print("[*] Model saved at: {}".format(file_path))

    def load(self, dir_path, step=0):
        model_vars = tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, self.name_scope)
        saver = tf.train.Saver(model_vars)

        file_path = os.path.join(dir_path, "mfac_{}".format(step))

        saver.restore(self.sess, file_path)
        print("[*] Loaded model from {}".format(file_path))
