import sys
import os
import datetime
import argparse


def create_str_to_txt(date, str_data):
    """
    创建txt，并且写入
    """
    path_file_name = 'action_{}.txt'.format(date)
    if not os.path.exists(path_file_name):
        with open(path_file_name, "w") as f:
            print(f)

    with open(path_file_name, "a") as f:
        f.write(str_data)


parser = argparse.ArgumentParser()
parser.add_argument("--config", type=str, default="DDPPO")
parser.add_argument("--stop", type=str, default="DDPPO")
parser.add_argument("--num_samples", type=int, default=1)
parser.add_argument("--checkpoint_freq", type=int, default=1)
parser.add_argument("--keep_checkpoints_num", type=int, default=1)

args = parser.parse_args()

print('config:')
print(eval(args.config.replace('$$', ' ')))
print('stop:')
print(eval(args.stop.replace('$$', ' ')))
print('num_samples:')
print(args.num_samples)
print('checkpoint_freq:')
print(args.checkpoint_freq)
print('keep_checkpoints_num:')
print(args.keep_checkpoints_num)

create_str_to_txt(datetime.datetime.now().strftime('%Y-%m-%d'), args.config)
create_str_to_txt(datetime.datetime.now().strftime('%Y-%m-%d'), args.stop)
create_str_to_txt(datetime.datetime.now().strftime('%Y-%m-%d'), str(args.num_samples))
create_str_to_txt(datetime.datetime.now().strftime('%Y-%m-%d'), str(args.checkpoint_freq))
create_str_to_txt(datetime.datetime.now().strftime('%Y-%m-%d'), str(args.keep_checkpoints_num))


raise ValueError("a 必须是数字")
