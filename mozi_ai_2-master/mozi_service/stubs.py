from mozi_service import commands
import sh
from pathlib import Path
from tools import read_config
# from mozi_ai_sdk.test.hxfb.bin.tune_ddppo_hxfb import start_tune

BASE_DIR = Path(__file__).resolve().parent.parent


def start_train(content):

    config = {
        'env_config': content['env_config'],
        'num_gpus': content['num_gpus'],
        'num_gpus_per_worker': content['num_gpus_per_worker'],
        'framework': content['framework'],
        'model': content['model'],
        'vf_share_layers': content['vf_share_layers'],
        'vf_loss_coeff': content['vf_loss_coeff'],
        'kl_coeff': content['kl_coeff'],
        'lambda': content['lambda_1'],
        'clip_param': content['clip_param'],
        'num_sgd_iter': content['num_sgd_iter'],
        'sgd_minibatch_size': content['sgd_minibatch_size'],
        'rollout_fragment_length': content['rollout_fragment_length'],
        'train_batch_size': content['train_batch_size'],
        'num_workers': content['num_workers']
    }

    stop = {'training_iteration': content['training_iteration']}

    num_samples = content['num_samples']

    checkpoint_freq = content['checkpoint_freq']

    keep_checkpoints_num = content['keep_checkpoints_num']

    str_args = '--config "' + str(config).replace(' ', '$$').replace('"', '\\"') + '"'
    str_args += ' --stop "' + str(stop).replace(' ', '$$') + '"'
    str_args += ' --num_samples ' + str(num_samples)
    str_args += ' --checkpoint_freq ' + str(checkpoint_freq)
    str_args += ' --keep_checkpoints_num ' + str(keep_checkpoints_num)
    print('----------------------------------------------------------')
    print(str_args)

    password = read_config.password
    _sudo = sh.sudo.bake("-S", _in=password)
    sh.cd(str(BASE_DIR).replace('\\', '/') + '/mozi_service')
    _sudo.sh("start3.sh", str_args)

    return True


# result=dir,config={a1 : 1, a2 : 2
def restart_tune(result_dir, kwargs):
    pass


def evaluate(result_dir, kwargs):
    pass


def result_dis(result_dir):
    result_url = commands.Create_Tensorboad()
    return result_url
