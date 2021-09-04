import matplotlib.pyplot as plt
import numpy as np
import etc
import os
import collections
import cv2

import file_utils as pyfile

def read_reward_file():
    # 读取奖励文档
    epochs_list = []
    reward_list = []
    f = open("%s/final_reward.txt" % etc.OUTPUT_PATH)
    con = f.read()
    f.close()
    con_lt = con.split("\n")
    for i in range(len(con_lt) - 1):
        lt = con_lt[i].split(',')
        epochs_list.append(int(lt[0]))
        reward_list.append(float(lt[1]))
    return epochs_list, reward_list

def write_loss(step, loss_value, loss_name="loss_critic"):
    """
    保存损失
    :param step: 步
    :param loss_value:损失的值
    :param loss_name:创建损失的文档名
    :return:
    """
    pyfile.create_dir(etc.OUTPUT_PATH)
    file_path = "%s/%s.txt" % (etc.OUTPUT_PATH, loss_name)
    if not os.path.exists(file_path):
        f = open(file_path, "w")
    else:
        f = open(file_path, "a")

    f.write("%s,%s\n" % (step, loss_value))
    f.close()

def read_loss_file(file_name=""):
    # 读取损失文档
    epochs_list = []
    reward_list = []
    f = open(file_name)
    con = f.read()
    f.close()
    con_lt = con.split("\n")
    for i in range(len(con_lt) - 1):
        lt = con_lt[i].split(',')
        epochs_list.append(int(lt[0]))
        reward_list.append(float(lt[1]))
    return epochs_list, reward_list


def show_reward_pic():
    # 画出奖赏值的变化图
    epoch_list, reward_list = read_reward_file()
    reward_sum = 0.0
    for i in range(len(reward_list)):
        reward_sum += reward_list[i]

    reward_mean = reward_sum / len(reward_list)
    e = np.asarray(epoch_list)
    r = np.asarray(reward_list)
    plt.figure()
    plt.plot(e, r)
    plt.xlabel('Epochs')
    plt.ylabel('Reward')
    plt.show()
    plt.close()


def show_loss_pic(loss_name="q_next"):
    # 画出损失值的变化图
    file_name = "%s/%s.txt" % (etc.OUTPUT_PATH, loss_name)
    step_list, loss_list = read_loss_file(file_name)
    e = np.asarray(step_list)
    r = np.asarray(loss_list)
    plt.figure()
    plt.plot(e, r)
    plt.xlabel('steps')
    plt.ylabel(loss_name)
    # 使用plt.show(),然后使用plt.close()并不会关闭图，
    # plt.show()
    plt.draw()
    plt.pause(20)
    plt.close()


def show_pic():
    # 画图
    if etc.SHOW_FIGURE:
        # show_reward_pic()
        show_loss_pic("q_next")


def plot_learning_curve(x, scores, epsilons, filename, lines=None):
    fig=plt.figure()
    ax=fig.add_subplot(111, label="1")
    ax2=fig.add_subplot(111, label="2", frame_on=False)

    ax.plot(x, epsilons, color="C0")
    ax.set_xlabel("Training Steps", color="C0")
    ax.set_ylabel("Epsilon", color="C0")
    ax.tick_params(axis='x', colors="C0")
    ax.tick_params(axis='y', colors="C0")

    N = len(scores)
    running_avg = np.empty(N)
    for t in range(N):
	    running_avg[t] = np.mean(scores[max(0, t-20):(t+1)])

    ax2.scatter(x, running_avg, color="C1")
    ax2.axes.get_xaxis().set_visible(False)
    ax2.yaxis.tick_right()
    ax2.set_ylabel('Score', color="C1")
    ax2.yaxis.set_label_position('right')
    ax2.tick_params(axis='y', colors="C1")

    if lines is not None:
        for line in lines:
            plt.axvline(x=line)

    plt.savefig(filename)
