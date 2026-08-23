# 中继节点故障下异构多无人机拓扑鲁棒协同：分布鲁棒拓扑扰动训练与种子可靠性

> **稿件状态：** 中文完整工作稿 v0.2。问题建模、方法、实验协议与讨论边界已写入；正式 seeds 2301–2305 的 10M 结果尚在训练，所有 `[FORMAL RESULT PENDING]` 位置必须由冻结汇总产物填充，禁止人工挑选 checkpoint 或 seed。

## 摘要

异构多无人机协同依赖由角色、感知、通信与任务支持共同形成的动态关系结构。中继节点故障并不必然造成完全信息中断；在合法直连仍然存在时，它仍可能使通信路径由中继转发重构为直接传递，并改变任务支持来源与协同几何。针对这一结构性扰动，本文构建中继故障下的拓扑鲁棒多智能体协同问题，并提出分布鲁棒拓扑扰动单图 MAPPO（Distributionally Robust Topology-Perturbation Single-Graph MAPPO，DRTP-SG-MAPPO）。该方法保持 116,728 参数的 Single-Graph MAPPO 策略、PPO 目标、奖励和执行信息边界不变，在固定 50% nominal exposure anchor 的条件下，根据各拓扑扰动组相对 nominal 的回报差异，对六类故障组进行有界自适应加权。为隔离自适应加权本身的作用，本文采用参数量、拓扑组、训练预算和评估协议完全匹配的均匀拓扑随机化基线 UTR-SG-MAPPO。正式实验使用五个预先冻结的配对训练种子、统一 10M 训练预算以及覆盖 nominal、F0、timing、duration 和 compound 条件的共同 evaluation tape，并以训练种子作为独立统计单位，同时报告任务得分、安全性、最坏 OOD 表现、故障触发有效性和不利种子。`[FORMAL RESULT PENDING：填入 J_F0、J_OOD_mean、J_OOD_worst 的 mean/median paired effect、win count、catastrophic seed 数量与安全结论。]` 本文的结论限于冻结的三无人机仿真任务，不主张信息恢复、通用拓扑泛化或对随机初始化的稳定优越性。

## 关键词

异构多无人机；多智能体强化学习；通信拓扑；中继节点故障；拓扑扰动训练；分布鲁棒学习；训练种子可靠性

## 1 引言

### 1.1 应用背景与结构性协同问题

异构无人机编队通常由具有不同感知、通信和任务执行能力的平台共同完成任务。本文关注由 Scout、Relay 和 Attacker 组成的三机协同系统：Scout 负责获得目标信息，Relay 提供潜在的多跳通信支持，Attacker 利用合法获得的信息形成攻击窗口。此类系统的任务能力不仅取决于单机运动学，还取决于信息能否沿合法的感知、通信和任务支持关系传递。因此，协同策略面对的是一个随角色状态和空间几何变化的通信–任务图，而不是三个彼此独立的控制器。

中继节点故障对该图施加的是结构性扰动。冻结环境中的 Relay failure 会使与 Relay 相连的通信边在规定时间窗内失效，但在物理规则允许时，Scout 到 Attacker 的直接边仍可保持合法。既有机制审计显示，故障窗口内的信息路径可由 `0–1–2` 重构为 `0–2`，任务得分同时发生下降。这一现象不能被准确描述为“完全失联后恢复信息”，因为合法直连信息并未必消失；更合适的问题是：策略能否在路径组成和任务支持关系改变后维持任务能力。

### 1.2 现有研究缺口

图结构 MARL 已经证明显式表示智能体关系有助于协同决策，通信感知型 UAV MARL 也研究了连通性、通信资源、轨迹和中继选择等问题 `[R1–R2，待逐条核验]`。鲁棒 MARL 与分布鲁棒强化学习进一步从对手变化、模型不确定性或环境分布变化角度研究策略性能 `[R3–R5，待逐条核验]`。这些工作构成本文的直接知识基础，但尚不能替代本文的受控比较：本任务同时要求固定异构角色、合法去中心化信息边界、明确的 Relay failure 语义以及 timing、duration 和 compound 拓扑扰动。

另一个缺口来自训练分布。若所有故障组始终以相同概率采样，训练可能在容易条件上重复消耗预算，而对当前策略更困难的拓扑扰动投入不足。相反，如果采样权重完全由历史回报自由驱动，又可能形成对训练种子敏感的反馈。因而需要检验一个受约束的问题：在保持 nominal exposure、策略网络和 PPO 不变的前提下，有界自适应故障组加权能否改善平均与最坏拓扑鲁棒性，并且这种收益在不同训练种子上是否可靠。

### 1.3 本文方法与研究问题

本文以 116,728 参数的 matched Single-Graph MAPPO 为共同策略主干。均匀拓扑随机化方法 UTR-SG-MAPPO 固定使用 50% nominal episode，并将其余 50% 均匀分配给六个故障组。DRTP-SG-MAPPO 保持相同 nominal anchor，只根据组回报相对 nominal competence 的差异更新有界权重。两种方法具有相同的网络、PPO、环境、奖励、拓扑组、训练预算和评估 tape，唯一预期差异是 uniform weighting 与 adaptive weighting。

围绕这一设计，本文回答三个问题。第一，Relay failure 是否确实引起合法拓扑与路径组成重构，而不是仅仅制造一个抽象噪声标签？第二，在同等容量和暴露范围下，自适应扰动加权能否提高 F0、OOD mean 和 OOD worst 表现，同时保持 nominal competence 与安全边界？第三，平均收益是否能跨训练种子保持，还是会出现需要在主文中报告的严重反转？

### 1.4 贡献

本文贡献概括如下。

1. 构建一个面向 Relay-node-induced topology/path reconfiguration 的异构 UAV 鲁棒协同问题。问题定义保留合法直连路径和严格 actor information boundary，避免将拓扑重构错误表述为完全信息中断或信息恢复。
2. 提出 DRTP-SG-MAPPO。该方法不改变网络、PPO、奖励或执行期输入，仅在固定 nominal anchor 下对六类预定义拓扑扰动实施有界自适应加权，从而将方法差异集中于训练分布。
3. 建立参数与暴露范围完全匹配的 UTR–DRTP 主消融，并通过五个预注册配对训练种子、统一 10M final checkpoint、共同 12-condition tape、OOD worst、安全指标与 risk-set trigger validity 评价自适应加权。
4. 将训练可靠性纳入主结论。所有 seed 均被保留，历史不利 seed 和正式实验中的潜在 catastrophic seed 不被作为“异常值”删除，平均性能与最坏训练结果并列报告。

## 2 相关工作

### 2.1 图结构多智能体强化学习

图神经网络为多智能体系统提供了与智能体数量和关系结构相适配的表示方式。图注意力与拓扑感知策略梯度方法通常根据邻接关系聚合邻居信息，使策略能够利用交互结构，而不必将所有智能体状态拼接为固定长度向量 `[R1–R2，待核验]`。这些研究说明“使用图”本身已不能构成充分创新。本文不提出新的图编码器，而是固定同一个 Single-Graph actor/critic，将研究焦点转向拓扑扰动训练分布。

### 2.2 鲁棒与分布变化下的多智能体学习

鲁棒 MARL 研究涵盖对手策略变化、环境动力学不确定性以及最坏情况优化等路线 `[R3，待核验]`。分布鲁棒强化学习则通过不确定集合或对训练分布重新加权来提高分布偏移下的性能 `[R4–R5，待核验]`。DRTP 与这些思想存在明确知识继承关系，但其贡献边界更窄：本文不建立一般 DRMDP 理论，也不声称求得严格最坏情况策略，而是在冻结的六类拓扑扰动组上实现可复现的有界经验加权。

### 2.3 通信受限与故障条件下的多无人机协同

现有 UAV relay/MARL 工作常围绕连通性恢复、中继部署、通信功率、隐蔽通信或轨迹规划构建目标 `[R6–R7，待核验]`。本文研究的输出不是通信吞吐量或网络连通度本身，而是 Relay failure 引起路径与任务支持组成变化后，异构团队的任务得分和安全表现。因此，相关方法具有研究定位价值，但在动作空间、学习器、奖励和 actor information boundary 上并非可直接迁移的公平基线。

### 2.4 本文定位与对照边界

本文的核心经验比较是 UTR-SG-MAPPO 与 DRTP-SG-MAPPO。两者接触相同的七个训练组，具有相同参数量、PPO、环境、奖励、训练预算和 evaluation tape。该设计回答的是“在相同拓扑扰动集合上，自适应加权是否优于均匀加权”，而不是“DRTP 是否优于所有鲁棒 MARL”。对 TAPE、M3DDPG 和相关 UAV relay 方法的审计表明，它们需要改变当前任务或学习合同，因而本文将其用于知识定位，不制造表面公平、实质不可比的 comparator zoo。

## 3 问题建模

### 3.1 异构角色与 3DOF 环境

环境包含三架蓝方 UAV 和一个目标，蓝方角色依次为 Scout（智能体 0）、Relay（智能体 1）和 Attacker（智能体 2）。仿真采用轻量 3DOF 运动学，时间步长为 1 s，最大时域为 260 steps，水平空间半径为 50 km，高度范围为 1–9 km。每架蓝方 UAV 从 27 个离散动作中选择转向、爬升和加减速指令的组合。不同角色具有冻结的速度、加速度、转弯、爬升、雷达、通信和攻击几何参数。

每个 actor 的局部观测包含自身位置、速度、航向、航迹倾角、合法目标相对信息、探测状态、局部攻击窗口、能量、角色、入向连通度、消息 age 和目标缓存置信度等 34 维特征。严格目标感知与 agent target-information bottleneck 同时开启：未探测目标且未合法接收新鲜缓存的智能体不能通过共享图获得真实目标状态。集中 critic 仅用于 CTDE 训练，不向 actor 增加执行期信息。

### 3.2 通信–任务图与合法信息边界

记时刻 (t) 的图为

\[
G_t=(V,E_t,X_t,Z_t),
\]

其中 (V) 包含三架 UAV 与目标节点，(X_t) 和 (Z_t) 分别表示节点和边特征。邻接矩阵采用 receiver-row 约定：

\[
A_t[i,j]=1
\]

表示接收方 (i) 当前能够合法使用来自发送方 (j) 的关系。Perception edge 仅由冻结感知模型产生；Communication edge 同时满足物理通信距离、节点状态和通信实现；Task-support edge 由已合法交付的信息与活跃任务支持状态产生，不构成额外隐藏信息通道。Single-Graph encoder 使用这些合法关系的 union adjacency，但 actor 不接收 failure label、最短路、未来链路或 simulator ground truth。

### 3.3 Relay failure 与路径重构

Relay failure 在冻结起始时刻 (t_f) 和持续时间 (d_f) 内禁用 Relay 的感知、发送与接收能力，并移除其相关通信边。canonical F0 定义为

\[
t_f=44,\qquad d_f=80.
\]

故障前，合法信息可能经 `Scout→Relay→Attacker` 传递；故障后，若物理规则允许，`Scout→Attacker` 可继续作为合法直连路径。故障事件因此表现为

\[
0\rightarrow1\rightarrow2
\quad\longrightarrow\quad
0\rightarrow2,
\]

而不是必然的信息全失。本文将需要策略适应的对象定义为 communication-path composition、task-support source 和 coordination geometry 的变化。

### 3.4 Nominal、F0 与 OOD 条件

Nominal 条件不注入 Relay failure。除 F0 外，训练与正式评价覆盖以下扰动组：early timing `TE={(28,80),(36,80)}`、late timing `TL={(52,80),(60,80)}`、short duration `DS={(44,40),(44,60)}`、long duration `DL={(44,100),(44,120)}` 和 compound `CP={(28,120),(60,120)}`。括号分别表示 onset 和 duration。正式 evaluation tape 对全部方法和 seed 使用相同的 100 个 base episode IDs，并在 12 个条件间复用这些 ID，以减少场景差异对配对比较的干扰。

### 3.5 性能、安全与技术有效性 estimands

记某条件 (c) 下的平均 episode mission score 为 (J_c)。本文报告

\[
J_{\mathrm{nominal}},\qquad J_{F0},
\]

以及十个 OOD 条件的

\[
J_{\mathrm{OOD,mean}}=\frac{1}{10}\sum_{c\in\mathcal C_{\mathrm{OOD}}}J_c,
\qquad
J_{\mathrm{OOD,worst}}=\min_{c\in\mathcal C_{\mathrm{OOD}}}J_c.
\]

配对退化量定义为

\[
\Delta J_c=J_{\mathrm{nominal}}-J_c.
\]

任务得分之外，本文报告 collision、timeout、constraint violation、episode length、pre-trigger collision 和 survival-to-onset fraction。故障触发技术有效性只在 scheduled onset 前仍存活的 risk set (R_c) 上计算：

\[
V_{\mathrm{trigger},c}=
\frac{\#\{\text{在 }R_c\text{ 中正确触发故障的 episodes}\}}
{|R_c|}.
\]

在 onset 前合法碰撞终止的 episode 不属于 evaluator defect，也不会从 unconditional return 或 safety 汇总中删除。

## 4 方法

### 4.1 Matched Single-Graph MAPPO

两种方法共用 Single-Graph MAPPO。对智能体 (i)，actor 根据局部观测和合法图表示产生离散动作分布：

\[
a_{i,t}\sim\pi_\theta(a_{i,t}\mid o_{i,t},G_{i,t}).
\]

节点特征经线性编码后进入两层共享图注意力模块，图表示与本地观测表示融合后输出 27 维动作 logits。集中 critic 在训练期估计 (V_\phi(s_t))。训练使用标准 clipped PPO 与 GAE：学习率 (3\times10^{-4})、折扣因子 0.99、GAE 系数 0.95、clip 0.2、entropy 系数 0.01、value 系数 0.5、最大梯度范数 0.5，每批执行 4 个 PPO epochs。UTR 与 DRTP 的 trainable parameter count 均为 116,728。

### 4.2 Uniform Topology Randomization

训练组集合为

\[
\mathcal G=\{N,F0,TE,TL,DS,DL,CP\}.
\]

UTR 固定 nominal mass：

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

### 4.3 DRTP bounded adaptive weighting

DRTP 的概念目标为

\[
\max_\theta\left[
p_NJ_N(\theta)+(1-p_N)
\min_{q\in\mathcal Q}\sum_{k\in\mathcal F}q_kJ_k(\theta)
\right],
\]

其中有界分布集合为

\[
\mathcal Q=\left\{q\in\Delta^6:0.05\le q_k\le0.35\right\}.
\]

该目标不改变 PPO loss，而是通过训练 episode sampling 近似内层分布。设 adaptation boundary (u) 前收集到组 (k) 的 completed-episode mean return 为 \(\widehat J_{k,u}\)。若该组在窗口内被观测，则其 EMA 更新为

\[
\bar J_{k,u}=(1-\kappa)\bar J_{k,u-1}+\kappa\widehat J_{k,u};
\]

未观测组的 EMA 保持不变。Nominal EMA 采用相同规则。相对难度定义为

\[
d_{k,u}=\operatorname{clip}\!\left(
\frac{\bar J_{N,u}-\bar J_{k,u}}
{\max(|\bar J_{N,u}|,\epsilon)},0,d_{\max}
\right),
\]

并通过去均值得到

\[
\tilde d_{k,u}=d_{k,u}-\frac{1}{6}\sum_{j\in\mathcal F}d_{j,u}.
\]

指数更新候选为

\[
\tilde q_{k,u+1}=
\frac{q_{k,u}\exp(\eta\tilde d_{k,u})}
{\sum_{j\in\mathcal F}q_{j,u}\exp(\eta\tilde d_{j,u})},
\]

最终权重经过平滑与有界单纯形投影：

\[
q_{u+1}=\Pi_{\mathcal Q}\left[(1-\beta)q_u+\beta\tilde q_{u+1}\right].
\]

冻结超参数为：初始 (q_k=1/6)，前 128 updates 均匀 warm-up，之后每 32 updates 适配一次，\(\kappa=0.20\)、\(\eta=1.00\)、\(\beta=0.50\)、\(d_{\max}=2.00\)、\(\epsilon=10^{-8}\)。

### 4.4 Nominal competence anchor

DRTP 中存在两种不同的 anchor。第一，(p_N=0.50) 固定了 nominal exposure，避免自适应器将全部训练质量转移到故障条件。第二，\(\bar J_N\) 作为 competence reference，使 difficulty 表示某故障组相对 nominal 的任务差距。二者均属于训练 sampler，不是辅助 loss，也不进入 actor/critic。

### 4.5 训练流程、复杂度与信息边界

每次环境 reset 时，sampler 先以 0.5 概率选择 nominal；否则根据 (q) 选择故障组，再在组内均匀选择 onset/duration。UTR 的 (q) 固定，DRTP 的 (q) 仅在 adaptation boundary 更新。group label、onset、duration、EMA、difficulty 和 (q) 只存在于训练 bookkeeping 和日志中。评价阶段不实例化自适应 sampler。

DRTP 不增加 trainable parameter，也不改变 inference graph。其附加计算来自按组累计 episode return、EMA 更新和六维有界投影；因此论文只主张“参数量相同且无 inference-time 模块”，不在缺少共同硬件日志的情况下声称 wall-clock 或显存优势。

## 5 实验协议

### 5.1 正式方法与公平性合同

正式实验仅比较 UTR-SG-MAPPO 和 DRTP-SG-MAPPO。每个方法使用 seeds 2301–2305，共十条 from-scratch strict-continuous 轨迹。每条轨迹训练 39,063 updates，采用 4 个并行环境和 64-step rollout，对应 10,000,128 environment steps。所有方法使用相同的网络、PPO、S2 environment、reward、七个 topology groups、50% nominal anchor、运行时状态持久化和 checkpoint 规则。

最终比较只使用共同 10M final checkpoint。0.5M 间隔 milestone 仅用于学习曲线和中断恢复，不允许 best-checkpoint promotion、early stopping、seed exclusion 或性能驱动重跑。

### 5.2 正式 evaluation tape

正式 tape 使用 episode IDs 490000–490099，在 nominal、F0、四个 timing、四个 duration 和两个 compound 条件间复用同一组 base IDs。每个 method×seed×condition 评价 100 episodes，总计 12,000 条 raw evaluation records。tape 在看到正式 performance 前生成并冻结，其 manifest/hash 必须与汇总脚本一致。

### 5.3 历史证据与正式证据分层

历史 development 3M（seeds 1901/1902）与 held-out 10M（seeds 2001/2002/2003）保留为 provenance 和 reliability background。它们的训练预算与评价合同不同，不能与正式 seeds 2301–2305 合并成一个同质 (n=10) 实验。历史 development `NO-GO`、held-out `FAIL`、seed1902 weakness 和 seed2002 catastrophic reversal 均永久保留。

### 5.4 指标与统计单位

独立统计单位是配对 training seed（正式实验 (n=5)），而不是 evaluation episode。对 (J_{\mathrm{nominal}})、(J_{F0})、(J_{\mathrm{OOD,mean}}) 和 (J_{\mathrm{OOD,worst}})，本文报告 UTR 与 DRTP 绝对值、每 seed 的 DRTP−UTR difference、paired ratio、mean、median、sample SD、IQR、MAD、win count、best/worst difference。若报告 bootstrap interval，必须明确其为小样本描述性区间，不能用 episode-pooled p-value 扩大方法优越性结论。

### 5.5 Safety、exposure 与 catastrophic rule

Safety 指标包括 collision、timeout 和 constraint violation。所有 scheduled episodes 均保留在 unconditional return 和 safety 中。pre-trigger collision 单独报告；技术 trigger validity 在 alive-at-onset risk set 上计算。

正式合同继承预先冻结的 catastrophic definition。若同一 paired seed 满足以下任一组合，则 DRTP seed 被标记为 catastrophic：

\[
\frac{J_{F0}^{D}}{J_{F0}^{U}}<0.70
\quad\text{且}\quad
\frac{J_{\mathrm{OOD,worst}}^{D}}{J_{\mathrm{OOD,worst}}^{U}}<0.85,
\]

或

\[
\frac{J_{\mathrm{OOD,worst}}^{D}}{J_{\mathrm{OOD,worst}}^{U}}<0.70
\quad\text{且}\quad
\frac{J_{F0}^{D}}{J_{F0}^{U}}<0.85.
\]

此外，若 timeout 增量大于 0.20，且 F0 或 OOD-worst ratio 小于 0.85，也判为 catastrophic。该阈值在正式 seeds 训练前冻结，不能根据结果修改。

## 6 结果

### 6.1 Relay failure 引起合法拓扑与路径重构

冻结的 S1/S2 机制审计表明，暴露于故障窗口后，两条 Relay 通信边失效，而合法 `Scout→Attacker` direct edge 与配对 nominal 轨迹相比保持可用。Attacker 的缓存路径由 `0–1–2` 转为 `0–2`。与此同时，已有 paired diagnostic 中 failure mission score 低于 nominal。该证据支持

\[
\text{Relay failure}
\rightarrow
\text{topology/path reconfiguration}
\rightarrow
\text{mission degradation},
\]

但不支持“合法信息必然减少”或“DRTP 恢复丢失信息”的叙述。

### 6.2 正式五种子绝对结果

`[FORMAL RESULT PENDING：从 DRTP_UTR_Q2_FORMAL_DECISION.json 的 pooled 字段填入 UTR/DRTP 的 J_nominal、J_F0、J_OOD_mean、J_OOD_worst、collision、timeout、constraint。绝对值必须先于差值。]`

主表预留如下：

| Method | Params | (J_{nominal}) | (J_{F0}) | (J_{OOD,mean}) | (J_{OOD,worst}) | Collision | Timeout | Constraint |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| UTR-SG-MAPPO | 116,728 | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` |
| DRTP-SG-MAPPO | 116,728 | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` |

### 6.3 Paired seed effects 与 reliability

`[FORMAL RESULT PENDING：逐 seed 填入 2301–2305 的四个 primary differences、三个 robustness win counts、mean、median、SD、IQR、MAD、worst 与 catastrophic flag。所有 seed 必须显示。]`

| Seed | ΔNominal | ΔF0 | ΔOOD mean | ΔOOD worst | ΔCollision | ΔTimeout | Catastrophic |
|---:|---:|---:|---:|---:|---:|---:|---|
| 2301 | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` |
| 2302 | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` |
| 2303 | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` |
| 2304 | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` |
| 2305 | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` | `[PENDING]` |

结果段必须根据冻结 verdict 选择措辞：

- `PASS_SEED_SENSITIVE`：仅可表述为“正式证据支持正向 mean/median center 和至少 3/5 paired directions，同时保留最多一个 catastrophic seed 的 seed-sensitive boundary”。
- `LIMITATION_ONLY`：不得声称 prospective superiority；DRTP 仅作为历史高收益、可靠性受限的方法讨论。
- `FAIL_DEMOTE_DRTP`：DRTP 从主方法降级，论文主线转为 relay-failure topology robustness 与 matched UTR reference。
- `TECHNICAL_INVALID`：只报告技术无效原因，不能解释性能。

### 6.4 Timing、duration 与 compound OOD

`[FORMAL RESULT PENDING：按十个 OOD conditions 分解，报告每个条件的 UTR/DRTP mean、paired seed directions 和 worst condition。不得仅报告聚合均值。]`

该部分用于判断收益是否集中在某一个已见 F0 条件，还是能够覆盖 failure onset、duration 和 compound shift。对最差条件的解释必须同时给出绝对 (J) 和 paired difference，避免“低 nominal 导致假鲁棒”。

### 6.5 Safety、pre-trigger termination 与 risk-set validity

`[FORMAL RESULT PENDING：报告 overall collision/timeout/constraint、pre-trigger collision count/rate、survival-to-onset、risk-set size 和 trigger success。]`

若 episode 在 scheduled onset 前碰撞终止，该记录继续计入 overall return 和 collision，不重标为 exposed。只有存活至 onset 的 episode 才进入 trigger-validity denominator。正式技术有效性要求所有 onset-surviving failure episodes 正确触发。

### 6.6 自适应权重与机制遥测

`[FORMAL RESULT PENDING：报告 DRTP q、EMA、difficulty、realized group counts 的训练历程；关联 timing/duration/compound 的实际困难变化，但不将相关性写成因果。]`

机制分析还应展示 path-switch count、direct-path fraction、relay-path fraction、task-support fraction、legal-information fraction、cache age、travelled distance 和 control effort。允许的解释是“结果与更有针对性的扰动暴露和不同的路径/任务支持利用相一致”；除非有受控因果证据，不得写成“adaptive weighting 导致某一确定策略 basin”或“恢复信息”。

### 6.7 历史 reliability evidence

正式结果之外，历史分层证据用于说明为什么 seed reliability 必须进入论文主文。Development 3M 中，DRTP 的 pooled nominal、F0、OOD mean 和 OOD worst 均高于 UTR，但 seed1902 在 F0 和 OOD mean 上方向不利。Held-out 10M 中，seed2001 和 seed2003 获益，而 seed2002 在 F0、OOD 和 timeout 上发生严重反转，导致 held-out verdict 为 `FAIL`。这些历史结果不能与正式五种子作为一个同质样本合并，但必须作为方法风险和结果解释边界保留。

## 7 讨论

### 7.1 自适应扰动加权的作用范围

DRTP 的设计价值在于把模型容量、拓扑语义和奖励等因素固定后，单独检验训练分布控制。若正式结果通过，最强可支持的结论是：在本文冻结的三 UAV Relay failure 任务中，有界自适应故障组加权相对均匀拓扑随机化提高了任务鲁棒性的中心趋势，并且没有牺牲合同要求的 nominal competence 和安全边界。该结论仍是经验性的、任务有界的，不等价于一般分布鲁棒最优性。

### 7.2 平均收益与 seed reliability

MARL 的 pooled mean 可能掩盖训练初始化导致的策略分叉。历史 seed2002 已经排除了“单一 evaluation tape 偶然测低”的主要解释：其反转跨多个 tape 和 failure family 重复出现。另一方面，现有证据尚未将这种差异因果归结为特定 RNG source、policy basin 或优化机制。因此，本文将 mean、median、win count、dispersion、worst degradation 和 catastrophic seed 并列报告，而不把不利 seed 删除为 outlier。

正式五种子实验的作用正是把“平均收益”和“训练可靠性”放在同一前瞻性合同中判断。如果结果仅有少数 seed 提升或出现多个 catastrophic seeds，则高 pooled mean 不能支撑主方法结论。如果至少 3/5 seed 在三个 robustness endpoints 上有利且 mean/median 同时为正，仍只能支持 seed-sensitive，而非 seed-stable 的方法定位。

### 7.3 Safety 与替代解释

较高任务得分并不自动意味着更安全。DRTP 可能通过更激进的机动或更长的任务保持换取 return，因此 collision、timeout、constraint、distance 和 control effort 必须独立分析。历史结果中的 safety outcome 是 mixed，正式结果也必须按预注册 safety gate 判定。若 return 提升伴随系统性 collision/timeout 恶化，论文不能用任务得分覆盖该问题。

另一个替代解释是训练时接触了更多故障类型。该解释被 UTR 控制：UTR 与 DRTP 使用完全相同的六个 failure groups 和 50% nominal anchor，差别只在组权重是否自适应。因此，两者的正式差异不能归因于“DRTP 看过而 UTR 没看过”的 condition universe 差异。

### 7.4 与已有 robust/topology-aware MARL 的关系

DRTP 继承了 distributional robustness 和 adaptive sampling 的基本思想，也建立在 graph-based CTDE 之上。本文不声称发明图 MARL、鲁棒 MARL 或指数加权。其可辨识贡献是：将 Relay failure 定义为合法 communication/task-support path reconfiguration，在严格 actor information boundary 下构造 topology groups，并用 matched uniform comparator、paired OOD 和 seed reliability 对 bounded adaptive weighting 进行经验检验。

### 7.5 局限性

本文至少存在五项边界。第一，实验限于冻结的 Scout–Relay–Attacker 三 UAV 轻量 3DOF 仿真，尚无 4/5 UAV scalability、HIL 或实飞证据。第二，当前没有满足同一动作、信息和学习合同的 external drop-in comparator，主结论依赖内部 matched UTR ablation。第三，训练种子数量为五，统计结论以描述性 paired effect 为主，不支持广泛总体推断。第四，历史证据显示真实 seed sensitivity，其根因尚未建立。第五，DRTP 通过采样分布近似分布鲁棒目标，不提供理论 worst-case guarantee。

## 8 结论

本文研究了 Relay failure 导致合法通信路径和任务支持关系重构时的异构 UAV 协同。DRTP-SG-MAPPO 保持 Single-Graph MAPPO 网络、PPO、奖励和执行信息边界不变，仅在固定 nominal anchor 下对预定义拓扑扰动组进行有界自适应加权。通过与 UTR-SG-MAPPO 的参数和暴露范围匹配比较，本文将任务性能、OOD worst、安全性、故障触发有效性和训练种子可靠性纳入同一证据链。

`[FORMAL RESULT PENDING：根据冻结 verdict 插入一段且仅一段最终结论。不得使用 stable、consistently superior、universal robustness、information recovery 等表述。]`

无论正式结果方向如何，本文的适用范围均限于冻结的三 UAV 仿真和预定义 Relay-failure conditions。更大规模协同、真实通信栈、硬件在环与实飞验证需要独立合同和新的证据。

## 数据与代码可用性

`[AUTHOR INPUT NEEDED：填写匿名仓库或公开仓库地址、训练配置、checkpoint、evaluation tape、raw episode metrics、统计脚本及发布时点。建议至少公开正式合同、十个 final checkpoint hash、tape manifest/hash 和聚合脚本。]`

## 作者贡献、利益冲突与资助

`[AUTHOR INPUT NEEDED：作者名单、CRediT 分工、通讯作者、资助项目、利益冲突。]`

## 参考文献状态

正文中的 `[R1–R7]` 仅对应 `09_citation_ledger.md` 的待核验候选，不是最终参考文献。正式投稿前必须逐篇核对作者、标题、期刊/会议、年份、卷页和 DOI，并补充 MAPPO、GAT/graph MARL、robust MARL 与 UAV relay 领域的直接 primary sources。
