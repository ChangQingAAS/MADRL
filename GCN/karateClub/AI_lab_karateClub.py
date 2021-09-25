###############################################################################
# Step 0: Problem description
# ---------------------------
#
# We start with the well-known "Zachary's karate club" problem. The karate club
# is a social network which captures 34 members and document pairwise links
# between members who interact outside the club.  The club later divides into
# two communities led by the instructor (node 0) and the club president (node
# 33). The network is visualized as follows with the color indicating the
# community:
#
# .. image:: https://s3.us-east-2.amazonaws.com/dgl.ai/tutorial/img/karate-club.png
#    :align: center
#
# The task is to predict which side (0 or 33) each member tends to join given
# the social network itself.
###############################################################################

###############################################################################
# Import libraries
###############################################################################

import dgl
import networkx as nx
import torch
import torch.nn as nn
import torch.nn.functional as F
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import pdb

###############################################################################
# Step 1: Creating a graph in DGL
# -------------------------------
# Creating the graph for Zachary's karate club goes as follows:
###############################################################################

###############################################################################
# Load graph
###############################################################################


def build_karate_club_graph():
    g = dgl.DGLGraph()
    # add 34 nodes into the graph; nodes are labeled from 0~33
    g.add_nodes(34)
    # all 78 edges as a list of tuples
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
    # add edges two lists of nodes: src and dst
    src, dst = tuple(zip(*edge_list))
    g.add_edges(src, dst)
    # edges are directional in DGL; make them bi-directional
    g.add_edges(dst, src)

    return g


###############################################################################
# We can print out the number of nodes and edges in our newly constructed graph:
###############################################################################
G = build_karate_club_graph()
print('We have %d nodes.' % G.number_of_nodes())
print('We have %d edges.' % G.number_of_edges())

i_num_nodes = G.number_of_nodes()
i_num_edges = G.number_of_edges()

###############################################################################
# Model parameters
###############################################################################
i_num_epochs = 50
i_num_neurons_layer_1 = 5
i_num_neurons_layer_2 = 2

###############################################################################
# We can also visualize the graph by converting it to a `networkx
# <https://networkx.github.io/documentation/stable/>`_ graph:
# Since the actual graph is undirected, we convert it for visualization
# purpose.
nx_G = G.to_networkx().to_undirected()
# Kamada-Kawaii layout usually looks pretty for arbitrary graphs
pos = nx.kamada_kawai_layout(nx_G)
nx.draw(nx_G, pos, with_labels=True, node_color=[[.7, .7, .7]])

###############################################################################
# Step 2: assign features to nodes or edges
# --------------------------------------------
# Graph neural networks associate features with nodes and edges for training.
# For our classification example, we assign each node's an input feature as a one-hot vector:
# node :math:`v_i`'s feature vector is :math:`[0,\ldots,1,\dots,0]`,
# where the :math:`i^{th}` position is one.
#
# In DGL, we can add features for all nodes at once, using a feature tensor that
# batches node features along the first dimension. This code below adds the one-hot
# feature for all nodes:
###############################################################################
G.ndata['feat'] = torch.eye(i_num_nodes)

###############################################################################
# We can print out the node features to verify:
###############################################################################
# print out node 2's input feature
print(G.nodes[2].data['feat'])

# print out node 10 and 11's input features
print(G.nodes[[10, 11]].data['feat'])

###############################################################################
# Step 3: define a Graph Convolutional Network (GCN)
# --------------------------------------------------
# To perform node classification, we use the Graph Convolutional Network
# (GCN) developed by `Kipf and Welling <https://arxiv.org/abs/1609.02907>`_. Here
# we provide the simplest definition of a GCN framework, but we recommend the
# reader to read the original paper for more details.
#
# - At layer :math:`l`, each node :math:`v_i^l` carries a feature vector :math:`h_i^l`.
# - Each layer of the GCN tries to aggregate the features from :math:`u_i^{l}` where
#   :math:`u_i`'s are neighborhood nodes to :math:`v` into the next layer representation at
#   :math:`v_i^{l+1}`. This is followed by an affine transformation with some
#   non-linearity.
#
# The above definition of GCN fits into a **message-passing** paradigm: each
# node will update its own feature with information sent from neighboring
# nodes. A graphical demonstration is displayed below.
#
# .. image:: https://s3.us-east-2.amazonaws.com/dgl.ai/tutorial/1_first/mailbox.png
#    :alt: mailbox
#    :align: center
#
# Now, we show that the GCN layer can be easily implemented in DGL.
###############################################################################


# Define the message & reduce function
# NOTE: we ignore the GCN's normalization constant c_ij for this tutorial.
def gcn_message(edges):
    # The argument is a batch of edges.
    # This computes a (batch of) message called 'msg' using the source node's feature 'h'.
    return {'msg': edges.src['h']}


def gcn_reduce(nodes):
    # The argument is a batch of nodes.
    # This computes the new 'h' features by summing received 'msg' in each node's mailbox.
    return {'h': torch.sum(nodes.mailbox['msg'], dim=1)}


# Define the GCNLayer module
class GCNLayer(nn.Module):
    def __init__(self, in_feats, out_feats):
        super(GCNLayer, self).__init__()
        self.linear = nn.Linear(in_feats, out_feats)

    def forward(self, g, inputs):
        # g is the graph and the inputs is the input node features
        # first set the node features
        g.ndata['h'] = inputs
        # trigger message passing on all edges
        # g.send(g.edges(), gcn_message)
        # trigger aggregation at all nodes
        # g.recv(g.nodes(), gcn_reduce)
        g.send_and_recv(g.edges(), gcn_message, gcn_reduce)

        # get the result node features
        h = g.ndata.pop('h')
        # perform linear transformation
        return self.linear(h)


###############################################################################
# In general, the nodes send information computed via the *message functions*,
# and aggregates incoming information with the *reduce functions*.
#
# We then define a deeper GCN model that contains two GCN layers:
###############################################################################


# Define a 2-layer GCN model
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


# The first layer transforms input features of size of 34 to a hidden size of 5.
# The second layer transforms the hidden layer and produces output features of
# size 2, corresponding to the two groups of the karate club.
net = GCN(i_num_nodes, i_num_neurons_layer_1, i_num_neurons_layer_2)

###############################################################################
# Step 4: data preparation and initialization
# -------------------------------------------
#
# We use one-hot vectors to initialize the node features. Since this is a
# semi-supervised setting, only the instructor (node 0) and the club president
# (node 33) are assigned labels. The implementation is available as follow.
###############################################################################
inputs = torch.eye(i_num_nodes)
labeled_nodes = torch.tensor(
    [0, 33])  # only the instructor and the president nodes are labeled
labels = torch.tensor([0, 1])  # their labels are different

###############################################################################
# Step 5: train then visualize
# ----------------------------
# The training loop is exactly the same as other PyTorch models.
# (1) create an optimizer,
# (2) feed the inputs to the model,
# (3) calculate the loss, and
# (4) use autograd to optimize the model.
###############################################################################

optimizer = torch.optim.Adam(net.parameters(), lr=0.01)
all_logits = []

for epoch in range(i_num_epochs):
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

###############################################################################
# This is a rather toy example, so it does not even have a validation or test
# set. Instead, Since the model produces an output feature of size 2 for each node, we can
# visualize by plotting the output feature in a 2D space.
# The following code animates the training process from initial guess
# (where the nodes are not classified correctly at all) to the end
# (where the nodes are linearly separable).
###############################################################################


def draw(i):
    cls1color = '#00FFFF'
    cls2color = '#FF00FF'
    pos = {}
    colors = []
    for v in range(34):
        pos[v] = all_logits[i][v].numpy()
        cls = pos[v].argmax()
        colors.append(cls1color if cls else cls2color)
    ax.cla()
    ax.axis('off')
    ax.set_title('Epoch: %d' % i)
    nx.draw_networkx(nx_G.to_undirected(),
                     pos,
                     node_color=colors,
                     with_labels=True,
                     node_size=300,
                     ax=ax)


fig = plt.figure(dpi=150)
fig.clf()
ax = fig.subplots()
draw(0)  # draw the prediction of the first epoch
plt.show()
plt.savefig('graph_deep_learning_karateclub.png')
plt.close()

###############################################################################
# .. image:: https://s3.us-east-2.amazonaws.com/dgl.ai/tutorial/1_first/karate0.png
#    :height: 300px
#    :width: 400px
#    :align: center

###############################################################################
# The following animation shows how the model correctly predicts the community
# after a series of training epochs.
###############################################################################
fig = plt.figure(dpi=150)
fig.clf()
ax = fig.subplots()
draw(0)  # draw the prediction of the first epoch
ani = animation.FuncAnimation(fig, draw, frames=len(all_logits), interval=200)
plt.show()
# plt.savefig('graph_deep_learning_karateclub.png')
plt.close()
###############################################################################
# .. image:: https://s3.us-east-2.amazonaws.com/dgl.ai/tutorial/1_first/karate.gif
#    :height: 300px
#    :width: 400px
#    :align: center
###############################################################################

###############################################################################
# Next steps
# ----------
#
# In the :doc:`next tutorial <2_basics>`, we will go through some more basics
# of DGL, such as reading and writing node/edge features.
###############################################################################

exit()

#####################################################################################
# Print summary of a model and inspect model
#####################################################################################
print("\n ********** Model Summary Section ********** \n")
print("Printing model summary and model details: \n")
print(model.summary())
#keras.utils.print_summary(model, line_length=None, positions=None, print_fn=None)
print(model.output_shape)
print(model.input_shape)
#print(model.get_config())
#print(model.get_weights())

#####################################################################################
# Plot model
#####################################################################################
#plot_model(model, to_file='model.png')
keras.utils.plot_model(model,
                       to_file='graph_lstm_imdb_model_thymus.png',
                       show_shapes=True,
                       show_layer_names=True,
                       rankdir='TB')

print("\n ********** Model Parameters ********** \n")
#print("\nLearning rate: ", f_learning_rate)
#print("Learning rate decay: ", f_learning_rate_decay)
print("\n Optimizer:", str_optimizer)
#print("Momentum: ", f_momentum)
print("Fitting epochs: ", i_num_epochs)
print("Batch size: ", i_batch_size)
print("Validation split of training set: ", f_validation_split)
print("Dropout probability: ", f_dropout)
print("Number of neurons in first hidden layer: ", i_num_neurons_layer_1)
print("Number of neurons in second hidden layer: ", i_num_neurons_layer_2)
print("Activation function for first hidden layer: ", str_activation_layer1)
print("Activation function for first hidden layer: ", str_activation_layer2)
#print("Kernel initialization: ", "Orthogonal") # k_kernel_initializer   = keras.initializers.Orthogonal(gain=1.0, seed=None)
#print("Kernel regularization: ", "L1")         # k_kernel_regularizer   = keras.regularizers.l1(0.01)
#print("Kernel activity initialization: ", "L1") # k_activity_regularizer = keras.regularizers.l1(0.01)
print("**************************************")

#####################################################################################
# Save model
#####################################################################################
print("\n ********** Model Save Section ********** \n")
print("       Saving model ......  \n")
str_model_save_filename = "model_file_imdb_lstm.h5"
model.save(str_model_save_filename)
#model_saved = load_model(str_model_save_filename)

print("\n ***************************************** \n")
print("   All tasks successfully completed \n")
print(" ***************************************** \n")
