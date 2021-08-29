import numpy as np
import scipy as sp
from scipy import sparse
from scipy.spatial import cKDTree
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from sklearn.preprocessing import MinMaxScaler

L = 32.0  # 平面大小
rho = 3.0  # 密度？
# number of particles (rho per unit of the box)
N = int(rho * L**2)  # 粒子数目
print("N", N)

r0 = 1.0  # radius of influence
v0 = 1.0  # 假设所有速度都一样
iterations = 10000  # number of steps
eta = 0.2  # noise 0.5 or 0.1

# initialize positions and orientations
# (N,2)
pos = np.random.uniform(0, L, size=(N, 2))  # 位置（还没分配
# (N)
orient = np.random.uniform(-np.pi, np.pi, size=N)  # 角度

fig, ax = plt.subplots(figsize=(6, 6))

# 画箭袋 qv = (x,y,cos(),sin(), thet)
qv = ax.quiver(pos[:, 0],
               pos[:, 1],
               np.cos(orient),
               np.sin(orient),
               orient,
               clim=[-np.pi, np.pi])


def animate(i):
    # 计算
    #  print(i)
    global orient
    tree = cKDTree(pos, boxsize=[L, L])
    # dist.col 和 dist.row 包含非零数据的索引
    # (N, N)
    dist = tree.sparse_distance_matrix(tree,
                                       max_distance=r0,
                                       output_type='coo_matrix')
    #  we evaluate a quantity for every column j
    #  (#  of non-zero values,)
    data = np.exp(orient[dist.col] * 1j)
    #  construct  a new sparse marix with entries in the same places ij of the dist matrix
    # (N, N)
    neigh = sparse.coo_matrix((data, (dist.row, dist.col)),
                              shape=dist.get_shape())
    #  and sum along the columns (sum over j)
    # (N,)
    # 邻居的速度方向
    S = np.squeeze(np.asarray(neigh.tocsr().sum(axis=1)))

    # 更新角度，邻居平均角度 + 扰动角度
    orient = np.angle(S) + eta * np.random.uniform(-np.pi, np.pi, size=N)

    #  scaled_orient=np.interp(orient, (orient.min(), orient.max()), (0, +1))
    #  #  print(abs(sum(scaled_orient)/(N)))
    #  order=np.var(orient)
    #  print(abs(order-7.33438)/7.33438)

    #  if i==499:
    #      return

    # 计算后更新
    cos, sin = np.cos(orient), np.sin(orient)
    pos[:, 0] += cos * v0
    pos[:, 1] += sin * v0

    pos[pos > L] -= L
    pos[pos < 0] += L

    qv.set_offsets(pos)
    qv.set_UVC(cos, sin, orient)
    return qv,


# 制作动图
"""
函数FuncAnimation(fig,func,frames,init_func,interval,blit)是绘制动图的主要函数，其参数如下：
　　a.fig 绘制动图的画布名称
　　b.func自定义动画函数，即下边程序定义的函数update
　　c.frames动画长度，一次循环包含的帧数，在函数运行时，其值会传递给函数update(n)的形参“n”
　　d.init_func自定义开始帧，即传入刚定义的函数init,初始化函数
　　e.interval更新频率，以ms计
　　f.blit选择更新所有点，还是仅更新产生变化的点。应选择True，但mac用户请选择False，否则无法显
"""
FuncAnimation(fig, animate, np.arange(0, 500), interval=1, blit=True)
plt.show()
