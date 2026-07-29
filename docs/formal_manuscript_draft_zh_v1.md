# 中文论文初稿 v1：有限通信与中继失效条件下异构无人机任务链恢复

日期：2026-07-29

本文档是当前项目的一篇论文中文初稿，依据以下文件编写：

- `docs/FINAL_Q1_SINGLE_PAPER_PLAN.md`
- `docs/formal_protocol_freeze.md`
- `docs/gate_prior_dev100_three_seed_decision.md`
- `docs/formal_manuscript_draft_v1.md`
- `docs/formal_methods_experiments_latex_zh.md`

本文档替代旧的二维追逃中文稿作为当前论文主线。旧稿中的“二维追逃、通信半径鲁棒性、随机半径微调”不再作为当前最终论文的中心叙事。

## 写作边界

当前可以写定的内容：

- 研究问题；
- 任务场景；
- 环境建模；
- 方法框架；
- 训练协议；
- baseline 设置；
- checkpoint 选择规则；
- 统计方法；
- 结果章节结构。

当前不能写死的内容：

- 最终成功率；
- 最终恢复率；
- 与 Single-Graph、HAPPO、MAPPO 的最终优势大小；
- 消融实验结论；
- 摘要中的最终数字；
- 结论中的强定量表述。

这些必须等待正式预算研究、五种子训练、validation 选点和最终 held-out test 完成后再填入。

## 中文题目候选

推荐题目：

**面向有限通信的异构无人机任务链恢复多关系角色图强化学习方法**

候选题目 1：

**有限通信与中继失效条件下异构无人机协同任务链恢复方法**

候选题目 2：

**基于多关系角色图的异构无人机协同杀伤链恢复决策方法**

候选题目 3：

**面向中继节点失效的异构无人机任务链韧性强化学习方法**

建议优先使用“任务链恢复”而不是直接使用“杀伤链闭合”作为主标题。原因是“任务链恢复”更适合算法论文和工程可复现实验；“杀伤链”可以在引言和任务定义中作为背景概念出现。

## 摘要

异构无人机协同任务依赖侦察、信息传递和攻击窗口形成等连续环节。当目标感知间歇发生、通信链路存在丢包和时延，或关键中继节点发生功能失效时，团队失败往往并非来自单个平台机动能力不足，而是来自任务链中的信息流断裂。现有多智能体强化学习方法通常采用无显式图结构的策略表示，或将所有智能体关系合并为单一同质图，难以区分直接感知、实际通信和任务支援三类关系在任务链恢复中的不同作用。针对这一问题，本文构建三自由度异构无人机任务链恢复环境，并提出边感知多关系角色图 MAPPO 方法 EA-RG-MAPPO。该方法分别建模感知关系、通信关系和任务支援关系，并通过发送—接收角色对条件消息传播机制，使不同角色关系能够采用差异化的信息聚合方式。实验协议采用严格目标感知、Actor 目标信息瓶颈、通信丢包、消息时延和中继节点失效设置，并与 MAPPO/no-graph、Single-Graph MAPPO、HAPPO 和参数量匹配 Single-Graph baseline 进行公平比较。最终结果将基于统一训练预算、固定 validation 选点、五个训练种子和一次性 held-out test 报告。[正式实验完成后填入核心定量结果：失效后新鲜信息恢复率、旧缓存恢复率、恢复时间、置信区间和安全指标。] 本文旨在为有限通信条件下异构无人机协同决策提供可复现的任务链韧性建模、训练和评价框架。

关键词：异构无人机；多智能体强化学习；MAPPO；多关系图；有限通信；间歇感知；任务链恢复；中继失效

## 1 引言

无人机协同任务正在从单个平台追踪与拦截，逐步转向由多平台共同完成的网络化侦察、信息传递和攻击窗口形成过程。在这类任务中，成功并不只取决于某一架无人机是否能够接近目标，而取决于团队是否能够持续完成“发现目标—传递信息—保持链路—形成攻击窗口”的任务链。如果目标信息无法被有效感知、传递或更新，即使平台本身仍然具备飞行能力，整个团队任务也可能失败。

异构无人机团队进一步放大了这一问题。侦察无人机可能具有更大的探测范围，但机动或攻击能力较弱；中继无人机可能负责维持通信链路，但一旦其通信功能失效，信息流会发生断裂；攻击无人机具备形成攻击窗口的能力，但往往依赖其他平台提供的新鲜目标信息。因此，智能体之间的关系不能简单看作“有边”或“无边”。侦察机到攻击机的关系可能表示目标信息支援，中继机到攻击机的关系可能表示消息传递路径，攻击机到中继机的关系也可能表示对关键通信链路的任务需求。

多智能体强化学习为这类协同决策问题提供了可行工具。集中训练、分散执行范式允许训练阶段使用全局状态估计价值函数，而执行阶段每个智能体只依赖自身可获得的信息。MAPPO 已经成为合作式多智能体任务中的强基线方法。然而，普通 MAPPO Actor 缺少显式拓扑和关系建模能力；普通图注意力方法虽然能够聚合邻居信息，但通常将不同关系压缩到同一个图结构中。对于通信受限和中继失效条件下的任务链恢复，关系类型本身具有明确物理意义：感知关系决定目标信息来源，通信关系决定消息是否真实到达，任务支援关系决定不同角色如何支撑任务链闭合。

本文关注一个现实可实现但具有任务深度的中间问题：在三自由度异构无人机协同拦截环境中，研究有限通信、消息丢包、消息时延、严格目标感知和中继节点失效条件下的任务链恢复。该环境不是完整六自由度空战系统，也不包含在线导弹、复杂雷达信号处理和有人机协同全流程。这样的设定是有意为之：它可以在可控计算成本内完成多种子、公平 baseline 和统计验证，同时保留无人机协同任务中最关键的信息链约束。

为解决上述问题，本文提出 EA-RG-MAPPO，即边感知多关系角色图 MAPPO 方法。该方法将无人机团队的关系分为感知关系、通信关系和任务支援关系，并在消息传播时显式考虑发送方和接收方的角色类型。本文的核心问题不是证明该方法在所有无人机任务中都最优，而是验证在严格感知、有限通信和中继失效条件下，多关系角色图是否能够提高任务链恢复的可靠性、安全性和可解释性。

本文主要贡献如下：

1. 构建有限通信与中继失效条件下的异构无人机任务链恢复问题。该任务包含侦察、中继和攻击角色分工，严格目标感知，Actor 信息边界，通信丢包，消息时延，消息缓存 TTL 与置信度，以及中继节点通信功能失效。
2. 提出感知—通信—任务支援多关系角色图表示。该表示将直接感知、实际消息传递和动态任务支援从单一同质图中分离出来，使策略能够区分不同边的物理意义。
3. 提出角色对条件消息传播机制，使不同发送—接收角色组合采用不同的信息变换和聚合方式，从而更好地建模异构无人机任务链恢复中的角色依赖。

本文后续的实验部分将围绕一个冻结协议展开：四个固定中继失效时机场景、统一训练预算、固定 validation 选点、五个训练种子、一次性最终 held-out test 和 seed-aware hierarchical bootstrap 统计。所有最终结论均以正式协议下的数据为准。

## 2 相关工作

### 2.1 多智能体强化学习与无人机协同

多智能体强化学习广泛应用于合作控制、资源分配、协同追踪和对抗决策等任务。集中训练、分散执行框架通过集中式 critic 缓解训练过程中的非平稳性，同时保留执行阶段的分布式特征。MAPPO 作为 PPO 在多智能体合作任务中的扩展，因实现稳定、调参成本相对可控，已经成为重要 baseline。HAPPO 等异构智能体 PPO 方法进一步考虑了不同智能体策略或动作空间差异，为异构无人机协同任务提供了有价值的比较对象。

在无人机任务中，强化学习已被用于轨迹规划、协同追逃、空战机动和集群控制。然而，许多工作主要关注几何接近、拦截成功或奖励累计值，而对任务链中的信息来源、通信可达性和关键节点失效关注不足。在有限通信和中继失效条件下，策略不仅要控制平台运动，还要在信息不完整的情况下恢复侦察—通信—攻击链路。因此，仅使用常规成功率或累计奖励评价策略是不充分的。

### 2.2 图神经网络与多智能体关系建模

图神经网络适合描述多智能体系统中智能体之间的动态关系。图注意力网络能够根据节点特征自适应聚合邻居信息，已被用于多智能体协同、通信学习和编队控制等任务。对于无人机协同任务，图结构具有直接物理意义：节点表示平台或目标，边可以表示距离邻近、通信可达、目标感知或任务支援。

现有图强化学习方法常采用单一邻接矩阵，将所有关系压缩为同一种边。该做法在一般协同任务中可能有效，但在异构无人机任务链恢复中存在表达不足。感知关系、通信关系和任务支援关系不仅来源不同，其失效方式也不同。目标感知可能因视场限制而丢失，消息传递可能因丢包或时延而失效，任务支援关系则取决于当前链路阶段和角色职责。本文因此采用多关系图结构，而不是单一同质图结构。

### 2.3 有限通信与韧性多智能体系统

有限通信是实际多智能体系统中的基本约束。通信半径、链路质量、带宽、消息丢包和时延都会影响智能体可获得的信息。已有研究讨论了智能体何时通信、与谁通信以及如何压缩消息等问题。韧性多智能体系统进一步关注节点失效、链路断裂和拓扑变化下的任务保持能力。

本文与上述工作的区别在于，本文不只把通信受限看作图连接变化，而是将其放入异构无人机任务链恢复过程中。中继节点失效后，策略需要判断哪些平台仍能感知目标，哪些消息仍然有效，攻击平台是否拥有足够新鲜的目标信息，以及任务链是否重新闭合。因此，本文评价的不只是通信图是否连通，而是通信约束下任务链是否能够恢复。

### 2.4 无人机任务链与协同拦截评价

传统无人机协同拦截实验常用成功率、平均距离、任务时间和碰撞率作为评价指标。这些指标必要但不充分。对于异构任务链而言，团队可能在几何上接近目标，却因目标信息过期或攻击平台失去有效信息而无法形成攻击窗口。本文因此引入失效后新鲜信息恢复率、旧缓存恢复率、限制平均恢复时间、目标持续跟踪率、攻击平台目标缓存新鲜度、通信连通率和消息年龄等指标，以更直接地评价任务链韧性。

## 3 问题建模

本文将异构无人机任务链恢复建模为集中训练、分散执行条件下的部分可观测多智能体决策问题。蓝方包含侦察无人机、中继无人机和攻击无人机，红方包含一个受控目标。蓝方智能体集合为 \(\mathcal{N}=\{1,\ldots,N\}\)，全局状态为 \(s^t\)，智能体 \(i\) 的局部观测为 \(o_i^t\)，可见图输入为 \(\mathcal{G}_i^t\)，高层三自由度动作为 \(a_i^t\)。问题可写为

\[
\mathcal{M}=\langle \mathcal{N},\mathcal{S},\{\mathcal{O}_i\}_{i=1}^{N},
\{\mathcal{A}_i\}_{i=1}^{N},P,R,\gamma\rangle .
\]

训练阶段采用 centralized training with decentralized execution。critic 可以使用全局状态、真实攻击窗口和任务链闭合状态来估计价值；actor 只能使用自身状态、角色编码、已投递消息、消息年龄、置信度、直接感知标志、本地目标缓存和 actor 可见图关系。actor 不允许读取真实目标状态、未送达消息、全局攻击保持计数、全局任务链阶段或评价专用链路闭合变量。

为明确区分评价真值与 actor 可见代理，本文定义两类攻击窗口。真实攻击窗口 \(\omega_i^t\) 由环境真实目标状态计算，只用于奖励、critic、终止和评价。actor 可见本地攻击窗口 \(\ell_i^t\) 由智能体 \(i\) 的本地目标估计 \(\hat{x}_{T,i}^t\) 计算；在 strict sensing 和 target-information bottleneck 开启时，若 \(i\) 没有直接探测或未过期目标缓存，则 \(\ell_i^t=0\)。因此，本地攻击窗口不是从真实目标位置直接读取的泄漏变量。

目标信息有效性定义为

\[
F_i^t =
\mathbb{I}\left[d_i^t=1\right]
\lor
\mathbb{I}\left[
v_i^t=1,\ 
t-g_i^t \le A_{\max},\
c_i^t \ge c_{\min}
\right],
\]

其中 \(d_i^t\) 为直接目标探测标志，\(v_i^t\) 为本地目标缓存有效标志，\(g_i^t\) 为缓存生成时刻，\(A_{\max}\) 为最大消息年龄，\(c_i^t\) 为缓存置信度，\(c_{\min}\) 为最小置信度阈值。

任务链闭合评价由目标信息、通信可达和真实攻击窗口共同决定。设攻击平台集合为 \(\mathcal{A}_{\mathrm{atk}}\)，攻击平台 \(k\) 在时刻 \(t\) 具备有效目标信息 \(F_k^t=1\)，且真实攻击窗口 \(\omega_k^t=1\)，则瞬时闭合标志为

\[
z_t=\mathbb{I}\left[
\exists k\in \mathcal{A}_{\mathrm{atk}},\
F_k^t=1,\ \omega_k^t=1
\right].
\]

为避免将偶然穿越攻击包线视为成功，任务成功要求 \(z_t\) 连续保持 \(H\) 步，且回合步数不早于最小成功步 \(t_{\min}\)：

\[
\mathrm{success}=
\mathbb{I}\left[
t\ge t_{\min},\
\sum_{\tau=t-H+1}^{t} z_{\tau}=H
\right].
\]

设中继通信失效起始时刻为 \(t_f\)，失效后恢复必须与成功条件一致，也要求形成连续 \(H\) 步稳定闭合窗口。失效后首次稳定恢复步定义为

\[
t_{\mathrm{rec}}=
\min\left\{
t\mid t\ge t_f+H-1,\
\sum_{\tau=t-H+1}^{t}z_{\tau}=H
\right\}.
\]

恢复延迟按稳定闭合窗口的起始点计算：

\[
T_{\mathrm{rec}}=t_{\mathrm{rec}}-t_f-H+1 .
\]

若回合结束前不存在 \(t_{\mathrm{rec}}\)，则该回合记为未恢复。若失效开始时任务链已经保持闭合，则记为 maintained case；若失效后曾丢失再恢复，则记为 recovered-after-loss case。为避免将失效前旧缓存或“故障后投递的故障前旧观测”误判为真正恢复，本文进一步定义故障后生成的新鲜信息标志：

\[
F_{k,\mathrm{fresh}}^t=
F_k^t
\mathbb{I}
\left[
g_{k,\mathrm{cache}}^t\ge t_f
\right],
\]

其中 \(g_{k,\mathrm{cache}}^t\) 为攻击机当前生效缓存对象的生成步。投递步 \(d_{k,\mathrm{cache}}^t\) 只用于区分“故障后投递的旧信息”和通信恢复来源，不能替代生成步作为新鲜信息判据。新鲜信息闭合标志定义为

\[
z_{t,\mathrm{fresh}}=
\mathbb{I}
\left[
\exists k\in\mathcal{A}_{\mathrm{atk}},
F_{k,\mathrm{fresh}}^t=1,\;
\omega_k^t=1
\right].
\]

主指标要求连续 \(H\) 步均满足 \(z_{t,\mathrm{fresh}}=1\)，并且在恢复窗口之前任务链确实发生过丢失。若任务链始终保持闭合，只计入 `fresh_info_acquired_without_prior_loss`，不计入 `post_failure_fresh_info_recovered`。若任务链闭合依赖失效前缓存，则计入 stale-cache recovered；若信息在故障前生成但故障后投递，则计入 post-delivered old-information recovery。正式主指标采用 after-loss 的故障后新鲜信息恢复率；delayed recovery 仅作为辅助指标。未恢复样本按删失样本处理，论文统计中必须同时报告恢复概率和恢复时间，不能只在已恢复样本上计算平均恢复时间。

## 4 三自由度异构无人机任务链恢复环境

### 4.1 三自由度状态、动作与动力学

主实验采用轻量三自由度异构无人机协同拦截环境。平台状态为

\[
x_i^t=[p_{x,i}^t,p_{y,i}^t,p_{z,i}^t,v_i^t,\psi_i^t,\gamma_i^t],
\]

其中 \(p_i^t\) 为三维位置，\(v_i^t\) 为速度，\(\psi_i^t\) 为航向角，\(\gamma_i^t\) 为航迹倾角。蓝方策略输出高层离散指令

\[
a_i^t=[u_{\psi,i}^t,u_{\gamma,i}^t,u_{v,i}^t],\quad
u_{\psi,i}^t,u_{\gamma,i}^t,u_{v,i}^t\in\{-1,0,1\}.
\]

状态更新为

\[
\psi_i^{t+1}=\mathrm{wrap}
(\psi_i^t+u_{\psi,i}^t \dot{\psi}_{i,\max}\Delta t),
\]

\[
\gamma_i^{t+1}=\mathrm{clip}
(\gamma_i^t+u_{\gamma,i}^t\dot{\gamma}_{i,\max}\Delta t,
-\gamma_{i,\max},\gamma_{i,\max}),
\]

其中 \(\dot{\gamma}_{i,\max}=0.35\gamma_{i,\max}\)，单位为 \(\mathrm{rad/s}\)，表示高层爬升指令对应的航迹倾角响应率。

\[
v_i^{t+1}=\mathrm{clip}
(v_i^t+u_{v,i}^t a_{i,\max}\Delta t,
v_{i,\min},v_{i,\max}),
\]

\[
p_i^{t+1}=p_i^t+
\begin{bmatrix}
v_i^{t+1}\cos\gamma_i^{t+1}\cos\psi_i^{t+1}\\
v_i^{t+1}\cos\gamma_i^{t+1}\sin\psi_i^{t+1}\\
v_i^{t+1}\sin\gamma_i^{t+1}
\end{bmatrix}
\Delta t .
\]

该接口有意保持在高层战术控制层，使强化学习主要学习任务链恢复与协同决策，而不是低层飞行控制。主训练和正式统计均基于该 3DOF 环境；6DOF/JSBSim 只作为少量高层指令可执行性验证。

### 4.2 平台异构参数

平台异构性进入动力学、雷达、通信和攻击窗口约束，而不是只作为角色标签。当前主实验平台参数如下，正式投稿时应由代码配置自动导出：

| 平台 | 角色 | 速度范围 m/s | 最大加速度 | 最大转弯率 rad/s | 最大航迹倾角 rad | 雷达范围 m | 通信范围 m | 攻击范围 m | 攻击锥 rad |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Scout | 侦察 | 120-245 | 18 | 0.035 | 0.26 | 17500 | 9500 | 1800-6500 | 0.733 |
| Relay | 中继 | 115-220 | 14 | 0.030 | 0.22 | 12000 | 15500 | 2000-5800 | 0.611 |
| Attacker | 攻击 | 135-270 | 22 | 0.052 | 0.31 | 11000 | 8500 | 1400-5200 | 0.873 |
| Target | 目标 | 130-255 | 18 | 0.046 | 0.28 | 10000 | - | - | - |

冻结主实验中红方目标采用 straight 策略。该设置不是为了回避复杂目标机动，而是为了把主因果问题集中在通信受限、中继失效和任务链恢复上。更复杂的 weaving target、4v2/5v2 和 LAG/JSBSim 回放只能作为主结果冻结后的真实性补充。

### 4.3 感知、缓存与 Actor 信息流

目标探测由雷达距离、水平视场、垂直视场和雷达丢失共同决定。若目标处于平台 \(i\) 的雷达范围和视场内，且本步未发生雷达 dropout，则 \(d_i^t=1\)，平台写入本地目标缓存。缓存字段包括目标位置估计、速度估计、信息源、生成步、投递步、跳数、置信度和路径。

actor observation schema 采用代码中的 `OBS3D_FIELD_NAMES` 管理，当前长度为 34。关键字段来源如下：

| 字段/变量 | Actor 可见 | 来源 | 约束 |
|---|---|---|---|
| 自身位置、速度、航向、航迹倾角 | 是 | 本机状态 | 始终可见 |
| 角色 one-hot | 是 | 平台配置 | 仅表示 scout/relay/attacker/interceptor |
| `direct_target_detected` | 是 | 本机雷达探测 | 受距离、视场和 radar dropout 约束 |
| 目标相对量 | 是 | 本地目标估计 | strict+bottleneck 下来自本地缓存或合法先验 |
| `local_target_cache_age` | 是 | 本地缓存生成步 | 超 TTL 后不再视为有效 |
| `local_target_cache_confidence` | 是 | 本地缓存置信度 | 多跳转发衰减 |
| `local_attack_window` | 是 | 本地目标估计 | 无有效目标信息时强制为 0 |
| `comm_adj` / delivered message | 是 | 已投递消息 | 受通信半径、丢包、时延和节点失效约束 |
| `attack_window` | 否 | 真实目标状态 | 仅用于 reward、critic、termination、evaluation |
| `attack_hold` / `chain_closed` | 否 | 全局评价变量 | 不进入 actor |

这一区分直接回应信息泄漏风险：正文中的“本地攻击窗口标志”指 `local_attack_window`，其计算使用 \(\hat{x}_{T,i}^t\) 而不读取真实目标位置。真实攻击窗口 \(\omega_i^t\) 仍保留为环境评价变量。

### 4.4 通信、丢包、时延与中继失效

通信图采用接收者-发送者约定，\(C_{ij}^t=1\) 表示智能体 \(i\) 在时刻 \(t\) 收到来自智能体 \(j\) 的消息。若任一端处于通信失效状态，则该边不可用。否则，物理通信候选边满足

\[
\|p_i^t-p_j^t\|_2
\le \alpha \min(r_i^{\mathrm{comm}},r_j^{\mathrm{comm}}).
\]

在距离约束满足后，消息仍以概率 \(p_{\mathrm{drop}}\) 丢失，并以 \(D\) 步延迟投递。到期消息只有在发送者和接收者当前均未通信失效时才能进入 delivered communication graph。目标消息随投递写入接收者缓存，置信度按跳数衰减；若缓存年龄超过 \(A_{\max}\) 或置信度低于 \(c_{\min}\)，则不再被 actor 视为有效目标信息。

中继节点失效建模为通信功能失效，而非平台动力学失效。设失效节点为 \(k\)，失效区间为 \([t_f,t_f+T_f)\)，则

\[
C_{ij}^t=C_{ji}^t=0,\quad
\forall j\ne i,\ i=k,\ t\in[t_f,t_f+T_f).
\]

该节点仍可飞行，也可能具有本地感知，但不能发送或接收普通消息和目标消息。

### 4.5 攻击窗口、终止与指标

真实攻击窗口 \(\omega_i^t\) 由真实相对距离、高度差、进入角和闭合速度决定：

\[
\omega_i^t=\mathbb{I}
\left[
r_{\min,i}^{\mathrm{atk}}\le \|p_T^t-p_i^t\|_2\le r_{\max,i}^{\mathrm{atk}},
\ |\Delta \psi_i^t|\le \theta_i^{\mathrm{atk}},
\ |\Delta h_i^t|\le h_{\max},
\ v_{\mathrm{closure},i}^t>-30
\right].
\]

本地攻击窗口 \(\ell_i^t\) 使用相同几何判据，但将真实目标状态 \(p_T^t\) 替换为 actor 合法目标估计 \(\hat{p}_{T,i}^t\)，并要求 \(F_i^t=1\)。因此 \(\ell_i^t\) 可进入 actor 和任务支援图，\(\omega_i^t\) 只能用于评价和训练信号。

主评价指标包括任务成功率、失效后新鲜信息恢复率、旧缓存恢复率、受限平均恢复时间、目标跟踪率、通信连通率、平均消息年龄、攻击平台新鲜目标缓存比例、碰撞率和超时率。延迟恢复率作为辅助诊断指标报告。这些指标共同反映策略是否真正恢复任务链，而不是只提高累计奖励。

## 5 方法：EA-RG-MAPPO

### 5.1 总体框架

EA-RG-MAPPO 在 MAPPO 的集中训练、分散执行框架上引入 actor 侧多关系角色图编码器。每个时间步构建

\[
\mathcal{G}^t=
\{\mathbf{A}_{\mathrm{per}}^t,
\mathbf{A}_{\mathrm{comm}}^t,
\mathbf{A}_{\mathrm{sup}}^t,
\mathbf{E}^t\},
\]

其中 \(\mathbf{A}_{\mathrm{per}}^t\) 为感知关系，\(\mathbf{A}_{\mathrm{comm}}^t\) 为已投递通信关系，\(\mathbf{A}_{\mathrm{sup}}^t\) 为任务支援关系，\(\mathbf{E}^t\) 为边特征。三类关系分别编码再融合，使 actor 能够区分“谁拥有目标信息”“谁实际传递了消息”和“谁以合法可见方式支援当前任务链”。

主实验蓝方只有 Scout、Relay 和 Attacker 三类角色。代码中的 Interceptor 是为后续 4v2/5v2 扩展保留的角色槽位，在 3v1 主实验中不出现。论文主公式以 \(\{\mathrm{Scout},\mathrm{Relay},\mathrm{Attacker},\mathrm{Target}\}\) 为准。EA-RG-MAPPO-S 中的后缀 S 表示使用冻结 staged/gate-prior 训练协议的候选版本，不代表一个额外独立算法贡献。

### 5.2 多关系角色图构建

感知关系表示目标信息来源。若蓝方节点 \(i\) 直接探测到目标节点 \(T\)，则

\[
A_{\mathrm{per},iT}^t=d_i^t .
\]

目标节点角色记为 \(\rho_T=\mathrm{Target}\)。若 strict sensing 和 target-information bottleneck 开启，actor 共享图中的目标节点固定为公共先验位置和零速度，不携带真实目标状态，也不携带“任一平台已探测目标”的全局标志。合法目标信息只进入直接探测或收到有效消息的平台局部观测和本地缓存。实现中保留的本地攻击窗口辅助边不属于三类主关系，也不作为方法贡献；它仅由 actor 可见的 \(\ell_i^t\) 生成，不能由真实攻击窗口 \(\omega_i^t\) 生成。

通信关系表示实际投递的智能体间消息：

\[
A_{\mathrm{comm},ij}^t=C_{ij}^t .
\]

任务支援关系采用“角色兼容 + 已投递通信 + actor 可见支援证据”的定义。设 \(R_{ji}=1\) 表示发送者 \(j\) 和接收者 \(i\) 的角色组合允许形成支援关系，例如 scout-to-attacker、relay-to-attacker、relay-to-scout 和 attacker-to-relay。设 \(E_j^t\) 为发送者 \(j\) 的可见支援证据，则

\[
A_{\mathrm{sup},ij}^t
=R_{ji}\cdot C_{ij}^t\cdot E_j^t .
\]

其中

\[
E_j^t=
\begin{cases}
F_j^t, & \rho_j=\mathrm{Scout},\\
F_j^t, & \rho_j=\mathrm{Relay},\\
\ell_j^t, & \rho_j=\mathrm{Attacker},\\
0, & \mathrm{otherwise}.
\end{cases}
\]

Relay 的支援证据只取决于其自身已经更新后的目标信息 \(F_j^t\)。如果 Scout 的消息在时刻 \(t\) 成功投递给 Relay，环境先写入 Relay 本地缓存，再计算 \(F_j^t\)；若消息未投递、已过期或置信度不足，则 Relay 不能通过读取 Scout 当前私有状态激活支援边。这里 \(\ell_j^t\) 是 actor 可见本地攻击窗口，而非真实攻击窗口。任务支援边不能绕过通信图形成独立信息通道；若 \(C_{ij}^t=0\)，则即使角色兼容，\(A_{\mathrm{sup},ij}^t\) 也必须为 0。

边特征 \(\mathbf{e}_{ij}^t\) 包括相对位置、相对距离、视线方向、相对速度、同队标志、感知标志、通信标志、静态角色支援兼容标志、本地攻击窗口标志、消息年龄和置信度等。边特征中的静态角色兼容只作为特征，不能单独打开图邻接；真正可传播的任务支援关系由 \(A_{\mathrm{sup}}\) 控制。

### 5.3 角色对条件消息传播

设节点 \(i\) 的表示为 \(h_i^t\)，关系类型为 \(r\in\{\mathrm{per},\mathrm{comm},\mathrm{sup}\}\)。发送者 \(j\) 到接收者 \(i\) 的消息为

\[
m_{ij}^{r,t}
=g_{\rho_j,\rho_i}^{r}
\left(h_j^t,\mathbf{e}_{ij}^t\right),
\]

其中 \(g_{\rho_j,\rho_i}^{r}\) 根据发送者和接收者角色调制消息映射。关系内注意力为

\[
\alpha_{ij}^{r,t}=
\mathrm{softmax}_{j}
\left(q_i^{r,t\top}k_{ij}^{r,t}\right),
\]

\[
\tilde{h}_i^{r,t}
=\sum_j A_{r,ij}^t\alpha_{ij}^{r,t}m_{ij}^{r,t}.
\]

多关系表示再经融合网络得到 actor 表示：

\[
\bar{h}_i^t=
\phi\left(h_i^t,\tilde{h}_i^{\mathrm{per},t},
\tilde{h}_i^{\mathrm{comm},t},
\tilde{h}_i^{\mathrm{sup},t}\right).
\]

普通 Single-Graph MAPPO 将感知、通信和支援关系合并为单一同质邻接；EA-RG-MAPPO 的区别在于保留关系类型，并根据角色对调制消息传播。当前冻结候选使用 `role_gate_prior_strength=0.4` 的 role-gate prior，以避免角色门控在短预算训练中长期停留在近中性状态。该先验是统一训练协议的一部分，不单独作为论文贡献。

### 5.4 MAPPO 优化与训练初始化

策略为

\[
\pi_{\theta}(a_i^t|o_i^t,\mathcal{G}_i^t),
\]

联合动作概率按智能体策略相乘。MAPPO 裁剪目标为

\[
\mathcal{L}_{\pi}(\theta)=
\mathbb{E}_t
\left[
\min\left(
r_t(\theta)\hat{A}_t,
\mathrm{clip}(r_t(\theta),1-\epsilon,1+\epsilon)\hat{A}_t
\right)
\right],
\]

\[
r_t(\theta)=
\frac{\pi_{\theta}(a_t|o_t,\mathcal{G}_t)}
{\pi_{\theta_{\mathrm{old}}}(a_t|o_t,\mathcal{G}_t)} .
\]

集中式 critic 通过

\[
\mathcal{L}_{V}(\psi)=
\mathbb{E}_t[(V_{\psi}(s_t)-\hat{R}_t)^2]
\]

进行训练。最终目标包含策略损失、价值损失和熵正则。行为克隆初始化、几何 offset teacher、后失效恢复奖励、安全惩罚和 role-gate prior 均作为统一训练协议处理；所有支持相应机制的方法必须使用相同设置，不能给主方法额外训练资源。

### 5.5 奖励函数

环境采用团队共享奖励加少量角色项。设 \(\Delta d_t\) 为平均目标距离缩短量，\(\bar{D}_t\) 为平均直接探测率，\(\bar{\omega}_t\) 为真实攻击窗口比例，\(\kappa_t\) 为通信连通率，\(\bar{a}_t\) 为平均消息年龄归一化惩罚，\(q_t\) 为攻击几何辅助分数，\(b_t^{\mathrm{rec}}\) 为失效后任务链重新闭合奖励，\(p_t^{\mathrm{safe}}\) 为安全距离惩罚，则基础团队奖励为

\[
r_t^{\mathrm{team}}=
0.25\Delta d_t
+0.12\bar{D}_t
+0.18\bar{\omega}_t
+0.05\kappa_t
-0.03\bar{a}_t
+0.05[\bar{D}_t-\bar{D}_{t-1}]_{+}
+0.08[\bar{\omega}_t-\bar{\omega}_{t-1}]_{+}
+w_{\mathrm{geo}}q_t
+b_t^{\mathrm{rec}}
-w_{\mathrm{safe}}p_t^{\mathrm{safe}} .
\]

成功终止额外加 \(+2.0\)，碰撞惩罚为 \(-2.0\)，飞行边界或约束违规惩罚为 \(-1.5\)。角色项为

\[
r_{i,t}=r_t^{\mathrm{team}}
+0.08\mathbb{I}[\rho_i=\mathrm{Scout}]d_i^t
+0.05\mathbb{I}[\rho_i=\mathrm{Relay}]\kappa_t
+0.12\mathbb{I}[\rho_i=\mathrm{Attacker}]\omega_i^t
-0.02(1-e_i^t).
\]

正式协议固定 \(w_{\mathrm{geo}}=0\)，\(w_{\mathrm{safe}}=0.5\)，失效后任务链重闭合奖励权重为 \(0.5\)。奖励函数对所有学习方法一致；行为克隆和奖励塑形只作为训练协议，不作为主创新点。

### 5.6 信息边界审计

当前代码已将 actor 侧 `local_attack_window` 与评价侧 `attack_window` 分离，并增加自动化信息边界测试。测试覆盖任务支援边必须依赖已投递通信、未投递静态支援不能进入 union graph、中继失效阻断中继发出的支援边、Relay 不能读取队友当前私有目标信息、隐藏目标状态变化不能改变断联攻击机 logits、本地攻击窗口必须依赖 actor 可见目标信息，以及失效后恢复时间必须与连续闭合窗口一致。该测试属于可复现性证据，正式论文可在实现细节或补充材料中报告。

## 6 实验协议

### 6.1 对比方法

正式实验包含五个主方法：

| 方法 | 作用 |
|---|---|
| MAPPO/no-graph | 无图 CTDE 基线，用于检验显式拓扑是否必要 |
| Single-Graph MAPPO | 单一同质图基线，用于检验多关系拆分是否必要 |
| Parameter-Matched Single-Graph MAPPO | 参数量匹配单图基线，用于排除容量差异解释 |
| HAPPO | 异构策略更新外部 MARL 基线 |
| EA-RG-MAPPO-S | 当前主候选，多关系角色图与角色对条件消息传播 |

几何规则控制器只作为任务可达性参考，不作为学习算法 baseline。Original EA-RG-MAPPO without prior 只作为内部开发消融或训练协议分析，不作为必须外部 baseline。任务支援图必要性还需通过以下消融验证：Multi-Relation without Support Graph、Multi-Relation with Support as Edge Feature、Single-Graph + full edge features，以及 Single-Graph + Role-Pair Gate。

### 6.2 冻结场景

正式 validation 和最终 test 使用四个固定场景：

- `dropout030_delay2_relay_failure_early`
- `dropout030_delay2_relay_failure`
- `dropout030_delay2_relay_failure_delayed`
- `dropout030_delay2_relay_failure_late`

冻结设置包括：

- 目标策略：straight；
- 严格目标感知：开启；
- Actor 目标信息瓶颈：开启；
- 通信丢包概率：0.30；
- 消息时延：2；
- 失效蓝方节点：中继机，编号 1；
- 训练失效开始时间：随机区间 [25, 70]；
- 失效持续时间：80 步；
- 最小成功步数：80。

冻结协议后，不允许通过新增目标难度、修改通信丢包、调整时延或改变失效时机来选择最终方法。额外场景只能在主结果冻结后作为鲁棒性补充。

### 6.3 训练预算与 checkpoint 选择

训练预算使用环境交互步数定义：

```text
environment steps = num_envs * rollout_steps * updates
```

在 `num_envs=8`、`rollout_steps=128` 下，每个 update 对应 1024 个环境交互步。1M 环境步约为 977 updates，2M 环境步约为 1954 updates。

正式流程先进行五方法、三开发种子的 1M 预算研究。定义最后 10% checkpoint 的验证主指标均值为 \(\bar{y}_{\mathrm{last}}\)，前一个 10% checkpoint 区间均值为 \(\bar{y}_{\mathrm{prev}}\)，晚期提升为 \(\Delta_{\mathrm{late}}=\bar{y}_{\mathrm{last}}-\bar{y}_{\mathrm{prev}}\)。若至少三种主方法满足 \(\Delta_{\mathrm{late}}>0.03\)，或至少两种方法在 1M 下存在 seed failure，则所有方法统一扩展到 2M；否则使用 1M。seed failure 预先定义为该 seed 在验证套件失效后新鲜信息恢复率低于 0.10 且成功率低于 0.20。最终公共预算 \(B^*\) 必须对所有方法相同，不能只延长 EA-RG-MAPPO。

每个方法、每个训练种子只能通过 validation 选择一个 checkpoint。该 checkpoint 同时用于四个失效时机场景。选择指标为 suite-level post-failure fresh-information recovery。`delayed_recovery_min_step=80` 仅作为辅助报告阈值，不作为主选点指标。最终 held-out test 只能在方法、预算、checkpoint 规则、奖励、安全、BC 和场景全部冻结后运行一次。

预算扩展规则必须在查看最终 test 前冻结。1M/2M 的选择依据 validation 曲线和预定义 seed failure，而不是某个方法在 held-out test 中的表现。最终公共预算 \(B^\*\) 对所有主方法相同。

### 6.4 统计方法

主统计采用 paired seed-aware hierarchical bootstrap。重采样过程为：

1. 以训练 seed 对为最高层单位重采样；
2. 在每个被抽中的 seed 内重采样相同的 matched episode index；
3. 对所有方法保留相同场景、episode seed 和重采样索引；
4. 先计算配对方法差值，再重复 10000 次获得 95% 置信区间。

论文将报告方法均值、seed 级标准差、均值差、置信区间和逐 seed 散点。不能把同一训练模型产生的所有 episode 当成完全独立样本，也不能只报告最佳 seed。

五个训练种子是当前算力和周期下的最低正式配置。为降低统计不足风险，论文应同时报告逐 seed 散点、paired difference、bootstrap confidence interval 和场景分解结果。若主方法只在部分 seed 或部分场景中领先，结论必须写成有条件优势，而不能写成无条件 SOTA。

## 7 结果章节计划

本章节将在正式实验完成后填入。当前只确定结果组织方式。

### 7.1 主结果对比

需要回答：

主要问题是：EA-RG-MAPPO 是否在四场景平均失效后新鲜信息恢复率上优于 Parameter-Matched Single-Graph MAPPO，并在碰撞率不升高的约束下保持优势？MAPPO/no-graph、Single-Graph MAPPO 和 HAPPO 用于解释图结构、参数容量和异构策略更新的影响。

需要报告：

- post-failure fresh-information recovery；
- recovered-after-loss rate；
- stale-cache recovered rate；
- delayed recovery；
- recovery rate；
- restricted mean recovery time；
- success rate；
- timeout rate；
- collision rate；
- seed-aware confidence interval。

### 7.2 中继失效后的恢复过程

需要回答：

优势是否来自失效后更快恢复目标跟踪、通信连通或攻击平台新鲜目标缓存？

需要报告：

- 失效对齐后的 tracking rate 曲线；
- communication connectivity 曲线；
- chain-closed probability 曲线；
- message age 曲线；
- 代表性成功/失败 episode。

### 7.3 多关系机制分析

需要回答：

感知关系、通信关系和任务支援关系是否真正参与了恢复过程？

需要报告：

- relation attention；
- role-pair gate 统计；
- 不同关系在失效前后变化；
- 预定义规则选择的代表性案例。

### 7.4 消融实验

正式消融必须重新训练，不能只在 test 时关闭模块。关键消融包括：

- w/o Role-Pair Gate；
- w/o Task-Support Relation；
- w/o Explicit Role Identity；
- Parameter-Matched Single Graph。

如果消融结果不支持预期机制，论文必须收缩主张，不能强行声称这些模块是主要原因。

### 7.5 场景深度补充

主实验完成后，可以加入：

- mild maneuvering target；
- 小规模 4v2/5v2 rule-red；
- LAG/JSBSim replay 或可执行性验证。

这些内容用于增强真实性和一区投稿竞争力，但不能替代主实验的公平统计证据。

## 8 讨论

如果正式结果支持开发阶段趋势，本文可以得出以下解释：在通信受损和中继失效条件下，异构无人机团队的主要难点不是单纯机动控制，而是目标信息如何在受限网络中恢复到攻击平台。无图 MAPPO 可能学到一定协同行为，Single-Graph MAPPO 也能够利用拓扑信息，但二者都没有显式区分感知、通信和任务支援关系。EA-RG-MAPPO 的潜在优势在于，它把这些关系分离，使策略能够更清楚地建模任务链恢复过程中的信息来源和角色依赖。

本文也必须讨论替代解释。如果最终结果显示 Single-Graph 与 EA-RG-MAPPO 接近，说明显式图结构可能已经提供了主要收益，多关系机制的边际贡献有限。如果 HAPPO 表现接近或超过 EA-RG-MAPPO，则需要讨论异构策略更新与图结构信息传播之间的差异。如果 role-gate prior 或行为克隆初始化解释了主要性能提升，则必须将这些因素作为训练协议优势，而不是算法结构创新。

本文的边界同样明确。主实验是 3DOF 3v1 场景，不是完整 6DOF 空战；目标策略在主实验中受控；导弹、复杂雷达、有人机协同和大规模红蓝自博弈不属于当前主统计证据。这些边界不是缺陷，而是为了在有限研究周期内形成可验证、可复现、可审计的算法证据链。

## 9 结论

本文研究有限通信、间歇感知、消息不确定性和中继节点失效条件下的异构无人机任务链恢复问题。本文构建了通信可行的三自由度异构无人机任务链恢复环境，并提出 EA-RG-MAPPO 方法，通过感知—通信—任务支援多关系角色图和角色对条件消息传播建模异构无人机之间的信息流与任务依赖。最终结论将在正式 held-out test 完成后补充具体结果。论文结论必须严格限定在正式实验支持的范围内，不扩展为完整六自由度空战、在线导弹交战或有人机协同系统结论。

## 10 主张—证据对应表

| 论文主张 | 所需证据 | 当前状态 |
|---|---|---|
| 环境满足通信可行和 Actor 信息边界 | P0 测试、观测 schema、协议文档 | 需要在论文 Methods 中引用具体测试 |
| EA-RG-MAPPO 优于 MAPPO/no-graph | 五种子 final held-out test、bootstrap CI | 等待正式实验 |
| EA-RG-MAPPO 优于 Single-Graph | 五种子 final held-out test、参数匹配 baseline | 等待正式实验，不能提前强写 |
| 角色对消息传播有效 | w/o Role-Pair Gate 重新训练消融 | 等待正式消融 |
| 任务支援关系有效 | w/o Task-Support Relation 重新训练消融 | 等待正式消融 |
| 方法具有场景时机鲁棒性 | 四场景 suite 结果 | 等待正式 validation/test |
| 可扩展到高保真仿真 | LAG/JSBSim replay 或可执行性验证 | 仅作为后续补充 |

## 11 下一步写作任务

1. 将 `docs/formal_methods_experiments_latex_zh.md` 整合进第 3-6 节，并转为 `paper_latex/` 中的正式 LaTeX 源文件。
2. 使用文献检索 skill 补充近五年相关工作，并替换正文中的泛化表述。
3. 等正式预算研究结果完成后，按照 `docs/formal_results_tables_and_figures_zh.md` 填入第 7 节主结果表、场景分解表、消融表和恢复过程曲线。
4. 使用统计审查 skill 检查 seed-aware bootstrap、置信区间和指标解释。
5. 使用图表 skill 生成主结果图、恢复过程曲线、消融图和机制案例图。
6. 最终英文投稿稿应从本中文稿、`docs/formal_methods_experiments_latex_zh.md` 和 `docs/formal_manuscript_draft_v1.md` 双向校对生成。
