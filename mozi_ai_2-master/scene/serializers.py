from rest_framework import serializers
from scene.models import Scene, Scenario, Agent


class ScenarioSerializer(serializers.ModelSerializer):

    class Meta:
        model = Scenario
        fields = ('id', 'scenario_name', 'side_list', 'scenario_file')


class ScenarioSerializerO(serializers.ModelSerializer):

    class Meta:
        model = Scenario
        fields = ('id', 'scenario_name', 'side_list')


class AgentSerializerO(serializers.ModelSerializer):
    scenario = ScenarioSerializerO(many=False, read_only=True)

    class Meta:
        model = Agent
        fields = ('id', 'agent_name', 'algorithm', 'scenario', 'side', 'type', 'comments', 'status',
                  'created_time', 'created_user', 'framework', 'model', 'vf_share_layers', 'vf_loss_coeff',
                  'kl_coeff', 'vf_clip_param', 'lambda_1', 'clip_param', 'lr_min', 'lr_max', 'num_sgd_iter',
                  'sgd_minibatch_size', 'rollout_fragment_length', 'train_batch_size')


class AgentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Agent
        fields = '__all__'


# 返回下拉框中的display name
class AgentSerializerDisplay(serializers.ModelSerializer):
    scenario = ScenarioSerializerO(many=False, read_only=True)

    # 显示下拉框中的值
    algorithm = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    framework = serializers.SerializerMethodField()

    # created_time = serializers.DateTimeField(fromat='%Y年%m月%d日%H时%M分', required=False, read_only=True)

    # 显示下拉框中的值
    def get_status(self, obj):
        return obj.get_status_display()

    def get_algorithm(self, obj):
        return obj.get_algorithm_display()

    def get_type(self, obj):
        return obj.get_type_display()

    def get_framework(self, obj):
        return obj.get_framework_display()

    class Meta:
        model = Agent
        fields = ('id', 'agent_name', 'algorithm', 'scenario', 'side', 'type', 'comments', 'status',
                  'created_time', 'created_user', 'framework', 'model', 'vf_share_layers', 'vf_loss_coeff',
                  'kl_coeff', 'vf_clip_param', 'lambda_1', 'clip_param', 'lr_min', 'lr_max', 'num_sgd_iter',
                  'sgd_minibatch_size', 'rollout_fragment_length', 'train_batch_size')


class SceneSerializerO(serializers.ModelSerializer):

    # 显示下拉框中的值
    # status = serializers.SerializerMethodField()

    agent = AgentSerializerO(many=False, read_only=True)

    class Meta:
        model = Scene
        fields = ('id', 'scene_name', 'created', 'study_time', 'average_reward', 'status',
                  'env', 'env_config', 'num_gpus', 'num_gpus_per_worker',
                  'current_training_iteration',
                  'num_workers', 'training_iteration', 'num_samples', 'checkpoint_freq', 'keep_checkpoints_num',
                  'result_storage_path', 'created_user', 'agent')

    # 显示下拉框中的值
    # def get_status(self, obj):
    #     return obj.get_status_display()


class SceneSerializer(serializers.ModelSerializer):

    class Meta:
        model = Scene
        fields = ('id', 'scene_name', 'created', 'study_time', 'average_reward', 'status',
                  'env', 'env_config', 'num_gpus', 'num_gpus_per_worker',
                  'current_training_iteration',
                  'num_workers', 'training_iteration', 'num_samples', 'checkpoint_freq', 'keep_checkpoints_num',
                  'result_storage_path', 'created_user', 'agent')


class SceneSerializerDisplay(serializers.ModelSerializer):
    agent = AgentSerializerDisplay(many=False, read_only=True)

    status = serializers.SerializerMethodField()

    # 显示下拉框中的值
    def get_status(self, obj):
        return obj.get_status_display()

    class Meta:
        model = Scene
        fields = ('id', 'scene_name', 'created', 'study_time', 'average_reward', 'status',
                  'env', 'env_config', 'num_gpus', 'num_gpus_per_worker',
                  'current_training_iteration',
                  'num_workers', 'training_iteration', 'num_samples', 'checkpoint_freq', 'keep_checkpoints_num',
                  'result_storage_path', 'created_user', 'agent')



