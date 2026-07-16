# 论文完整草稿骨架

日期：2026-07-13

## 题目候选

中文题目：

```text
面向有限通信无人机协同追逃的边特征增强角色图多智能体强化学习方法
```

英文题目：

```text
Edge-Aware Role Graph Multi-Agent Reinforcement Learning for UAV Cooperative Pursuit under Limited Communication
```

如果强调分阶段训练：

```text
Edge-Aware Role Graph MAPPO with Staged Communication-Radius Adaptation for UAV Cooperative Pursuit
```

当前建议使用第一个英文题目，更简洁，也更贴近主贡献。

## 摘要草稿

无人机集群协同追逃任务要求多个异构平台在有限通信条件下完成目标拦截，同时避免平台间碰撞。现有多智能体强化学习方法通常依赖局部观测或普通图注意力表示，难以显式建模无人机之间的相对空间关系和通信可达性，导致在通信半径变化时策略稳定性不足。为此，本文提出一种边特征增强角色图多智能体强化学习方法 EA-RG-MAPPO-S。该方法将追击无人机和目标统一建模为带角色标记的动态图节点，并在图注意力得分中引入相对位置、距离、方位、相对速度和通信可达性等边特征，使策略能够根据物理关系和通信拓扑进行信息聚合。进一步地，本文设计分阶段随机通信半径微调机制，先在固定通信半径下学习基础协同策略，再在随机通信半径区间内进行低学习率微调，以提升跨通信半径鲁棒性。二维异构无人机协同追逃实验表明，在 mixed 目标机动和多种通信半径下，所提方法相比 MAPPO 和 GAT-MAPPO 具有更低碰撞率和更稳定的跨半径性能。可视化结果进一步表明，所提方法能够根据通信半径变化调整节点注意力分布。本文结果为有限通信条件下无人机协同决策提供了一种可扩展的图强化学习框架。

## 关键词

```text
无人机集群；多智能体强化学习；有限通信；图注意力网络；协同追逃；MAPPO
```

英文：

```text
UAV swarm; multi-agent reinforcement learning; limited communication; graph attention network; cooperative pursuit; MAPPO
```

## 1. Introduction

### 1.1 研究背景

可写要点：

1. 无人机集群协同拦截、巡逻和对抗任务对自主决策提出需求。
2. 多智能体强化学习适合处理协同策略学习，但现实无人机任务存在通信半径、异构平台和安全碰撞约束。
3. 单纯 MAPPO 缺少显式关系建模，普通 GAT 又缺少物理边语义。

### 1.2 问题挑战

三个挑战：

```text
1. 有限通信导致队友信息不完整；
2. 异构无人机和目标节点具有不同语义；
3. 协同追逃依赖相对距离、方位和速度等几何关系。
```

### 1.3 本文思路

本文不直接构建完整 6DOF 空战系统，而是在可控二维环境中验证有限通信协同算法。这样可以隔离算法因素，避免动力学和传感器复杂性掩盖方法贡献。

核心方法：

```text
EA-RG-MAPPO-S = MAPPO
              + role graph
              + edge-aware attention
              + staged random-radius fine-tuning
```

### 1.4 贡献点草稿

建议写成 3 条：

```text
1. 提出一种边特征增强角色图策略表示，将无人机和目标建模为带角色语义的动态图节点，并将相对位置、距离、方位、速度和通信可达性引入图注意力得分。

2. 设计分阶段随机通信半径微调机制，使策略先学习固定半径下的基础协同能力，再适应变化通信拓扑，从而提升跨通信半径稳定性。

3. 构建有限通信异构无人机协同追逃实验，对 MAPPO、GAT-MAPPO 和多个消融版本进行 3-seed 对比，并通过轨迹图、per-seed 散点图和注意力热力图分析方法行为。
```

不要写：

```text
提出高精度目标意图识别方法。
```

## 2. Related Work

建议分三类：

### 2.1 Multi-Agent Reinforcement Learning for UAVs

要点：

```text
MAPPO、MADDPG、QMIX、HAPPO 等；
无人机协同、追逃、空战决策；
现有方法常忽略通信受限和物理关系显式建模。
```

建议引用：

```text
\cite{yu2021mappo}
\cite{zhao2024uav_pursuit_evasion}
```

### 2.2 Graph Neural Networks for Multi-Agent Coordination

要点：

```text
GNN/GAT 能建模智能体关系；
普通 GAT 多依赖节点特征；
无人机任务需要将相对距离、方位、速度和通信可达性作为边语义。
```

建议引用：

```text
\cite{velickovic2017gat}
\cite{malysheva2020magnet}
\cite{liu2024gnn_marl}
```

### 2.3 Limited Communication and Robust Coordination

要点：

```text
通信半径、通信丢包、邻居选择；
有限通信下策略容易过拟合某一拓扑；
本文用 staged random-radius adaptation 提升跨半径稳定性。
```

建议引用：

```text
\cite{singh2018ic3net}
\cite{cuzin2026gnn_comm_survey}
\cite{feng2024gat_uav_comm}
\cite{kim2024uav_mec_madrl}
```

## 3. Problem Formulation

可直接整合：

```text
docs/paper_method_section_draft.md 的第 2、3 节
```

需要包含：

1. 任务定义；
2. 状态、观测、动作；
3. 有限通信图；
4. 优化目标；
5. 指标定义。

建议公式：

```text
G^t = (V^t, E^t)
rho_i^t(theta) = pi_theta / pi_theta_old
L = L_policy + c_v L_value - c_H L_entropy + c_aux L_aux
```

## 4. Method

章节结构：

### 4.1 Overview

引用图：

```text
results/figures/method_overview_ea_rg_mappo_s.png
```

说明方法组成：

```text
local observation encoder
role graph encoder
edge-aware attention
centralized critic
staged random-radius fine-tuning
```

### 4.2 Role Graph Construction

写：

```text
UAV nodes + target nodes
role embedding
communication mask
```

### 4.3 Edge-Aware Attention

写边特征：

```text
relative position
distance/world size
distance/communication radius
bearing
relative velocity
communication reachable
target flag
```

核心公式：

```text
score_ij = LeakyReLU(a^T[Wh_i, Wh_j]) + g_e(e_ij)
```

### 4.4 MAPPO Training Objective

写 clipped objective、value loss、entropy。

### 4.5 Staged Random-Radius Fine-Tuning

写：

```text
Stage 1: fixed radius=8
Stage 2: random radius in [4, 10], low learning rate
```

强调这是鲁棒性训练技巧，不是单纯加长训练。

## 5. Experiments

可整合：

```text
docs/paper_experiment_section_draft.md
results/paper_result_tables.md
```

### 5.1 Environment Settings

写：

```text
3 pursuers + 1 target
heterogeneous UAV types
mixed target policy
communication radii 4/6/8/10
100 episodes per seed
3 seeds
```

### 5.2 Baselines

写：

```text
MAPPO
GAT-MAPPO
RG-MAPPO
EA-RG-MAPPO
EA-RG-MAPPO-S
```

并注明历史实验名映射：

```text
RI no-edge -> RG-MAPPO
RI edge fixed-r8 -> EA-RG-MAPPO
RI edge staged -> EA-RG-MAPPO-S
```

### 5.3 Main Results

引用：

```text
results/final_300_eval_notes.md
results/latex_final_comm_300_table.tex
```

核心表述：

```text
EA-RG-MAPPO-S 在四个通信半径下保持 0.879-0.926 成功率；
碰撞率保持在 0.054-0.086；
相比 MAPPO 方差更小，相比 GAT-MAPPO 在 radius=8/10 更稳。
```

300-episode final table:

```text
radius=4:  success=0.926 ± 0.004, collision=0.054 ± 0.007
radius=6:  success=0.919 ± 0.012, collision=0.064 ± 0.006
radius=8:  success=0.890 ± 0.021, collision=0.083 ± 0.012
radius=10: success=0.879 ± 0.017, collision=0.086 ± 0.020
```

### 5.4 Ablation Study

讨论：

```text
RG-MAPPO vs EA-RG-MAPPO: 边特征贡献；
EA-RG-MAPPO vs EA-RG-MAPPO-S: staged 微调贡献；
```

注意：

```text
EA-RG-MAPPO fixed-r8 在 radius=4 上碰撞最低，但 radius=10 泛化较差；
EA-RG-MAPPO-S 是更均衡方案。
```

### 5.5 Visualization

引用：

```text
results/figures/per_seed_success_scatter.png
results/figures/per_seed_collision_scatter.png
results/figures/trajectory_ri_advantage_r4.png
results/figures/trajectory_ri_advantage_r10.png
results/figures/ri_attention_heatmap_r4.png
results/figures/ri_attention_heatmap_r10.png
```

### 5.6 Intent Branch Diagnostic

放在附录或讨论：

```text
plain accuracy=0.587
balanced accuracy=0.200
```

结论：

```text
当前不把 intent recognition 作为主贡献。
```

## 6. Discussion

可讨论：

1. 为什么边特征有用；
2. 为什么普通 GAT 不够；
3. 为什么 MAPPO 有时强但方差大；
4. 为什么 staged 微调是均衡选择；
5. 到 6DOF/LAG 的迁移路径。

建议写法：

```text
本文方法不是替代真实飞行动力学仿真，而是提供一种可迁移的有限通信协同表示层。
后续可将节点特征扩展为 6DOF 状态、雷达观测和导弹威胁，将角色扩展为有人机/无人机/导弹/目标等类型。
```

## 7. Conclusion

结论草稿：

本文针对有限通信条件下无人机协同追逃问题，提出了 EA-RG-MAPPO-S 方法。该方法通过角色图表示和相对边特征增强图注意力，使策略能够显式建模无人机、目标和通信拓扑之间的关系；通过分阶段随机通信半径微调，提升了跨通信半径的鲁棒性。实验表明，所提方法在 mixed 机动目标和多种通信半径下取得了更低碰撞率和更稳定表现。未来工作将进一步扩展到 6DOF 空战环境，并引入雷达、导弹和有人机协同因素。

## 8. 当前草稿还缺什么

必须补：

```text
1. Related Work 需要继续补本地中文论文和正式期刊/会议引用。
2. 方法公式需要排版成 LaTeX。
3. 主结果表需要转成论文格式。
4. 图需要统一字号和英文标注。
```

可选补：

```text
1. 5-seed 主表；
2. LAG/JSBSim 小迁移；
3. 注意力图更多案例；
4. 失败案例统计。
```

当前不建议补：

```text
短期继续微调 intent head，除非重新设计标签和历史观测。
```
