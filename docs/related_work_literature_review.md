# Related Work 文献综述初稿

日期：2026-07-13

说明：

```text
本文件用于支撑论文 Related Work 部分。
重点服务当前主线：EA-RG-MAPPO-S，即有限通信下的边特征增强角色图多智能体强化学习。
```

## 1. Multi-Agent Reinforcement Learning for Cooperative Control

多智能体强化学习为无人机集群协同决策提供了基础框架。PPO 是本文策略优化的基础，其 clipped objective 使 on-policy 策略梯度训练在实现复杂度和稳定性之间取得了较好平衡。经典 CTDE 范式允许训练阶段使用全局状态，而执行阶段每个智能体仅依赖局部观测。MADDPG、COMA、VDN 和 QMIX 分别代表了集中式 actor-critic、反事实信用分配和值函数分解等重要路线。MAPPO 是当前合作式多智能体任务中非常常用的强基线。Yu 等人在 MAPPO 工作中指出，经过合适实现和超参数设置后，PPO 类方法在多个合作式多智能体基准上可以取得有竞争力的表现。这一点对本文很重要，因为本文不能把 MAPPO 当作弱基线，而应将其视为需要严肃比较的强基线。

本文的实验也支持这一判断：MAPPO 在部分 seed 下可以取得较高成功率，但在有限通信压力下方差较大，低半径下碰撞率明显升高。因此，本文不是简单声称“图方法超过弱 MAPPO”，而是关注在通信半径变化下的稳定性和安全性。

可引用文献：

```text
Yu et al., The Surprising Effectiveness of PPO in Cooperative, Multi-Agent Games, 2021.
Schulman et al., Proximal Policy Optimization Algorithms, 2017.
Lowe et al., Multi-Agent Actor-Critic for Mixed Cooperative-Competitive Environments, NeurIPS 2017.
Foerster et al., Counterfactual Multi-Agent Policy Gradients, AAAI 2018.
Sunehag et al., Value-Decomposition Networks For Cooperative Multi-Agent Learning, AAMAS 2018.
Rashid et al., QMIX: Monotonic Value Function Factorisation for Deep Multi-Agent Reinforcement Learning, ICML 2018.
```

## 2. Graph Neural Networks for Multi-Agent Coordination

图神经网络适合处理多智能体系统中的关系建模问题。GAT 通过 masked self-attention 让节点能够对邻居特征进行加权聚合，为多智能体通信和协同提供了自然工具。已有工作如 MAGNet、GNNComm-MARL 相关综述和多智能体图通信方法均说明，图结构和注意力机制有助于在部分可观测、多智能体场景中学习更有效的信息聚合。

但是，普通 GAT 主要基于节点表示计算注意力权重，对无人机任务中的物理关系建模不足。无人机协同追逃强依赖相对距离、方位、速度差和通信可达性。如果仅使用节点特征注意力，模型需要间接从节点状态中推断这些关系，学习难度较高，也容易在通信半径变化时出现不稳定。

本文方法与普通 GAT-MAPPO 的核心区别在于：将相对边特征直接引入 attention score，使图注意力显式感知空间关系和通信约束。

可引用文献：

```text
Velickovic et al., Graph Attention Networks, ICLR 2018.
Malysheva et al., MAGNet: Multi-agent Graph Network for Deep Multi-agent Reinforcement Learning, 2020.
Cuzin-Rambaud et al., A Survey of Multi-Agent Deep Reinforcement Learning with Graph Neural Network-Based Communication, 2026.
Liu et al., Graph Neural Network Meets Multi-Agent Reinforcement Learning, 2024.
```

## 3. Limited Communication in MARL

现实无人机集群通常无法假设全局通信。通信半径、链路不稳定、带宽限制和邻居数量限制都会影响协同策略。IC3Net 等早期工作关注智能体何时通信，以及如何在合作与竞争任务中学习通信门控。近期 GNN-based communication 综述进一步指出，基于交互图的通信机制可以将多智能体信息交换过程结构化。

本文关注的不是“是否学习发送消息”，而是通信半径受限时，策略如何利用可达邻居和目标节点进行稳定决策。因此，本文在环境和图构建中显式加入通信半径 mask，并评估 radius=4/6/8/10 下的性能变化。

本文结果表明，固定通信半径训练会在其他半径下出现泛化问题；分阶段随机通信半径微调可以提升跨半径稳定性。这一点区别于只在固定拓扑或全通信条件下评估的图 MARL 工作。

可引用文献：

```text
Singh et al., Learning when to Communicate at Scale in Multiagent Cooperative and Competitive Tasks, 2018.
Cuzin-Rambaud et al., A Survey of Multi-Agent Deep Reinforcement Learning with Graph Neural Network-Based Communication, 2026.
```

## 4. UAV MARL and Pursuit-Evasion

无人机强化学习研究覆盖轨迹规划、资源分配、通信网络优化、追逃对抗和空战决策等任务。2024 年以来，多 UAV 通信和 MEC 场景中已有工作结合 GAT 或图结构进行轨迹和资源决策；UAV 追逃方向也有工作关注多角色协同、目标分配和深度强化学习。

这些工作说明 UAV 决策正在从单机控制转向多智能体协同。但大量通信/MEC 场景更关注吞吐量、资源分配或轨迹覆盖；追逃/空战场景则常采用规则、DQN 或特定角色分配机制。本文的定位是介于二者之间：以协同追逃为任务背景，重点研究有限通信下的图表示和鲁棒协同，而不是通信网络资源优化本身。

可引用文献：

```text
Feng et al., Graph Attention-based Reinforcement Learning for Trajectory Design and Resource Assignment in Multi-UAV Assisted Communication, 2024.
Kim et al., Cooperative Multi-Agent Deep Reinforcement Learning Methods for UAV-aided Mobile Edge Computing Networks, 2024.
Zhao et al., Autonomous Decision Making for UAV Cooperative Pursuit-Evasion Game with Reinforcement Learning, 2024.
```

## 5. 本文与已有工作的区别

可以在论文中这样总结差异：

```text
Existing MAPPO-based methods provide strong cooperative MARL baselines but do not explicitly encode limited-communication geometry.
GAT-based MARL methods introduce relation modeling but often rely mainly on node features or abstract interaction graphs.
UAV MARL studies demonstrate the feasibility of learning cooperative policies, but limited-communication robustness across varying radii is less emphasized.
```

本文贡献：

```text
1. 在 UAV 协同追逃任务中构建角色图，将 UAV 和目标作为不同语义节点；
2. 将相对距离、方位、速度和通信可达性作为边特征加入图注意力；
3. 用 staged random-radius fine-tuning 提升不同通信半径下的稳定性；
4. 通过 3-seed、4 个通信半径和多种消融验证方法有效性。
```

## 6. 可直接写入论文的 Related Work 草稿

### 6.1 Multi-Agent Reinforcement Learning

Multi-agent reinforcement learning has been widely studied for cooperative decision-making under partial observability. PPO provides the basic on-policy optimization backbone, while MADDPG, COMA, VDN, and QMIX establish representative CTDE and value-decomposition routes for multi-agent coordination. In the centralized-training decentralized-execution paradigm, agents can exploit global information during training while executing policies based on local observations. MAPPO has become a strong baseline for cooperative MARL, as PPO-based multi-agent methods can achieve competitive performance across diverse cooperative benchmarks when implemented carefully. Therefore, in this work MAPPO is treated as a strong baseline rather than a weak reference method.

### 6.2 Graph-Based Multi-Agent Coordination

Graph neural networks provide a natural representation for multi-agent interaction. Graph attention networks learn to aggregate information from neighboring nodes with adaptive attention weights, and have been extended to multi-agent reinforcement learning for scalable coordination and communication. However, vanilla graph attention mainly computes attention from node embeddings, while UAV pursuit tasks depend heavily on pairwise geometric relations such as relative distance, bearing, velocity difference, and communication availability. This motivates the proposed edge-aware role graph encoder, which injects physical edge attributes into the attention score.

### 6.3 Limited Communication and UAV Cooperation

In realistic UAV swarms, communication is constrained by range, bandwidth, and link availability. Existing communication-learning methods study when and how agents should exchange information, while recent GNN-based MARL methods use interaction graphs to structure communication. In UAV applications, graph attention and cooperative MARL have been used for trajectory design, resource assignment, mobile edge computing, and pursuit-evasion decision-making. Different from these studies, this work focuses on cooperative pursuit under explicitly varied communication radii and evaluates robustness across multiple communication settings.

## 7. 当前引用风险

需要注意：

```text
1. Related Work 中不能只引用 arXiv，最终投稿前最好补充期刊/会议正式版本。
2. UAV 追逃相关文献还需要继续补本地中文论文和空战/6DOF 文献。
3. 如果目标期刊偏控制/航空，需要增加制导、围捕、协同控制类传统方法引用。
4. 如果目标期刊偏 AI/机器人，需要增加 MARL/GNN/通信学习类引用。
```
