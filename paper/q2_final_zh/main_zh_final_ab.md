# 面向中继拓扑退化的异构多无人机协同训练暴露塑形

## 摘要

异构多无人机协同依赖目标感知、通信转发与任务支撑在角色之间形成连续的信息链。中继节点故障并不必然造成完全断联，却会改变攻击角色可合法使用的信息来源、缓存时效和协同路径，从而使训练阶段的拓扑暴露与执行阶段的结构性需求发生失配。本文研究这一训练暴露塑形问题：在策略主干、集中训练分散执行框架、PPO 目标、奖励、观测、动作、执行期信息边界、训练预算、名义工况暴露和故障支持集合均保持一致时，仅改变多个冻结故障组在 reset 阶段的采样分配，能否改善故障条件下的协同任务表现及其可靠性代价。为此，本文提出有界自适应拓扑扰动重加权方法（DRTP）。该方法以故障组回报相对名义工况的偏离构造训练期困难代理，周期性更新故障组采样质量，并以概率边界维持所有冻结组的持续覆盖。在两个相互独立、训练前冻结的 10M cohort 中，DRTP 相对参数量、条件集合和预算匹配的均匀拓扑随机化基线，扰动条件平均回报分别提高 39.64 和 23.15；正向配对种子数分别为 3/5 与 4/5。两个 cohort 中 DRTP 的观测最差种子和平均超时率均优于 UTR；A cohort 的碰撞率则由 0.003 升至 0.009，表明任务收益不能被直接等同为全面安全改进。本文据此将 DRTP 定位为一种在所评估中继拓扑故障条件下重复获得 cohort 级收益的训练暴露分配方法，而不主张每个训练种子均提升、一般分布鲁棒保证或执行期信息恢复。

## 关键词

异构多无人机；多智能体强化学习；通信拓扑退化；继电节点故障；训练暴露塑形；固定终点评价；训练种子

## 1 引言

### 1.1 中继拓扑退化是协同决策中的结构性问题

异构无人机编队通常由具有不同感知、通信和任务执行能力的平台共同完成任务。本文关注由侦察机、继电机和攻击机组成的三机协同系统：侦察机获取目标信息，继电机提供潜在的多跳通信支持，攻击机仅利用合法获得的信息形成攻击窗口。该任务的难点不只来自单机运动学，还来自信息能否沿合法的感知、通信和任务支撑关系传递。因此，协同策略面对的是一个随角色状态和空间几何变化的通信—任务图，而不是三个彼此独立的控制器。

继电节点故障对该图施加的是结构性扰动。故障窗口内，与继电机相关的通信关系会失效；在物理规则允许时，侦察机至攻击机的直接边仍可合法存在。由此，信息路径可能由“侦察机—继电机—攻击机”重构为“侦察机—攻击机”。研究问题并非在隐藏信息消失后恢复它，而是策略能否在合法信息路径和任务支撑关系改变后维持协同任务能力。

### 1.2 从故障多样性到训练暴露塑形

图结构多智能体强化学习、通信学习与鲁棒强化学习已经提供了关系建模、合法消息聚合和环境随机化的基础[2--5,17--21]。在多无人机通信网络中，节点失效也会改变可用转发路径与团队协同约束[15--16,27--30]。然而，单纯扩大故障条件集合并不回答一个训练分布问题：当多个故障组的当前任务难度不同，固定均匀随机化可能在相对容易的条件上重复消耗训练预算，而对更需要适应的结构性扰动暴露不足。

本文不把该问题包装为一般最坏情况优化，也不改变策略网络或执行期信息边界。相反，本文将可检验缺口限定为：在相同拓扑扰动支持、相同正常工况锚点和相同 PPO 学习器下，有界自适应故障组重加权是否会相对于均匀重加权改变故障任务表现及其可靠性权衡。这样的比较把方法差异限制在训练期 reset 条件的暴露分配，从而避免把容量、输入、奖励或任务接口差异误归因于采样器。

### 1.3 本文方法、证据问题与贡献

本文采用参数匹配的单图 MAPPO 作为共同策略主干。UTR 固定保留 50% 名义工况暴露，并在六个故障组间均匀分配其余质量；DRTP 保留完全相同的名义锚点和故障支持，仅依据故障组回报相对名义工况的偏离，周期性地在有界单纯形内更新权重。执行期 actor 不接收故障标签、全局拓扑真值、最短路或未来链路信息。

本文围绕以下问题组织证据。RQ1：在冻结的 UTR—DRTP 主比较中，自适应故障组暴露是否改善扰动任务端点？RQ2：任务增益是否伴随超时、碰撞或下尾表现的变化？RQ3：两个独立冻结 cohort 是否给出同方向的 cohort 级结论？RQ4：在训练未读取的预先冻结结构条件带上，结论的适用范围如何变化？RQ5：DRTP 与通用优先级式采样的关系如何定位？采样器遥测又能够证明什么，不能证明什么？

本文的贡献包括：

1. 将异构无人机中继故障定义为合法通信、信息路径和任务支撑关系的重构，并以严格执行期信息边界构造轻量 3DOF 协同任务；
2. 提出 DRTP，在不改变 actor、critic、PPO、奖励、观测、动作或故障支持集合的条件下，仅对冻结故障组实施有界自适应训练暴露分配；
3. 通过两个独立、训练前冻结的 10M cohort，以及源哈希可追溯的训练排除结构条件与 PLR-style 外部定位比较，分层报告平均回报、配对方向、下尾、超时和碰撞，从而给出 DRTP 相对于均匀暴露的受控经验边界。

## 2 相关工作

### 2.1 图结构多智能体强化学习

可学习通信、目标消息路由和注意力式通信为多智能体协同提供了多种关系表示与信息选择机制[17--21]。图注意力与拓扑感知策略梯度方法则可根据邻接关系聚合合法邻居信息[2--3]，并已用于多无人机协同搜索、跟踪和集群控制[6--7]。这些研究说明“使用图”本身不能构成本文的创新。本文固定同一个单图策略网络与价值网络，将研究焦点限定为拓扑扰动在训练期的分布方式。

### 2.2 鲁棒与分布变化下的多智能体学习

鲁棒 MARL 研究涵盖对手策略变化、环境动力学不确定性以及最坏情况优化等路线[4]，分布鲁棒 Q 学习则形式化了指定环境分布下的歧义集合[5]。组鲁棒优化、主动域随机化、课程、关卡回放、无监督环境设计和稳健 on-policy 采样分别研究最差组目标、环境参数采样、任务序列或采样数据分布[11--13,22--26]。DRTP 与这些思想存在明确知识继承关系，但贡献边界更窄：本文不建立一般 DRMDP 理论，不声称求得严格最坏情况策略，也不提供分布鲁棒保证；它只在冻结的六类拓扑扰动组上实现可复现的有界经验重加权。

### 2.3 通信受限与故障条件下的多无人机协同

现有无人机通信与 MARL 工作已围绕抗干扰通信、多跳中继、节点失效后的网络恢复，以及协同资源分配构建不同目标[8--9,27--30]。本文研究的输出不是通信吞吐量或网络连通度本身，而是中继节点故障引起路径与任务支持组成变化后，异构团队的任务得分和安全表现。因此，相关方法具有研究定位价值，但在动作空间、学习器、奖励和策略网络信息边界上并非可直接迁移的公平基线。

### 2.4 本文定位与对照边界

本文的核心经验比较是 UTR-SG-MAPPO 与 DRTP-SG-MAPPO。两者接触相同的七个训练组，具有相同参数量、PPO、环境、奖励、训练预算和配对评估样本带。该设计回答的是“在相同拓扑扰动集合上，自适应加权是否优于均匀加权”，而不是“DRTP 是否优于所有鲁棒 MARL”，也不回答“在线自适应是否优于任意固定非均匀分布”。

为补充同任务下的性能定位，本文还训练并评价了无图 MAPPO 性能参考（Non-Graph MAPPO Performance Reference，MAPPO-NoGraph）。该参考使用相同训练种子、10M 预算、环境、奖励和共同评价样本带，但移除了图消息输入，参数量为 35,771，与 UTR/DRTP 的 116,728 参数 SG 主干不同。因此，它只能回答该无图 MAPPO 参考在冻结任务中的性能位置，不能归因图结构、模型容量或 DRTP 自适应加权的单独作用。对 TAPE、M3DDPG 和相关无人机中继方法的审计表明，它们需要改变当前任务或学习合同，因而本文将其用于知识定位，不堆砌表面公平、实质不可比的对比方法。

## 3 问题建模

### 3.1 异构角色与 3DOF 环境

环境包含三架蓝方无人机和一个目标，蓝方角色依次为侦察机（智能体 0）、中继机（智能体 1）和攻击机（智能体 2）。仿真采用轻量三自由度（3DOF）运动学，时间步长为 1 s，最大时域为 260 步，水平空间半径为 50 km，高度范围为 1–9 km。每架蓝方无人机从 27 个离散动作中选择转向、爬升和加减速指令的组合。不同角色具有冻结的速度、加速度、转弯、爬升、雷达、通信和攻击几何参数。

每个策略网络（actor）的局部观测包含自身位置、速度、航向、航迹倾角、合法目标相对信息、探测状态、局部攻击窗口、能量、角色、入向连通度、消息时效和目标缓存置信度等 34 维特征。环境同时启用严格目标感知和智能体目标信息瓶颈：未探测目标且未合法接收新鲜缓存的智能体不能通过共享图获得真实目标状态。集中式价值网络（critic）仅用于集中训练分散执行（CTDE）[14]，不向策略网络增加执行期信息。

### 3.2 通信–任务图与合法信息边界

记时刻 (t) 的图为

\[
G_t=(V,E_t,X_t,Z_t),
\]

其中 (V) 包含三架 UAV 与目标节点，(X_t) 和 (Z_t) 分别表示节点和边特征。邻接矩阵采用 receiver-row 约定：

\[
A_t[i,j]=1
\]

表示接收方 (i) 当前能够合法使用来自发送方 (j) 的关系。感知边仅由冻结感知模型产生；通信边同时满足物理通信距离、节点状态和通信实现；任务支持边由已合法交付的信息与活跃任务支持状态产生，不构成额外隐藏信息通道。单图编码器使用这些合法关系的并集邻接矩阵，但策略网络不接收故障标签、最短路、未来链路或仿真器真实状态。

### 3.3 中继节点故障与路径重构

中继节点故障在冻结起始时刻 (t_f) 和持续时间 (d_f) 内禁用中继机的感知、发送与接收能力，并移除其相关通信边。典型故障 F0 定义为

\[
t_f=44,\qquad d_f=80.
\]

故障前，合法信息可能经“侦察机→中继机→攻击机”传递；故障后，若物理规则允许，“侦察机→攻击机”可继续作为合法直连路径。故障事件因此表现为

\[
0\rightarrow1\rightarrow2
\quad\longrightarrow\quad
0\rightarrow2,
\]

而不是必然的信息全失。本文将需要策略适应的对象定义为 communication-path composition、task-support source 和 coordination geometry 的变化。

![图1｜中继故障下的合法路径重构](formal_results/figures/fig1_relay_failure_topology_reconfiguration.png)

**图1｜中继节点故障下的通信—任务路径重构与信息边界。** 中继相关通信关系在故障窗口内失效；若物理规则满足，侦察机至攻击机的直连仍可能合法。图中区分训练合同信息与执行期允许输入，避免将故障标签或全局拓扑真值注入策略网络。

### 3.4 正常工况、F0 与跨扰动条件

正常工况（nominal）不注入中继节点故障。除 F0 外，训练与正式评价覆盖以下扰动组：早期故障时机 `TE={(28,80),(36,80)}`、晚期故障时机 `TL={(52,80),(60,80)}`、短持续时间 `DS={(44,40),(44,60)}`、长持续时间 `DL={(44,100),(44,120)}` 和复合扰动 `CP={(28,120),(60,120)}`。括号分别表示故障起始时刻和持续时间。十个具体 onset--duration 成员同时属于训练 sampler 的组内均匀支持集和正式评价条件；正式配对评估样本带对全部方法和训练种子使用相同的 100 个基础 episode ID，并在 12 个条件间复用这些 ID，以减少场景差异对配对比较的干扰。

### 3.5 性能、安全与技术有效性 estimands

记某条件 (c) 下的平均 episode mission score 为 (J_c)。每个 episode 的 mission score 是三架蓝方无人机逐步奖励之和；它不是距离、时间或通信吞吐量等单一物理量。其共同部分奖励团队向目标接近、目标跟踪、攻击窗口、合法通信连通性及信息时效，并对其改善给予增量奖励；角色项分别奖励侦察发现、中继连通和攻击窗口，能量消耗、碰撞和约束违规施加惩罚，满足连续攻击窗口条件的任务完成给予终端奖励。因此，较高的 (J_c) 表示在既定奖励合同下更完整的“接近--信息支持--攻击窗口--完成”任务过程，但不能替代 success-at-horizon、超时、碰撞和约束违规等终局/安全指标。本文始终将这些指标并列报告。

本文报告

\[
J_{\mathrm{nominal}},\qquad J_{F0},
\]

以及十个跨扰动条件的

\[
J_{\mathrm{pert,mean}}=\frac{1}{10}\sum_{c\in\mathcal C_{\mathrm{pert}}}J_c,
\qquad
J_{\mathrm{pert,worst}}=\min_{c\in\mathcal C_{\mathrm{pert}}}J_c.
\]

其中 \(\mathcal C_{\mathrm{pert}}\) 为十个冻结的时机、持续时间和复合条件。它们的具体 onset--duration 成员已被训练 sampler 使用；因此 `J_pert,mean` 与 `J_pert,worst` 是跨扰动汇总指标，不是严格未见分布外（OOD）指标。为保持原始归档可追溯性，机器结果字段 `J_OOD_mean` 与 `J_OOD_worst` 分别映射到本文的 `J_pert,mean` 与 `J_pert,worst`。与主端点分开，本文在训练完成后对固定 A/B endpoint 执行训练未读取的 held-out tape；其中结构条件带在运行前冻结，包含节点位置变化与有向或对称边删除，具体合同及其分层结果见第6.4节。该评价不重新训练、不选择 checkpoint，且不将 episode 计为额外训练重复。

故障退化量定义为

\[
D_c=J_{\mathrm{nominal}}-J_c.
\]

方法间的同条件、同训练种子配对差值另记为

\[
\Delta J_c^{D-U}=J_c^{\mathrm{DRTP}}-J_c^{\mathrm{UTR}}.
\]

任务得分之外，本文报告碰撞率、超时率、约束违规率、episode 长度、故障触发前碰撞率和故障起始时刻存活比例。故障触发技术有效性只在计划故障起始时刻前仍存活的风险集 (R_c) 上计算：

\[
V_{\mathrm{trigger},c}=
\frac{\#\{\text{在 }R_c\text{ 中正确触发故障的 episodes}\}}
{|R_c|}.
\]

在故障起始时刻前因碰撞合法终止的 episode 不属于评估器缺陷，也不会从无条件任务得分或安全汇总中删除。

## 4 方法

### 4.1 参数匹配的单图 MAPPO

两种方法共用单图 MAPPO。对智能体 (i)，策略网络根据局部观测和合法图表示产生离散动作分布：

\[
a_{i,t}\sim\pi_\theta(a_{i,t}\mid o_{i,t},G_{i,t}).
\]

节点特征经线性编码后进入两层共享图注意力模块，图表示与本地观测表示融合后输出 27 维动作对数概率。集中式价值网络在训练期估计 (V_\phi(s_t))。训练使用标准裁剪 PPO 与广义优势估计（GAE）[10]：学习率 (3\times10^{-4})、折扣因子 0.99、GAE 系数 0.95、裁剪系数 0.2、熵系数 0.01、价值损失系数 0.5、最大梯度范数 0.5，每批执行 4 轮 PPO 更新。UTR 与 DRTP 的可训练参数量均为 116,728。

![图2｜UTR 与 DRTP 的训练分布差异](formal_results/figures/fig2_utr_drtp_training_distribution.png)

**图2｜UTR 与 DRTP 的训练分布差异和隔离变量。** 两种方法具有相同的策略网络、PPO、训练组、正常工况锚点、预算与评估协议；只有故障组权重由固定均匀分布或有界自适应规则产生不同。自适应器仅在训练期运行，不增加执行期参数或输入。

### 4.2 Uniform Topology Randomization

训练组集合为

\[
\mathcal G=\{N,F0,TE,TL,DS,DL,CP\}.
\]

UTR 固定正常工况采样质量：

\[
p_N=0.50.
\]

在故障组集合
\(
\mathcal F=\{F0,TE,TL,DS,DL,CP\}
\)
上采用条件均匀分布：

\[
q_k^{\mathrm{UTR}}=\frac{1}{6},\qquad
p_k^{\mathrm{UTR}}=(1-p_N)q_k^{\mathrm{UTR}}=\frac{1}{12}.
\]

组内两个 scenario member 再以相同概率采样。UTR 因而与 DRTP 接触完全相同的 topology-training universe。

### 4.3 DRTP 有界自适应拓扑扰动重加权

DRTP 是训练期的有界采样控制器，而不是一般 min--max 或分布鲁棒优化问题的求解器。它保持故障暴露总质量 \(1-p_N=0.50\) 不变，只在六个预定义故障组之间重新分配该质量；其可行权重集合为

\[
\mathcal Q=\left\{q\in\Delta^6:0.05\le q_k\le0.35\right\}.
\]

该采样器不改变 PPO 损失，也不近似求解一个可证明的内层对手分布。设第 (u) 个自适应边界前收集到组 (k) 的已完成 episode 平均回报为 \(\widehat J_{k,u}\)。若该组在窗口内被观测，则其指数移动平均（EMA）更新为

\[
\bar J_{k,u}=(1-\kappa)\bar J_{k,u-1}+\kappa\widehat J_{k,u};
\]

未观测组的 EMA 保持不变。Nominal EMA 采用相同规则。相对正常工况的性能缺口定义为

\[
d_{k,u}=\operatorname{clip}\!\left(
\frac{\bar J_{N,u}-\bar J_{k,u}}
{\max(|\bar J_{N,u}|,\epsilon)},0,d_{\max}
\right),
\]

并通过去均值得到中心化性能缺口

\[
\tilde d_{k,u}=d_{k,u}-\frac{1}{6}\sum_{j\in\mathcal F}d_{j,u}.
\]

指数重加权候选为

\[
\tilde q_{k,u+1}=
\frac{q_{k,u}\exp(\eta\tilde d_{k,u})}
{\sum_{j\in\mathcal F}q_{j,u}\exp(\eta\tilde d_{j,u})},
\]

最终权重经过平滑与有界单纯形投影：

\[
q_{u+1}=\Pi_{\mathcal Q}\left[(1-\beta)q_u+\beta\tilde q_{u+1}\right].
\]

这里的 \(\Pi_{\mathcal Q}\) 是对欧氏距离的有界单纯形投影，而不是逐元素截断后任意归一化。对待投影向量 \(x\)，实现寻找标量 \(\lambda\)，使

\[
q_k=\min\{0.35,\max\{0.05,x_k-\lambda\}\},
\qquad \sum_{k\in\mathcal F}q_k=1.
\]

实现以确定性有界单纯形投影求解 \(\lambda\)，并在数值容差内检查总质量和逐组边界。该程序只作用于训练期的六维采样权重，不涉及策略或价值网络参数、PPO 损失或执行期输入。完整数值实现、容差与可复现性检查见补充材料。

冻结超参数为：初始 (q_k=1/6)，前 128 updates 均匀 warm-up，之后每 32 updates 适配一次，\(\kappa=0.20\)、\(\eta=1.00\)、\(\beta=0.50\)、\(d_{\max}=2.00\)、\(\epsilon=10^{-8}\)。该更新受组鲁棒重加权和自适应域随机化的经验动机启发[11--12]，但本文仅检验它相对均匀采样的经验效果。

### 4.4 Nominal competence anchor

DRTP 中存在两种不同的锚点。第一，(p_N=0.50) 固定正常工况暴露比例，避免自适应器将全部训练质量转移到故障条件。第二，\(\bar J_N\) 作为任务能力参照，使性能缺口表示某故障组相对正常工况的任务差距。二者均属于训练采样器，不是辅助损失，也不进入策略网络或价值网络。

### 4.5 训练流程、复杂度与信息边界

每次环境重置时，采样器先以 0.5 概率选择正常工况；否则根据 (q) 选择故障组，再在组内均匀选择故障起始时刻和持续时间。UTR 的 (q) 固定，DRTP 的 (q) 仅在自适应边界更新。组标签、故障起始时刻、持续时间、EMA、性能缺口和 (q) 只存在于训练记录和日志中。评价阶段不实例化自适应采样器。

DRTP 不增加 trainable parameter，也不改变 inference graph。其附加计算来自按组累计 episode return、EMA 更新和六维有界投影；因此论文只主张“参数量相同且无 inference-time 模块”，不在缺少共同硬件日志的情况下声称 wall-clock 或显存优势。



## 5 最终冻结实验设计与证据分层

### 5.1 主比较与唯一变化项

本文的主比较是 UTR-SG-MAPPO 与 Original DRTP-SG-MAPPO。两者均采用单图 actor/critic、相同 PPO 超参数、环境、奖励、观测、动作、七个训练组、50% 名义工况锚点、39,063 次更新、4 个并行环境和 64 步轨迹片段；每条轨迹对应 10,000,128 个环境步，且只使用固定 10M endpoint checkpoint。唯一变化项是六个冻结故障组间的训练期质量分配：UTR 为条件均匀，DRTP 为有界自适应。

| 项目 | cohort A | cohort B |
|---|---|---|
| 训练种子 | 78011--78015 | 78021--78025 |
| UTR/DRTP 训练 | 各 5 条、从零开始 | 各 5 条、从零开始 |
| 训练预算 | 每条 10,000,128 environment steps | 每条 10,000,128 environment steps |
| endpoint tape | 780000--780099 | 781000--781099 |
| 评价条件 | nominal、F0、TE、TL、DS、DL、CP | 相同条件集合 |
| 评价规模 | 7 条件 × 100 episodes × 4 arms × 5 seeds | 相同规模 |

cohort A 和 B 的训练种子、训练过程与评价 tape 相互独立。训练种子是独立统计单位；每个 seed 下的多个条件和 episode 用于形成该 seed 的 endpoint，不被误当作额外独立训练重复。两批 cohort 分开报告；十个种子的合并展示只可作描述性补充，不用作确认性推断。

### 5.2 端点、可靠性指标与统计表达

主要任务端点为各 seed 的扰动条件平均回报 \(J_{\mathrm{perturbed}}\)。同时报告中位数、最差 seed、样本标准差、扰动成功率、超时率与碰撞率。方法间差异按相同训练 seed 的 endpoint 配对计算；本文报告方向计数与 cohort 内描述性效应，不虚构 p 值、置信区间或将 episode 数作为 \(n\)。

结果解释遵循三条规则。第一，较高任务回报不自动等同于安全改进。第二，sampler log 可以证明训练分布被改变，但不能单独证明某种内部策略机制或信息恢复。第三，预先冻结的训练排除条件评价与 PLR-style 比较作为分层支撑证据，不替代 UTR—DRTP 的主受控比较；跨规模、全因子消融和运行开销仍须在各自冻结协议完成并经审计后才可纳入。

### 5.3 当前论文的证据边界

本文主结论仅使用 `78011--78015` 与 `78021--78025` 最终 A/B cohort。早期 2301--2305 与 2401--2405 项目结果属于不同的历史合同，不被重命名为本文的正式或独立确认 cohort，也不参与主表、摘要或结论的样本量。旧 6-UAV 训练因故障时机晚于大量 episode 终止而永久排除；后续 `fault-step=3` 协议须完成结果与注入有效性审计后才具有跨规模证据资格。

## 6 双 cohort 受控结果

### 6.1 两个冻结 cohort 中均观察到更高的扰动任务回报

表2给出 UTR 与 DRTP 的绝对 endpoint。A cohort 中，DRTP 的平均扰动回报为 216.66，高于 UTR 的 177.02；B cohort 中，对应数值为 210.34 与 187.18。以同一训练 seed 配对后，DRTP 相对 UTR 的 cohort 平均差分别为 +39.64 和 +23.15。两批的独立重复方向因此支持“在所评估冻结合同下的 cohort 级扰动任务收益”，而不是由单一有利训练队列支撑的结论。

**表2｜最终冻结 A/B cohort 的 UTR 与 DRTP 扰动端点。** 数值为五个独立训练种子的汇总；标准差为样本标准差。

| Cohort | 方法 | J_perturbed 均值 | 中位数 | 最差 seed | 样本 SD | 成功率 | 超时率 | 碰撞率 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| A | UTR | 177.02 | 181.12 | 79.75 | 64.53 | 0.267 | 0.730 | 0.003 |
| A | DRTP | 216.66 | 223.82 | 191.49 | 23.48 | 0.394 | 0.597 | 0.009 |
| B | UTR | 187.18 | 181.42 | 164.98 | 21.66 | 0.289 | 0.711 | 0.000 |
| B | DRTP | 210.34 | 218.78 | 172.03 | 30.54 | 0.398 | 0.602 | 0.000 |

### 6.2 配对方向与下尾表现共同限定结果解释

平均值不应替代逐 seed 检查。A 中 DRTP 的扰动回报在 3/5 个配对 seed 中为正，B 中为 4/5 个配对 seed 为正。尽管 A 未达到逐 seed 单调获益，DRTP 的观测最差 seed 在两批中均高于 UTR：A 为 191.49 对 79.75，B 为 172.03 对 164.98。该模式说明本文的主要证据并非仅由上尾偶然值驱动；但 3/5 与 4/5 也明确要求避免“每个 seed 均提升”的表述。

**表3｜主比较的 cohort 级配对与下尾摘要。**

| Cohort | DRTP−UTR 的平均 ΔJ_perturbed | 正向配对 seed | DRTP 最差 seed−UTR 最差 seed | 允许的解释 |
|---|---:|---:|---:|---|
| A | +39.64 | 3/5 | +111.73 | cohort 级中心趋势和观测下尾均有利 |
| B | +23.15 | 4/5 | +7.05 | 独立 cohort 中仍为正向，但优势幅度较小 |

### 6.3 任务收益与终局行为并非同一指标

在两个 cohort 中，DRTP 的平均成功率均高于 UTR，超时率均更低。A cohort 的碰撞率从 0.003 上升至 0.009；B cohort 两种方法的平均碰撞率均为 0。因此，回报和 timeout 的改善不能被改写为“全面安全提升”。本文将更准确地把结果描述为：在本任务奖励与终止合同下，DRTP 的较高扰动回报与更高成功率、较低超时相伴出现，但碰撞端点需要独立阅读。

### 6.4 训练排除的结构条件带提供了有限的泛化支撑

主比较的七个条件属于训练支持集合，因而不能被重命名为严格 OOD。为检验结果是否仅限于这一支持集合，研究在训练完成后针对两批冻结 10M checkpoint 执行训练未读取的 held-out tape；该 tape 在运行前冻结，不参与重新训练或 checkpoint 选择。其 primary structural 条件包括 Scout 节点故障、对称最长边删除、有向最长边删除及 Scout 节点故障与边删除的复合；两个仅改变 relay 故障时机或时长的 parameter 条件被保留作诊断，不被作为 structural OOD 结论的依据。

表4显示，在四个预先冻结的 structural 条件聚合上，DRTP 相对 UTR 的 cohort 平均回报差在 A/B 中分别为 +22.77 与 +11.96；按每个训练 seed 的最差 structural 条件汇总后，差值分别为 +32.48 与 +20.03。这些结果将主比较的结论延伸到所定义的训练排除结构条件带，但仍不足以证明对任意未见拓扑的普适泛化。可靠性端点也并非完全同向：A 中 DRTP 的 structural timeout 更低，而 B 中 timeout 更高、collision 更低。因此，该部分的正确定位是预先冻结条件带上的分层经验支持，而不是新的训练重复或一般化保证。

**表4｜训练排除 structural 条件带上的固定 endpoint 汇总。** 所有数值均按 cohort 内五个训练 seed 汇总；`J worst` 是每个 seed 在四个 structural 条件中最低回报后再作 cohort 汇总，不能按 episode 解释为独立重复。

| Cohort | 方法 | structural J mean | structural J worst | structural timeout | structural collision |
|---|---|---:|---:|---:|---:|
| A | UTR | 178.31 | 151.35 | 0.748 | 0.0030 |
| A | DRTP | 201.08 | 183.83 | 0.647 | 0.0055 |
| B | UTR | 179.38 | 149.03 | 0.628 | 0.0015 |
| B | DRTP | 191.34 | 169.06 | 0.689 | 0.0000 |

### 6.5 与 PLR-style 外部比较的定位：竞争性而非全面支配

PLR-style 采用与 A/B 对应的训练种子、10M 预算、任务环境、网络维度和 PPO 超参数从零开始训练；它是定位“通用优先级式暴露调整”而非替代主要因果对照的外部比较。表5中，A cohort 的 DRTP 平均扰动回报为 216.66，高于 PLR-style 的 203.87，且 DRTP timeout 更低；B cohort 则由 PLR-style 获得更高的平均扰动回报（220.03 对 210.34），同时 DRTP 的 success 更高、timeout 更低。由此，证据并不支持 DRTP 对通用 prioritization 的跨 cohort 全面支配；它支持的是 DRTP 在这一外部比较中具有竞争力，并呈现由拓扑语义暴露和通用优先级各自可能影响的性能—可靠性权衡。

**表5｜PLR-style 外部定位比较。** A/B 分层报告；UTR 与 DRTP 为原始冻结 endpoint，PLR-style 为匹配预算下从零训练的外部比较臂。

| Cohort | 方法 | J_perturbed 均值 | 中位数 | 最差 seed | 超时率 | 碰撞率 |
|---|---|---:|---:|---:|---:|---:|
| A | DRTP | 216.66 | 223.82 | 191.49 | 0.597 | 0.009 |
| A | PLR-style | 203.87 | 214.02 | 142.02 | 0.742 | 0.014 |
| B | DRTP | 210.34 | 218.78 | 172.03 | 0.602 | 0.000 |
| B | PLR-style | 220.03 | 218.22 | 201.06 | 0.699 | 0.000 |

### 6.6 方法选择与采样器遥测的证据角色

最初冻结合同同时保留 EGTR 与 Global-Anchored EGTR 作为候选 arm。A/B 完成后的方法选择文件将 Original DRTP 指定为 principal method：EGTR 在 A 的领先次序未在 B 保持，而 Global-Anchored EGTR 未在两批中维持相对于 UTR 或 DRTP 的一致优势。该选择过程说明主方法并非根据单一 cohort 的最高值事后替换。

DRTP 的训练日志记录每个故障组的权重和实际暴露计数，因此可直接审计 sampler 是否偏离 UTR 的均匀故障组质量。该遥测用于验证“训练暴露确实被重分配”这一实施事实；它不单独识别权重变化如何改变策略内部表示、信息路径利用或泛化机制。后续关于 q 演化与拓扑难度的图表只能在其源日志、训练合同和统计单位均核对后作为机制描述性证据加入。

## 7 讨论

### 7.1 训练暴露塑形为何是可检验的干预

DRTP 的价值不在于增加训练条件数量，而在于在固定条件集合内重新安排训练预算。UTR 与 DRTP 接触相同名义工况和相同六类故障组，拥有相同网络、奖励和 PPO 更新；因此，A/B 中观察到的差异不能归因于“DRTP 看过而 UTR 未看过”的拓扑条件。该设计将经验结论限定为有界自适应暴露相对于均匀暴露的合同内增量，而不把它外推为所有鲁棒 MARL 或所有非均匀分布的排序。

### 7.2 双 cohort 证据支持的范围

两个冻结 cohort 都给出正的扰动回报平均差，并且观测下尾与 timeout 行为具有有利方向。这一重复性使本文能够将 DRTP 写成在所评估拓扑故障设置下获得重复 cohort 级收益的方法。与此同时，A 的 3/5 与 B 的 4/5 配对方向表明训练初始化仍会影响单次运行结果；结论的合理边界是 cohort 级重复收益，而不是逐 seed 保证。

### 7.3 可靠性与安全性应当并列而非相互替代

强化学习任务分数、成功、超时和碰撞刻画不同的终局行为。DRTP 在两批中降低 timeout，但 A 中存在小幅碰撞率上升。这并不取消回报和 timeout 证据，也不允许将其包装为无条件安全优势。后续论文图表将对每个 endpoint 采用相同的 cohort 分层和独立种子标注，避免以 episode 数夸大训练重复。

### 7.4 支撑性证据如何扩展、而不替代主比较

预先冻结的结构条件评价表明，主比较的结果并未完全局限于训练支持集合；不过该证据只覆盖明确写入 tape 的结构变换，且 B 中 timeout 的方向提醒我们不能把回报差写成全面可靠性优势。PLR-style 结果则表明通用优先级式分配同样具有价值：A 的排序有利于 DRTP，B 的回报排序有利于 PLR-style，而 DRTP 在 B 保持更好的 success/timeout 组合。因此，本文不以外部方法替换 UTR—DRTP 的主要受控对照，也不把外部比较写成单向胜负。

项目早期的队列、机制审计和候选稳定化尝试保留在可追溯归档中，但它们服务于方法演变与风险背景，而非当前论文的正式因果结论。6-UAV v2、全因子消融和运行开销只有在各自合同完成并接受来源审计后才可扩展本文的适用范围。

### 7.5 局限性

本文研究限于冻结的三无人机轻量 3DOF 仿真、预定义的中继故障组和五种子 cohort。方法不提供一般分布鲁棒、最坏情况优化或实飞可靠性保证。当前主比较只识别 DRTP 相对于均匀暴露的增量，尚不单独证明自适应更新优于任何静态非均匀分配，亦不证明拓扑语义与自适应更新的因果必要性。跨规模、外部优先级比较与运行成本需以各自经过审计的结果补强。

## 8 结论

本文研究了中继节点故障导致合法信息路径和任务支撑关系重构时的异构无人机协同训练。DRTP 保持单图 MAPPO、PPO、奖励、观测、动作、执行期信息边界和故障支持集合不变，仅对冻结故障组进行有界自适应训练暴露分配。两个独立、训练前冻结的 10M cohort 均显示 DRTP 相对匹配 UTR 具有更高的扰动条件 cohort 平均回报，并伴随更有利的观测下尾和 timeout 行为。预先冻结的训练排除 structural 条件带也在 A/B 中给出正的 cohort 平均回报与下尾差，但可靠性端点仍需分层阅读；PLR-style 比较进一步将 DRTP 定位为具有竞争力、而非跨 cohort 全面支配通用优先级式采样的方法。该证据支持 DRTP 在所评估拓扑故障设置下的 cohort 级训练暴露塑形价值；它不支持每个 seed 均提升、全面安全优越、普适泛化或执行期信息恢复的更强主张。

## 附录A 最终证据的可追溯性

论文主结果对应 A cohort（78011--78015）与 B cohort（78021--78025）的终点评价。两批均使用独立训练种子、独立 endpoint tape 和最终 checkpoint；训练种子是唯一独立统计单位。当前 principal-method 选择、归档 SHA256 与允许/禁止的证据解释由 `DRTP_FINAL_EVIDENCE_REGISTER_20260908.md` 统一记录。早期历史队列不计入本文的确认样本量。


## 参考文献

[1] Yu C, Velu A, Vinitsky E, et al. The Surprising Effectiveness of PPO in Cooperative Multi-Agent Games. *Advances in Neural Information Processing Systems*, 2022, 35. DOI: 10.52202/068431-1787.

[2] Veličković P, Cucurull G, Casanova A, et al. Graph Attention Networks. *International Conference on Learning Representations*, 2018.

[3] Lou X, Zhang J, Norman T J, et al. TAPE: Leveraging Agent Topology for Cooperative Multi-Agent Policy Gradient. *Proceedings of the AAAI Conference on Artificial Intelligence*, 2024, 38(16): 17496--17504. DOI: 10.1609/aaai.v38i16.29699.

[4] Li S, Wu Y, Cui X, et al. Robust Multi-Agent Reinforcement Learning via Minimax Deep Deterministic Policy Gradient. *Proceedings of the AAAI Conference on Artificial Intelligence*, 2019, 33(1): 4213--4220. DOI: 10.1609/aaai.v33i01.33014213.

[5] Liu Z, Bai Q, Blanchet J, et al. Distributionally Robust Q-Learning. *Proceedings of the 39th International Conference on Machine Learning*, 2022, 162: 13623--13643.

[6] Zhao B, Huo M, Li Z, et al. Graph-based multi-agent reinforcement learning for collaborative search and tracking of multiple UAVs. *Chinese Journal of Aeronautics*, 2025, 38(3): 103214. DOI: 10.1016/j.cja.2024.08.045.

[7] Zhao B, Huo M, Li Z, et al. Graph-based multi-agent reinforcement learning for large-scale UAVs swarm system control. *Aerospace Science and Technology*, 2024, 150: 109166. DOI: 10.1016/j.ast.2024.109166.

[8] Lv Z, Xiao L, Du Y, et al. Multi-Agent Reinforcement Learning Based UAV Swarm Communications Against Jamming. *IEEE Transactions on Wireless Communications*, 2023, 22(12): 9063--9075. DOI: 10.1109/TWC.2023.3268082.

[9] Bai H, Wang H, He R, et al. Multi-hop UAV relay covert communication: A multi-agent reinforcement learning approach. *Chinese Journal of Aeronautics*, 2025, 38(10): 103440. DOI: 10.1016/j.cja.2025.103440.

[10] Schulman J, Wolski F, Dhariwal P, et al. Proximal Policy Optimization Algorithms. arXiv:1707.06347, 2017. DOI: 10.48550/arXiv.1707.06347.

[11] Sagawa S, Koh P W, Hashimoto T B, Liang P. Distributionally Robust Neural Networks for Group Shifts: On the Importance of Regularization for Worst-Case Generalization. *International Conference on Learning Representations*, 2020.

[12] Mehta B, Diaz M, Golemo F, et al. Active Domain Randomization. *Conference on Robot Learning*, 2020, 155: 1162--1176.

[13] Narvekar S, Peng B, Leonetti M, et al. Curriculum Learning for Reinforcement Learning Domains: A Framework and Survey. *Journal of Machine Learning Research*, 2020, 21(181): 1--50.

[14] Lowe R, Wu Y, Tamar A, et al. Multi-Agent Actor-Critic for Mixed Cooperative-Competitive Environments. *Advances in Neural Information Processing Systems*, 2017, 30. arXiv:1706.02275.

[15] Luo J, Wang Z, Xia M, et al. Path Planning for UAV Communication Networks: Related Technologies, Solutions, and Opportunities. *ACM Computing Surveys*, 2023, 55(9): 1--37. DOI: 10.1145/3560261.

[16] Xiao H, Yang Y, Yu D, et al. 3D Self-Triggered-Organized Communication Topology Based UAV Swarm Consensus System With Distributed Extended State Observer. *IEEE Transactions on Network Science and Engineering*, 2025, 12(5): 3985--4000. DOI: 10.1109/TNSE.2025.3567462.

[17] Foerster J N, Assael I A, de Freitas N, Whiteson S. Learning to Communicate with Deep Multi-Agent Reinforcement Learning. *Advances in Neural Information Processing Systems*, 2016, 29: 2137--2145.

[18] Sukhbaatar S, Szlam A, Fergus R. Learning Multiagent Communication with Backpropagation. *Advances in Neural Information Processing Systems*, 2016, 29.

[19] Jiang J, Lu Z. Learning Attentional Communication for Multi-Agent Cooperation. *Advances in Neural Information Processing Systems*, 2018, 31.

[20] Das A, Gervet T, Romoff J, et al. TarMAC: Targeted Multi-Agent Communication. *Proceedings of the 36th International Conference on Machine Learning*, 2019, 97: 1538--1546.

[21] Iqbal S, Sha F. Actor-Attention-Critic for Multi-Agent Reinforcement Learning. *Proceedings of the 36th International Conference on Machine Learning*, 2019, 97: 2961--2970.

[22] Jiang M, Grefenstette E, Rocktäschel T. Prioritized Level Replay. *Proceedings of the 38th International Conference on Machine Learning*, 2021, 139: 4940--4950.

[23] Dennis M, Jaques N, Vinitsky E, et al. Emergent Complexity and Zero-Shot Transfer via Unsupervised Environment Design. *Advances in Neural Information Processing Systems*, 2020, 33.

[24] Jiang M, Dennis M, Parker-Holder J, et al. Grounding Aleatoric Uncertainty for Unsupervised Environment Design. *Advances in Neural Information Processing Systems*, 2022, 35. DOI: 10.52202/068431-2382.

[25] Huang P, Xu M, Zhu J, et al. Curriculum Reinforcement Learning using Optimal Transport via Gradual Domain Adaptation. *Advances in Neural Information Processing Systems*, 2022, 35. DOI: 10.52202/068431-0774.

[26] Zhong R, Zhang D, Schäfer L, et al. Robust On-Policy Sampling for Data-Efficient Policy Evaluation in Reinforcement Learning. *Advances in Neural Information Processing Systems*, 2022, 35. DOI: 10.52202/068431-2709.

[27] Yin Z, Lin Y, Zhang Y, et al. Collaborative Multiagent Reinforcement Learning Aided Resource Allocation for UAV Anti-Jamming Communication. *IEEE Internet of Things Journal*, 2022, 9(23): 23995--24008. DOI: 10.1109/JIOT.2022.3188833.

[28] Li Z, Lu Y, Li X, et al. UAV Networks Against Multiple Maneuvering Smart Jamming With Knowledge-Based Reinforcement Learning. *IEEE Internet of Things Journal*, 2021, 8(15): 12289--12310. DOI: 10.1109/JIOT.2021.3062659.

[29] Zhang J, Wang T, Wang J, et al. Multi-UAV Collaborative Surveillance Network Recovery via Deep Reinforcement Learning. *IEEE Internet of Things Journal*, 2024, 11(21): 34528--34540. DOI: 10.1109/JIOT.2024.3446878.

[30] Mondal A, Mishra D, Alexandropoulos G C, et al. Multi-Agent Reinforcement Learning for Offloading Cellular Communications with Cooperating UAVs. *IEEE Transactions on Aerospace and Electronic Systems*, 2025, 61(4): 9344--9358. DOI: 10.1109/TAES.2025.3554150.

