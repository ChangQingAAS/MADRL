import dgl
import networkx as nx
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import torch
import torch.nn as nn
import torch.nn.functional as F


###################
# Step 1:建立图
###################
def build_karate_club_graph():
    g = dgl.DGLGraph()
    # 在图中添加34个节点，节点标记为0-33
    g.add_nodes(34)
    # 所有78条边作为一个元组列表
    edge_list = [(1, 0), (2, 0), (2, 1), (3, 0), (3, 1), (3, 2), (4, 0),
                 (5, 0), (6, 0), (6, 4), (6, 5), (7, 0), (7, 1), (7, 2),
                 (7, 3), (8, 0), (8, 2), (9, 2), (10, 0), (10, 4), (10, 5),
                 (11, 0), (12, 0), (12, 3), (13, 0), (13, 1), (13, 2), (13, 3),
                 (16, 5), (16, 6), (17, 0), (17, 1), (19, 0), (19, 1), (21, 0),
                 (21, 1), (25, 23), (25, 24), (27, 2), (27, 23), (27, 24),
                 (28, 2), (29, 23), (29, 26), (30, 1), (30, 8), (31, 0),
                 (31, 24), (31, 25), (31, 28), (32, 2), (32, 8), (32, 14),
                 (32, 15), (32, 18), (32, 20), (32, 22), (32, 23), (32, 29),
                 (32, 30), (32, 31), (33, 8), (33, 9), (33, 13), (33, 14),
                 (33, 15), (33, 18), (33, 19), (33, 20), (33, 22), (33, 23),
                 (33, 26), (33, 27), (33, 28), (33, 29), (33, 30), (33, 31),
                 (33, 32)]
    # 将边添加到两个节点列表中: src and dst
    src, dst = tuple(zip(*edge_list))
    g.add_edges(src, dst)
    # DGL中的边是有方向的，令其为双向
    g.add_edges(dst, src)

    return g


# 输出创建的节点和边的数量
G = build_karate_club_graph()
print('We have %d nodes.' % G.number_of_nodes())
print('We have %d edges.' % G.number_of_edges())

num_nodes = G.number_of_nodes()
num_edges = G.number_of_edges()

# 利用networkx绘制此网络
fig = plt.figure(dpi=150)
nx_G = G.to_networkx().to_undirected()
# Kamada-Kawaii layout usually looks pretty for arbitrary graphs
pos = nx.kamada_kawai_layout(nx_G)
nx.draw(nx_G, pos, with_labels=True, node_color=[[.5, .8, .7]])
plt.savefig('AI_lab/karateClub.png')
# plt.show()

#############################
# Step2: 给边和节点赋予特征
#############################

# 联合边和节点信息做图训练。
# 对于整个节点分类的例子，将每个节点的特征转化成one-hot向量：
# 节点变为[0,…,1,…,0][0,…,1,…,0],对应的位置上的数值为1。
# 在DGL里面，可以使用一个feature张量在第一维上一次性给所有的节点添加特征，代码如下
G.ndata['feat'] = torch.eye(num_nodes)

#############################
# Step3: 定义一个GCN
#############################

# 在第k层，每个节点用一个节点向量表示；
# GCN中每个节点会接受邻居节点的信息从而更新自身的节点表示。


# 定义message方法和reduce方法
# NOTE: 为了易于理解，整个教程忽略了归一化的步骤
# 节点通过message方法传播计算后的节点特征，reduce方法负责将收集到的节点特征进行聚合。
def gcn_message(edges):
    # 参数：batch of edges
    # 得到计算后的batch of edges的信息，这里直接返回边的源节点的feature
    return {'msg': edges.src['h']}


def gcn_reduce(nodes):
    # 参数：batch of nodes.
    # 得到计算后batch of nodes的信息，这里返回每个节点mailbox里的msg的和
    return {'h': torch.sum(nodes.mailbox['msg'], dim=1)}


# 节点通过message方法传播计算后的节点特征，reduce方法负责将收集到的节点特征进行聚合。
class GCNLayer(nn.Module):
    def __init__(self, in_feats, out_feats):
        super(GCNLayer, self).__init__()
        self.linear = nn.Linear(in_feats, out_feats)

    def forward(self, g, inputs):
        # g为图对象； inputs为节点特征矩阵

        # ····················补全此处代码················
        # 设置图的节点特征
        g.ndata['h'] = inputs
        # 触发边的信息传递 触发节点的聚合函数
        g.send_and_recv(g.edges(), gcn_message, gcn_reduce)
        # 取得节点向量
        h = g.ndata.pop('h')
        # 线性变换
        return self.linear(h)
        # ····················补全此处代码················


# 下面定义一个更深的GCN模型，包含两层GCN层：
class GCN(nn.Module):
    def __init__(self, in_feats, hidden_size, num_classes):
        super(GCN, self).__init__()
        self.gcn1 = GCNLayer(in_feats, hidden_size)
        self.gcn2 = GCNLayer(hidden_size, num_classes)

    def forward(self, g, inputs):
        h = self.gcn1(g, inputs)
        h = torch.relu(h)
        h = self.gcn2(g, h)
        return h


#############################
# Step4: 数据准备和初始化
#############################
num_epochs = 50
num_neurons_layer_1 = 8
num_neurons_layer_2 = 2
# 以空手道俱乐部为例
# 第一层将34层的输入转化为隐层为8
# 第二层将隐层转化为最终的分类数2
# 将整个网络节点分为2类，[0, 33]，二者对应的标签为[0, 1]
net = GCN(num_nodes, num_neurons_layer_1, num_neurons_layer_2)
inputs = torch.eye(num_nodes)
labeled_nodes = torch.tensor(
    [0, 33])  # only the instructor and the president nodes are labeled
labels = torch.tensor([0, 1])  # their labels are different

nx_G = G.to_networkx().to_undirected()
# Kamada-Kawaii layout usually looks pretty for arbitrary graphs
pos = nx.kamada_kawai_layout(nx_G)

#############################
# Step5: 训练和可视化
#############################

# The training loop is exactly the same as other PyTorch models.
# （1）创建优化器，
# （2）输入input数据，
# （3）计算loss，
# （4）使用反向传播优化模型
optimizer = torch.optim.Adam(net.parameters(), lr=0.01)
all_logits = []

for epoch in range(num_epochs):
    logits = net(G, inputs)
    # we save the logits for visualization later
    all_logits.append(logits.detach())
    logp = F.log_softmax(logits, 1)
    # we only compute loss for labeled nodes
    loss = F.nll_loss(logp[labeled_nodes], labels)

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    print('Epoch %d | Loss: %.4f' % (epoch, loss.item()))

#############################
# Step6:动态展示训练过程
#############################


# 这是一个非常简单的小例子，甚至没有划分验证集和测试集。
# 因此，因为模型最后输出了每个节点的二维向量，可以很容易地在2D的空间将这个过程可视化出来
# 下面的代码动态的展示了训练过程中从开始的状态到到最后所有节点都线性可分的过程。
def draw(i):

    # plt.clf()  # 此时不能调用此函数，不然之前的点将被清空。
    # color = ['green', 'b', 'r', '#7FFFD4', '#FFC0CB', '#00022e', '#F0F8FF']
    cls1color = '#00FFFF'
    cls2color = '#FF00FF'
    pos = {}
    colors = []
    for v in range(num_nodes):
        pos[v] = all_logits[i][v].numpy()
        cls = pos[v].argmax()
        # colors.append(color[cls])
        colors.append(cls1color if cls else cls2color)
    ax.cla()
    ax.axis('off')
    ax.set_title('Epoch: %d' % i)

    nx.draw_networkx(nx_G.to_undirected(),
                     pos,
                     node_color=colors,
                     with_labels=True,
                     node_size=200,
                     ax=ax)


# 下面的动态过程展示了模型经过一段训练之后能够准确预测节点属于哪个群组。
fig = plt.figure(dpi=150)
fig.clf()
ax = fig.subplots()
draw(0)  # draw the prediction of the first epoch
ani = animation.FuncAnimation(fig, draw, frames=len(all_logits), interval=200)
plt.pause(100)
plt.savefig('AI_lab/graph_deep_learning_karateclub.png')
plt.close()
