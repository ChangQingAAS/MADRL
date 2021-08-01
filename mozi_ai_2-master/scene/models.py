from django.db import models


class Scenario(models.Model):

    scenario_name = models.CharField(max_length=100, default='', verbose_name='想定名称')
    side_list = models.CharField(max_length=100, default='', verbose_name='推演方列表')
    scenario_file = models.BinaryField(editable=True, verbose_name='想定文件')
    created = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        ordering = ('created',)
        verbose_name = '想定表'
        verbose_name_plural = verbose_name
        db_table = 'scenario'


class Agent(models.Model):

    STATUS_CHOICES = (
        (1, "创建代码前"),
        (2, "编码阶段"),
        (3, "代码已提交"),
        (4, "训练中"),
        (5, "已完成"),
    )

    ALGORITHM_CHOICES = (
        (1, "PPO"),
    )

    FRAMEWORK_CHOICES = (
        (1, "torch"),
        (2, "tensorflow"),
    )

    TYPE_CHOICES = (
        (1, "强化学习智能体"),
        (2, "规则智能体"),
    )

    agent_name = models.CharField(max_length=100, default='', verbose_name='智能体名称')
    algorithm = models.SmallIntegerField(choices=ALGORITHM_CHOICES, default=1, verbose_name='算法')
    side = models.CharField(max_length=100, default='', verbose_name='推演方')
    code_file = models.BinaryField(default=b'', editable=True, verbose_name='代码文件')
    param_file = models.BinaryField(default=b'', editable=True, verbose_name='参数文件')

    type = models.SmallIntegerField(choices=TYPE_CHOICES, default=1, verbose_name='智能体类别')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    created_user = models.CharField(max_length=20, default='', verbose_name='创建人')
    framework = models.SmallIntegerField(choices=FRAMEWORK_CHOICES, default=1, verbose_name='深度学习框架')
    model = models.CharField(max_length=100, default='', verbose_name='网络模型配置')
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=0, verbose_name='状态')

    # 网络模型配置, 值类似 "{'custom_model': 'mask_model'}"
    vf_share_layers = models.BooleanField(default=True, verbose_name='价值函数共享层')
    vf_loss_coeff = models.FloatField(default=0.0, verbose_name='vf_损失系数')
    kl_coeff = models.FloatField(default=0.0, verbose_name='kl_散度系数')
    vf_clip_param = models.FloatField(default=0.0, verbose_name='vf_截断参数')
    lambda_1 = models.FloatField(default=0.0, verbose_name='lambda')
    clip_param = models.FloatField(default=0.0, verbose_name='截断系数')
    lr_min = models.FloatField(default=0.0, verbose_name='学习率下限')
    lr_max = models.FloatField(default=0.0, verbose_name='学习率上限')
    num_sgd_iter = models.IntegerField(default=0, verbose_name='随机梯度下降迭代次数')
    sgd_minibatch_size = models.IntegerField(default=0, verbose_name='随机梯度下降minibatch大小')
    rollout_fragment_length = models.IntegerField(default=0, verbose_name='rollout长度')
    train_batch_size = models.IntegerField(default=0, verbose_name='训练batch大小')
    comments = models.CharField(max_length=500, default='', verbose_name='备注')

    scenario = models.ForeignKey(Scenario, default=1, on_delete=models.CASCADE, verbose_name='想定ID')

    class Meta:
        ordering = ('created_time',)
        verbose_name = '智能体表'
        verbose_name_plural = verbose_name
        db_table = 'agent'


class Scene(models.Model):

    STATUS_CHOICES = (
        (1, "学习前"),
        (2, "学习中"),
        (3, "已完成"),
        (4, "学习异常"),
        (5, "服务中"),
    )

    scene_name = models.CharField(max_length=100, default='', verbose_name='场景名称')
    created = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    study_time = models.FloatField(default=0.0, verbose_name='学习时长')
    average_reward = models.IntegerField(default=0, verbose_name='平均奖赏值')
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=0, verbose_name='状态')

    # config
    env = models.CharField(max_length=100, default='', verbose_name='环境名称')
    # 环境类配置参数, 值类似 "{'mode': 'train'}"
    env_config = models.CharField(max_length=100, default='', verbose_name='环境类配置参数')
    num_gpus = models.IntegerField(default=1, verbose_name='GPU个数')
    num_gpus_per_worker = models.IntegerField(default=1, verbose_name='每个worker的GPU个数')

    num_workers = models.IntegerField(default=0, verbose_name='worker数量')
    current_training_iteration = models.IntegerField(default=0, verbose_name='当前训练次数')
    training_iteration = models.IntegerField(default=0, verbose_name='训练迭代次数')
    num_samples = models.IntegerField(default=0, verbose_name='实验个数')
    checkpoint_freq = models.IntegerField(default=0, verbose_name='模型参数文件保存频率')
    keep_checkpoints_num = models.IntegerField(default=0, verbose_name='保存最近的参数文件个数')
    result_storage_path = models.CharField(max_length=200, default='', verbose_name='结果文件路径')
    created_user = models.CharField(max_length=20, default='', verbose_name='创建人')
    agent = models.ForeignKey("Agent", on_delete=models.CASCADE)

    class Meta:
        ordering = ('created',)
        verbose_name = '场景表'
        verbose_name_plural = verbose_name
        db_table = 'scene'

