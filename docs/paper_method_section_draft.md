# 论文方法部分初稿：EA-RG-MAPPO-S

日期：2026-07-13

## 1. 方法总览

本文提出一种面向有限通信无人机协同追逃任务的边特征增强角色图多智能体强化学习方法，记为：

```text
EA-RG-MAPPO-S
```

其中：

```text
EA = Edge-Aware
RG = Role Graph
MAPPO = Multi-Agent PPO
S = Staged random-radius fine-tuning
```

方法核心思想是：在 MAPPO 的集中训练、分散执行框架下，将无人机和目标建模为带角色标记的动态图节点，并在图注意力中显式引入相对距离、相对方位、相对速度和通信可达性等边特征，使策略能够在有限通信条件下进行更稳定的信息聚合和协同决策。

与普通 GAT-MAPPO 相比，EA-RG-MAPPO-S 的区别不只是加入图注意力，而是：

```text
1. 节点具有角色语义：追击无人机节点和目标节点使用不同 role embedding。
2. 边具有物理语义：相对位置、距离、方位、速度和通信可达性进入 attention score。
3. 训练具有通信鲁棒性：先固定半径学习基础策略，再用随机通信半径短程微调。
```

目标意图分支在当前版本中保留为辅助模块，但不作为主要贡献。现有诊断表明，该分支的 balanced accuracy 仍不足，因此论文主线应聚焦边特征角色图和有限通信鲁棒性。

## 2. 问题建模

考虑由 \(N\) 架追击无人机和 \(M\) 个机动目标组成的协同追逃任务。每架无人机在离散时间步 \(t\) 根据局部观测选择动作：

```text
a_i^t ~ pi_theta(a_i^t | o_i^t, G_i^t)
```

其中：

```text
o_i^t: 第 i 架无人机的局部观测；
G_i^t: 在有限通信条件下可获得的图结构信息；
a_i^t: 离散机动动作，包括转向和加减速组合。
```

训练阶段使用集中式 critic：

```text
V_phi(s^t)
```

其中 \(s^t\) 为全局状态。执行阶段每架无人机仅依赖自身局部观测和通信半径内的图信息。

任务目标是最大化团队累积回报，同时降低无人机间碰撞和任务超时：

```text
max E[ sum_t gamma^t r^t ]
```

其中回报包含目标接近奖励、朝向奖励、成功拦截奖励、碰撞惩罚和超时相关惩罚。

## 3. 有限通信角色图构建

在每个时间步，将任务场景构建为动态图：

```text
G^t = (V^t, E^t)
```

节点集合包含：

```text
V^t = V_uav^t union V_target^t
```

其中追击无人机节点数为 \(N\)，目标节点数为 \(M\)。本文当前实验设置为：

```text
N = 3
M = 1
```

每个节点包含运动状态和角色信息。无人机节点特征包括归一化位置、航向、速度、剩余能量、最大速度和感知范围；目标节点特征包括归一化位置、航向和速度。

角色标记用于区分节点语义：

```text
role = 0: UAV
role = 1: target
```

角色 embedding 与节点运动特征拼接后输入图编码器：

```text
h_i^0 = f_in([x_i, emb(role_i)])
```

有限通信通过通信半径 \(R_c\) 定义。如果两个无人机节点距离超过 \(R_c\)，则对应通信边不可用。目标节点作为任务相关节点保留在图中，用于让策略形成目标导向的信息聚合。

## 4. 相对边特征

普通图注意力通常只依赖节点特征计算注意力权重，这会忽略无人机协同中非常关键的几何关系。本文为每条边构造相对边特征：

```text
e_ij = [
    relative_position_x,
    relative_position_y,
    distance / world_size,
    distance / communication_radius,
    cos(bearing),
    sin(bearing),
    relative_velocity_x,
    relative_velocity_y,
    communication_reachable,
    target_node_flag
]
```

这些特征分别描述：

```text
1. 节点间相对空间位置；
2. 节点间距离及其相对通信半径大小；
3. 相对方位；
4. 相对运动趋势；
5. 边是否在通信半径内；
6. 被关注节点是否为目标。
```

边特征的作用是让注意力机制不仅知道“有哪些节点”，还知道“这些节点之间处于怎样的几何和通信关系”。

## 5. 边特征增强图注意力

对节点 \(i\) 到节点 \(j\) 的注意力得分定义为：

```text
score_ij = LeakyReLU( a^T [W h_i, W h_j] ) + g_e(e_ij)
```

其中：

```text
h_i, h_j: 节点隐藏表示；
e_ij: 相对边特征；
g_e: 边特征打分网络；
a, W: 可学习参数。
```

随后对可通信邻居进行 masked softmax：

```text
alpha_ij = softmax_j(score_ij), j in N_i
```

节点更新为：

```text
h_i' = tanh( sum_j alpha_ij W h_j )
```

其中 \(N_i\) 由通信半径和自环共同决定。不可通信节点被 mask，不参与注意力归一化。

这种设计使模型在小通信半径下更关注自身和目标节点，在大通信半径下能够利用更多队友信息。当前注意力热力图也支持这一现象：radius=4 时部分队友权重为 0，radius=10 时队友间注意力更均匀。

## 6. Actor-Critic 结构

策略网络由三部分组成：

```text
1. local observation encoder
2. edge-aware role graph encoder
3. policy head
```

局部观测编码：

```text
z_i = f_obs(o_i)
```

图编码得到无人机节点表示：

```text
g_i = f_graph(G)
```

策略输入为：

```text
u_i = [z_i, g_i, c]
```

其中 \(c\) 是可选辅助上下文。在当前实现中，\(c\) 来自目标行为辅助分支；但由于该分支目前 balanced accuracy 不足，论文主结论不依赖它。

动作分布为：

```text
pi_theta(a_i | o_i, G) = softmax(f_pi(u_i))
```

critic 使用集中式状态：

```text
V_phi(s) = f_v(s)
```

## 7. MAPPO 优化目标

采用 MAPPO 的 clipped policy objective。对每个智能体的优势估计 \(\hat{A}_i^t\)，定义概率比：

```text
rho_i^t(theta) = pi_theta(a_i^t | o_i^t, G^t) / pi_theta_old(a_i^t | o_i^t, G^t)
```

策略损失：

```text
L_policy = - E[ min(
    rho_i^t * A_i^t,
    clip(rho_i^t, 1 - epsilon, 1 + epsilon) * A_i^t
) ]
```

价值损失：

```text
L_value = 0.5 * E[ (R_i^t - V_phi(s^t))^2 ]
```

熵正则：

```text
L_entropy = E[ H(pi_theta(. | o_i^t, G^t)) ]
```

总损失：

```text
L = L_policy + c_v L_value - c_H L_entropy + c_aux L_aux
```

其中 \(L_aux\) 为可选辅助损失。当前论文主线可以将其视为辅助项，不作为方法有效性的核心来源。

## 8. 分阶段随机通信半径微调

固定通信半径训练容易使策略适应单一通信拓扑。例如，仅在 radius=8 下训练时，模型在 radius=10 的泛化表现反而下降。为缓解这一问题，EA-RG-MAPPO-S 采用两阶段训练：

### Stage 1：固定半径训练

先在中等通信半径 \(R_c=8\) 下训练 edge-aware role graph policy，使模型学到基本追击和协同能力。

### Stage 2：随机半径微调

从 Stage 1 的 checkpoint 出发，使用较小学习率进行短程微调。每个 episode 从区间中随机采样通信半径：

```text
R_c ~ Uniform(4, 10)
```

该阶段的目的不是重新学习策略，而是让已学到的协同表示适应不同通信拓扑，降低固定半径训练带来的过拟合。

实验结果显示，分阶段随机半径微调能够改善 radius=10 的泛化，同时保持 radius=4/6/8 下较低碰撞率。

## 9. 与现有方法的区别

与 MAPPO 相比：

```text
MAPPO 缺少显式队友-目标关系建模，有限通信下 seed 方差较大。
EA-RG-MAPPO-S 通过角色图和边特征显式建模队友、目标和通信关系。
```

与普通 GAT-MAPPO 相比：

```text
GAT-MAPPO 使用节点特征注意力，但缺少相对边特征。
EA-RG-MAPPO-S 将距离、方位、相对速度和通信可达性加入 attention score。
```

与朴素随机半径训练相比：

```text
直接从头随机半径训练会削弱低半径表现。
分阶段微调先学习稳定基础策略，再适应通信半径变化，更符合当前实验结果。
```

## 10. 复杂度与可扩展性

设节点数为 \(K=N+M\)，图注意力计算复杂度约为：

```text
O(K^2 d)
```

当前任务中 \(K=4\)，计算成本很低。扩展到更多无人机时，可以通过通信半径、top-k 邻居或稀疏邻接降低复杂度。

该方法后续可迁移到 6DOF/LAG/JSBSim 平台。迁移时无需改变核心思想，只需要将节点特征和边特征替换为更真实的飞行动力学状态、雷达观测、导弹威胁和有人机角色信息。

## 11. 当前方法边界

当前方法仍有两个边界需要在论文中如实说明：

1. 实验环境是二维简化追逃，不是完整 6DOF 空战。
2. 目标意图辅助分支尚未形成可靠 balanced accuracy，不能作为强可解释意图识别模块。

因此，当前论文应聚焦：

```text
有限通信下的边特征角色图协同决策
```

而不是：

```text
完整空战系统
高精度目标意图识别
导弹/雷达/有人机协同全流程
```
