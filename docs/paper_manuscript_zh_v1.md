# 面向有限通信无人机协同追逃的边特征增强角色图多智能体强化学习方法

## 摘要

无人机集群协同追逃任务要求多个异构平台在有限通信条件下完成目标拦截，同时避免平台间碰撞。现有多智能体强化学习方法通常依赖局部观测或普通图注意力表示，难以显式建模无人机之间的相对空间关系和通信可达性，导致策略在通信半径变化时稳定性不足。为此，本文提出一种边特征增强角色图多智能体强化学习方法 EA-RG-MAPPO-S。该方法将追击无人机和目标统一建模为带角色标记的动态图节点，并在图注意力得分中引入相对位置、距离、方位、相对速度和通信可达性等边特征，使策略能够根据物理关系和通信拓扑进行信息聚合。进一步地，本文设计分阶段随机通信半径微调机制，先在固定通信半径下学习基础协同策略，再在随机通信半径区间内进行低学习率微调，以提升跨通信半径鲁棒性。二维异构无人机协同追逃实验表明，在 mixed 目标机动和多种通信半径下，所提方法相比 MAPPO 和 GAT-MAPPO 具有更低碰撞率和更稳定的跨半径性能。300 回合每种子复评结果显示，EA-RG-MAPPO-S 在通信半径 4、6、8、10 下分别取得 0.926、0.919、0.890、0.879 的成功率，并将碰撞率控制在 0.054 到 0.086 之间。可视化结果进一步表明，所提方法能够根据通信半径变化调整节点注意力分布。本文结果为有限通信条件下无人机协同决策提供了一种可扩展的图强化学习框架。

关键词：无人机集群；多智能体强化学习；有限通信；图注意力网络；协同追逃；MAPPO

## 1 引言

无人机集群在协同侦察、目标拦截、区域巡逻和空中对抗等任务中具有重要应用价值。与单机任务相比，集群任务更依赖多个平台之间的信息共享、角色分工和协同行为。在协同追逃场景中，多架追击无人机需要在动态目标机动和平台间安全约束下完成拦截；如果通信受限或协同策略不稳定，系统容易出现追击效率下降、无人机间碰撞或任务超时。

多智能体强化学习为无人机协同决策提供了端到端策略学习工具。集中训练、分散执行范式允许训练阶段使用全局信息，而执行阶段每个智能体仅依赖局部观测。MAPPO 等方法已经在多种合作式多智能体任务中表现出较强基线能力 \cite{yu2021mappo}。然而，普通 MAPPO 缺少显式关系建模机制，当通信半径受限时，不同无人机之间的相对空间关系和通信可达性难以被策略充分利用。图神经网络和图注意力机制为多智能体关系建模提供了自然表示 \cite{velickovic2017gat,malysheva2020magnet,liu2024gnn_marl}，但普通 GAT 主要从节点特征中计算注意力权重，并未显式利用无人机任务中关键的距离、方位、相对速度和通信约束。

现实无人机集群通常无法假设全局通信。通信半径、链路质量和带宽限制会改变智能体可获取的信息集合。已有通信学习和 GNN-based MARL 工作关注如何学习智能体间通信机制 \cite{singh2018ic3net,cuzin2026gnn_comm_survey}，UAV 通信与边缘计算场景中也已有图注意力和多智能体强化学习应用 \cite{feng2024gat_uav_comm,kim2024uav_mec_madrl}。但在无人机协同追逃任务中，如何在显式变化的通信半径下保持稳定协同，仍需要进一步研究。

本文从现实可实现角度出发，先在二维异构无人机协同追逃环境中验证有限通信图强化学习方法，而不直接进入完整 6DOF 空战、导弹、雷达和有人机协同系统。这样可以降低仿真复杂度，隔离算法贡献，并为后续迁移到 LAG/JSBSim 等平台提供可复用表示层。本文提出 EA-RG-MAPPO-S 方法，其核心由三部分组成：边特征增强角色图表示、基于 MAPPO 的集中训练分散执行优化、分阶段随机通信半径微调。

本文主要贡献如下：

1. 提出一种边特征增强角色图策略表示，将追击无人机和目标建模为带角色语义的动态图节点，并将相对位置、距离、方位、相对速度和通信可达性引入图注意力得分。
2. 设计分阶段随机通信半径微调机制，使策略先学习固定通信半径下的基础协同能力，再适应变化通信拓扑，从而提升跨通信半径稳定性。
3. 构建有限通信异构无人机协同追逃实验，对 MAPPO、GAT-MAPPO 和多个消融版本进行多种子对比，并通过轨迹图、散点图和注意力热力图分析方法行为。

需要说明的是，本文曾探索目标意图辅助分支，但诊断结果显示该分支当前 balanced accuracy 不足。因此，本文不将高精度目标意图识别作为主创新点，而将研究重点放在有限通信下的边特征角色图协同决策。

## 2 相关工作

### 2.1 多智能体强化学习

多智能体强化学习已广泛用于合作控制、资源分配和对抗决策等任务。PPO 通过截断策略优化目标提高了 on-policy 策略梯度训练的稳定性 \cite{schulman2017ppo}。在多智能体场景中，MADDPG、COMA、VDN 和 QMIX 分别从集中式 critic、反事实信用分配和值函数分解等角度缓解非平稳训练和协同信用分配问题 \cite{lowe2017maddpg,foerster2018coma,sunehag2018vdn,rashid2018qmix}。集中训练、分散执行框架通过集中式 critic 或集中式价值分解利用全局信息，同时保留执行阶段的分散性。MAPPO 是合作式多智能体任务中的常用强基线。Yu 等人的研究表明，经过合适实现和超参数设置后，PPO 类多智能体方法可以在多个合作式基准任务中取得有竞争力的性能 \cite{yu2021mappo}。因此，本文将 MAPPO 作为严肃基线，而不是弱参考方法。

在无人机协同任务中，强化学习被用于轨迹规划、目标追逃、空战机动和集群协同。近期 UAV cooperative pursuit-evasion 研究也表明，强化学习可以学习复杂追逃策略 \cite{zhao2024uav_pursuit_evasion}。但在有限通信条件下，单纯依赖局部观测和集中式 critic 仍可能出现种子间方差较大、低通信半径下碰撞率较高等问题。

### 2.2 图神经网络与多智能体协同

图神经网络适合处理多智能体系统中的关系建模问题。GAT 通过 masked self-attention 让节点自适应聚合邻居信息 \cite{velickovic2017gat}。在多智能体强化学习中，MAGNet 等工作探索了图网络在深度多智能体强化学习中的应用 \cite{malysheva2020magnet}。近期综述进一步总结了 GNN 与 MARL 在通信和协同中的结合方式 \cite{liu2024gnn_marl,cuzin2026gnn_comm_survey}。

然而，普通图注意力通常主要基于节点嵌入计算注意力分数。对于无人机协同追逃任务，智能体间相对距离、方位、速度差和通信可达性是影响协同决策的关键变量。如果这些物理关系只隐含在节点状态中，策略需要自行推断边关系，学习难度较高。本文因此将相对边特征直接加入注意力得分，使图编码器显式感知空间关系和通信拓扑。

### 2.3 有限通信无人机协同

现实无人机系统中的通信受到距离、带宽、链路质量和遮挡等因素影响。IC3Net 等工作关注智能体何时通信以及如何在多智能体任务中学习通信门控 \cite{singh2018ic3net}。UAV 通信网络和移动边缘计算任务中，已有研究结合图注意力和多智能体强化学习进行轨迹设计、资源分配和协同优化 \cite{feng2024gat_uav_comm,kim2024uav_mec_madrl}。

与上述工作不同，本文关注的是协同追逃任务中的有限通信鲁棒性。本文显式设置通信半径，并在半径 4、6、8、10 下评估策略性能。实验不仅关注成功率，也关注碰撞率和种子间方差，以反映策略在安全性和稳定性方面的实际可用性。

## 3 问题建模

考虑由 \(N\) 架追击无人机和 \(M\) 个机动目标组成的协同追逃任务。当前实验设置为 \(N=3, M=1\)。每个时间步 \(t\)，第 \(i\) 架无人机根据局部观测 \(o_i^t\) 和通信半径内的图信息 \(G^t\) 选择离散动作 \(a_i^t\)。动作包括转向和加减速组合。

训练阶段采用集中式 critic \(V_\phi(s^t)\)，其中 \(s^t\) 为全局状态；执行阶段每个智能体仅依赖局部观测和可通信图信息。优化目标为最大化团队折扣回报：

```text
max E[ sum_t gamma^t r^t ]
```

奖励由目标接近奖励、个体接近奖励、朝向奖励、成功拦截奖励、碰撞惩罚和超时相关惩罚组成。评价指标包括成功率、碰撞率、超时率和平均结束步数。其中碰撞率是本文重点关注的安全性指标。

有限通信通过通信半径 \(R_c\) 建模。若两个无人机之间距离超过 \(R_c\)，则其直接通信边不可用，相应局部队友观测槽位也置零。本文评估通信半径为：

```text
R_c in {4, 6, 8, 10}
```

## 4 方法

### 4.1 方法总览

本文方法记为 EA-RG-MAPPO-S，即 Edge-Aware Role Graph MAPPO with Staged random-radius fine-tuning。方法框图见：

```text
results/figures/method_overview_ea_rg_mappo_s.png
```

EA-RG-MAPPO-S 由局部观测编码器、边特征增强角色图编码器、集中式 critic 和分阶段随机通信半径微调组成。策略输入由局部观测表示和图表示拼接得到，critic 使用集中式全局状态。

### 4.2 角色图构建

每个时间步构建动态图：

```text
G^t = (V^t, E^t)
```

节点集合包括追击无人机节点和目标节点。每个节点包含归一化位置、航向、速度等运动状态，同时使用角色标记区分 UAV 和 target：

```text
role = 0: UAV
role = 1: target
```

节点特征与 role embedding 拼接后输入图编码器：

```text
h_i^0 = f_in([x_i, emb(role_i)])
```

角色图使模型能够区分队友节点和目标节点，避免将所有节点视为同质实体。

### 4.3 相对边特征增强注意力

对节点 \(i\) 到节点 \(j\) 的边，构造相对边特征：

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

边特征增强图注意力得分为：

```text
score_ij = LeakyReLU(a^T [W h_i, W h_j]) + g_e(e_ij)
```

其中 \(g_e\) 为边特征打分网络。随后对可通信邻居进行 masked softmax：

```text
alpha_ij = softmax_j(score_ij), j in N_i
```

节点表示更新为：

```text
h_i' = tanh( sum_j alpha_ij W h_j )
```

这种设计使注意力机制同时考虑节点语义和边的物理关系。注意力热力图显示，通信半径较小时，部分队友边不可达，UAV 节点主要关注自身和目标；通信半径较大时，注意力在队友和目标之间分布更均匀。

### 4.4 MAPPO 优化

策略网络输出每个智能体的动作分布：

```text
pi_theta(a_i | o_i, G)
```

采用 MAPPO clipped objective。概率比定义为：

```text
rho_i^t(theta) = pi_theta(a_i^t | o_i^t, G^t) / pi_theta_old(a_i^t | o_i^t, G^t)
```

策略损失为：

```text
L_policy = - E[ min(
    rho_i^t A_i^t,
    clip(rho_i^t, 1-epsilon, 1+epsilon) A_i^t
) ]
```

总损失为：

```text
L = L_policy + c_v L_value - c_H L_entropy + c_aux L_aux
```

其中 \(L_aux\) 是可选辅助损失。由于当前目标意图分支的 balanced accuracy 不足，本文主结论不依赖该辅助分支。

### 4.5 分阶段随机通信半径微调

固定通信半径训练容易使策略适应单一通信拓扑。本文采用两阶段训练：

1. Stage 1：在固定通信半径 \(R_c=8\) 下训练 edge-aware role graph policy，使模型学到基础协同能力。
2. Stage 2：从 Stage 1 checkpoint 出发，以较小学习率进行短程微调。每个 episode 从区间中随机采样通信半径：

```text
R_c ~ Uniform(4, 10)
```

该阶段的目标是增强策略对不同通信拓扑的适应性，而不是简单增加训练时间。

## 5 实验

### 5.1 环境设置

实验采用二维异构无人机协同追逃环境，包含 3 架追击无人机和 1 个机动目标。追击无人机具有不同最大速度、感知范围和能耗系数。目标采用 mixed 机动策略，包括远离最近追击者逃逸和随机转向机动。

最终主结果采用以下设置：

```text
target_policy = mixed
target_speed = 0.75
communication_radius = 4, 6, 8, 10
episodes = 300 per seed
seeds = 0, 1, 2
```

### 5.2 对比方法

本文比较以下方法：

1. MAPPO：无显式图结构的多智能体强化学习基线。
2. GAT-MAPPO：在 MAPPO 基础上加入普通图注意力。
3. EA-RG-MAPPO-S：本文最终方法，包含边特征增强角色图和分阶段随机半径微调。

在消融实验中，还比较 RG-MAPPO 和 EA-RG-MAPPO，用于分析角色图、边特征和 staged 微调的影响。

### 5.3 主结果

最终 300-episode 主表见：

```text
results/latex_final_comm_300_table.tex
results/final_comm_300_summary.csv
```

EA-RG-MAPPO-S 在四个通信半径下取得如下结果：

```text
radius=4:  success=0.926 ± 0.004, collision=0.054 ± 0.007
radius=6:  success=0.919 ± 0.012, collision=0.064 ± 0.006
radius=8:  success=0.890 ± 0.021, collision=0.083 ± 0.012
radius=10: success=0.879 ± 0.017, collision=0.086 ± 0.020
```

相比 MAPPO，EA-RG-MAPPO-S 在低通信半径下显著降低碰撞率。例如 radius=4 时，MAPPO 碰撞率为 0.228 ± 0.099，而 EA-RG-MAPPO-S 为 0.054 ± 0.007。相比 GAT-MAPPO，EA-RG-MAPPO-S 在 radius=8 和 radius=10 下成功率更高、碰撞率更低，并且标准差更小。

最终主图见：

```text
results/figures/final_300_success_rate.png
results/figures/final_300_collision_rate.png
```

### 5.4 消融分析

100-episode 全消融表保留用于分析模块贡献，对应 LaTeX 表：

```text
results/latex_ablation_comm_table.tex
```

RG-MAPPO、EA-RG-MAPPO 和 EA-RG-MAPPO-S 的比较表明，相对边特征能够降低低通信半径下的碰撞率，并修复部分种子在 radius=8 下的不稳定；分阶段随机通信半径微调能够恢复 radius=10 泛化，使模型在多个通信半径下表现更均衡。

需要注意，EA-RG-MAPPO fixed-r8 在某些单一半径下可能取得更低碰撞率，但在 radius=10 泛化较差。因此，EA-RG-MAPPO-S 更适合作为最终主方法，因为它在多半径条件下更稳定。

### 5.5 可视化分析

本文生成了多类可视化结果：

```text
results/figures/per_seed_success_scatter.png
results/figures/per_seed_collision_scatter.png
results/figures/trajectory_ri_advantage_r4.png
results/figures/trajectory_ri_advantage_r10.png
results/figures/ri_attention_heatmap_r4.png
results/figures/ri_attention_heatmap_r10.png
```

per-seed 散点图显示，MAPPO 在不同种子间波动较大，而 EA-RG-MAPPO-S 的成功率和碰撞率更集中。轨迹案例图显示，在相同环境种子下，基线方法可能出现碰撞，而 EA-RG-MAPPO-S 能保持成功追击。注意力热力图显示，通信半径变化会改变图注意力分布，支持有限通信图建模的解释。

### 5.6 目标意图分支诊断

当前实现曾包含目标意图辅助分支，但诊断结果显示：

```text
plain accuracy = 0.587
balanced accuracy = 0.200
```

说明该分支主要预测多数类，不能作为高精度意图识别模块。因此，本文不将意图识别作为主贡献。未来若继续强化该方向，需要引入短时历史、目标转弯率等可观测运动特征，并使用 balanced accuracy 作为主要评价指标。

### 5.7 目标速度泛化评估

为进一步验证方法稳定性不是单一目标速度设置下的偶然结果，本文在不重新训练模型的条件下，将 mixed 目标速度设置为 0.60、0.75 和 0.90，并在通信半径 4 和 8 下进行 100 回合每种子的附录级评估。结果见：

```text
results/speed_robustness_summary.csv
results/latex_speed_robustness_table.tex
results/figures/speed_robustness_success_r4.png
results/figures/speed_robustness_collision_r4.png
results/figures/speed_robustness_success_r8.png
results/figures/speed_robustness_collision_r8.png
```

速度泛化结果显示，随着目标速度升高，三种方法成功率均下降、碰撞率总体上升，但 EA-RG-MAPPO-S 仍保持较低碰撞率。当目标速度为 0.90 时，EA-RG-MAPPO-S 在 radius=4 下成功率为 0.867、碰撞率为 0.097，而 MAPPO 和 GAT-MAPPO 的碰撞率分别为 0.240 和 0.237；在 radius=8 下，EA-RG-MAPPO-S 碰撞率为 0.130，低于 MAPPO 的 0.300 和 GAT-MAPPO 的 0.203。该结果支持“低碰撞优势不只来自单一 target_speed 设置”的结论。

需要注意，该实验是 100-episode 附录级评估，不替代 300-episode 主结果。

### 5.8 Edge feature 评估时屏蔽诊断

为分析策略对不同边特征分量的依赖，本文进一步进行评估时屏蔽诊断：保持训练好的 EA-RG-MAPPO-S 参数不变，仅在评估时将某一组 edge feature 维度置零。结果见：

```text
results/edge_feature_ablation_summary.csv
results/latex_edge_feature_ablation_table.tex
results/figures/edge_feature_ablation_delta.png
```

结果显示，单独屏蔽位置、距离、方位或相对速度边特征时，30 回合诊断均值变化较小；屏蔽通信可达性和目标节点标记时，在 radius=4 和 radius=8 下均出现小幅成功率下降和碰撞率上升。屏蔽全部 edge feature 后没有出现灾难性退化，说明节点特征、邻接 mask 和局部观测中存在冗余信息。因此，该实验只能作为机制诊断，主消融证据仍应使用训练期消融表。

## 6 讨论

实验结果表明，有限通信下的稳定性不仅依赖是否使用图结构，还依赖图结构是否包含任务相关的物理边语义。普通 GAT-MAPPO 能在部分半径下改善 MAPPO，但在 radius=8/10 下仍存在成功率下降和碰撞率升高问题。EA-RG-MAPPO-S 通过相对边特征和 staged 随机半径微调，使策略在多个通信半径下保持更稳定表现。

本文方法的一个重要特点是可扩展性。当前实验使用二维追逃环境验证算法贡献，但方法本身并不依赖二维动力学。后续迁移到 LAG/JSBSim 或 6DOF 空战平台时，可以将节点特征扩展为三维位置、姿态、速度、过载、雷达观测和导弹威胁，将角色扩展为有人机、无人机、导弹、目标和僚机等类型。边特征也可以扩展为视距、雷达可探测性、导弹不可逃逸区和通信链路质量。

本文仍存在局限。首先，当前实验环境是二维简化追逃，不等同于完整空战系统。其次，目标意图辅助分支尚未形成可靠 balanced accuracy。最后，当前主结果使用 3 个随机种子，虽然 300 回合每种子复评已经提高可信度，但若面向更高要求期刊，仍可进一步扩展到 5 个种子或加入 LAG 小规模迁移验证。

## 7 结论

本文针对有限通信条件下无人机协同追逃问题，提出了 EA-RG-MAPPO-S 方法。该方法通过角色图表示和相对边特征增强图注意力，使策略能够显式建模无人机、目标和通信拓扑之间的关系；通过分阶段随机通信半径微调，提升了跨通信半径的鲁棒性。实验结果表明，所提方法在 mixed 机动目标和多种通信半径下取得了更低碰撞率和更稳定表现。未来工作将进一步扩展到 6DOF 空战环境，并引入雷达、导弹和有人机协同因素。

## 参考文献

参考 BibTeX 初版见：

```text
docs/references_seed.bib
```

后续需要将参考文献转换为目标期刊格式，并补充本地中文空战/无人机论文引用。
