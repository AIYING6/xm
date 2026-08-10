---
title: "受限通信异构无人机协同中的来源分离冲突融合决策"
language: zh-CN
status: pre-result manuscript scaffold; F1 training in progress; F2 not accessed
protocol: V1_9_PCRF_R2
---

# 受限通信异构无人机协同中的来源分离冲突融合决策

> 本稿仅包含已经冻结的方法、问题和评估协议，不包含 F1 验证曲线、F2 确证评估或性能结论。任何“优于”“显著改善”“机制成立”的表述，必须等待 F2 完成并通过 Paper P0 Audit 后补写。

## 术语与主张边界

| 术语 | 本文固定含义 |
|---|---|
| PCRF-R2 | 将直接局部感知（P）与实际递送且缓存有效的通信证据（C）分别编码，并以冲突条件融合的策略表示。 |
| single-R2 | 接收与 PCRF-R2 完全相同原始 P/C 字段，但采用来源感知的统一图编码器的主比较方法。 |
| matched-nongraph-R2 | 接收相同原始 P/C/context 字段、但不使用图消息传递的匹配信息比较方法。 |
| RMTE\(_\tau\) | 从故障开始到首次稳定合法任务链建立的受限平均时间；终端任务失败在窗口内按未建立处理。 |
| RMPE\(_\tau\) | 仅由真实物理状态定义的受限平均 physical-engagement-readiness 时间；为次级构念有效性终点。 |

本文检验的主假设是：在严格的 recipient-specific actor information contract 下，保留 P/C 两类合法证据的来源结构，并以冲突条件融合它们，是否相较于接收相同原始字段的来源感知统一图表示，更有利于预定中继失效协同任务中的端到端稳定任务链建立。该假设不是“首次分离感知与通信”的宣称，也不预设 PCRF-R2 对所有方法、场景或时间尺度具有普适优势。

## 摘要（F2 前占位稿）

异构无人机协同拦截依赖局部感知与环境递送通信共同维持可执行的任务链。当中继节点在有限通信、时延、丢包和间歇感知条件下失效时，策略不仅需要获得信息，还需要在信息来源不一致、不可用或过期时形成可审计的决策表示。本文研究预定中继失效任务中的端到端稳定任务链建立问题。我们提出来源保留冲突融合表示（provenance-preserving conflict-aware fusion representation, PCRF-R2）：策略将直接局部感知与实际递送且缓存有效的通信证据分别编码，仅使用接收方在当前时刻合法可得的字段，并通过“基线门控加冲突偏移”融合两类证据。为避免把信息优势误认为结构优势，PCRF-R2 与来源感知统一图、匹配信息非图方法共享同一原始 actor 信息集、训练预算和 checkpoint-selection 规则。主要终点为故障开始后首次稳定合法任务链建立的 restricted mean time to establishment（RMTE）；不可逆终端任务失败不被当作普通右删失。我们另设物理 engagement readiness 的 RMPE 次级终点，以检验任务链建立与独立物理任务状态之间的关联。正式多 seed 训练完成后，将在未访问的确认性评估集上按预冻结协议报告比较结果、失败分解和方法边界。

**关键词：** 异构无人机；多智能体强化学习；受限通信；信息溯源；图表示；故障协同；事件时间终点

## 1 引言

多无人机协同决策需要将异构平台的局部感知、角色能力与通信状态转化为可执行的联合行为。在追踪、拦截和中继支撑等任务中，通信并非总是即时、完整或可靠：包可能未递送、延迟、丢失，或在缓存超过有效期限后不再代表当前可用证据。中继节点的预定失效进一步使这种不确定性集中暴露。对于执行期策略而言，关键问题不是集中训练阶段是否可以访问完整状态，而是每个接收方在该时刻究竟合法知道什么，以及这些证据来自直接感知还是历史递送通信。

现有多智能体强化学习与图策略方法为协同决策提供了重要基础，但“把可用信息拼接后送入图网络”不足以自动保证信息边界公平。若未递送、过期或仅由模拟器全局状态提供的字段进入 actor，图结构上的邻接掩码并不能消除已发生的特征泄漏。反之，若比较方法得到不同粒度的原始信息，则观测到的性能差异无法归因于表示结构。因此，受限通信协同中的方法比较必须同时解决两类问题：recipient-specific information provenance，以及在合法多来源证据之间如何表示一致与冲突。

本文聚焦一个受控的 3DOF 异构无人机协同任务。蓝方由 scout、relay 与 attacker 等异构角色组成，在预定中继失效期间维持或重新建立稳定的合法任务链。我们不将终局成功率作为唯一问题答案，而将故障开始后首次稳定任务链建立的时间作为主要任务终点。该定义使“协同何时重新可用”成为可预注册、可逐 episode 追溯的对象，并显式区分已建立、终端失败以及窗口内仍未建立三类结局。

为检验来源结构的作用，本文提出 PCRF-R2。它只保留两个证据来源：P 为接收方对目标的直接局部感知；C 为实际递送且未过期的通信 packet/cache 证据。PCRF-R2 以独立 P/C 编码器提取表示，并以可审计的基线门控与冲突偏移融合；无冲突中性状态精确回到基线，单一合法来源时权重退化为一。主比较 single-R2 则接收完全相同的来源标记原始字段，但采用一个统一图编码路径。由此，主要比较针对来源分解与融合归纳偏置，而非额外 actor 信息、参数规模或训练预算。

本文的预结果贡献如下。

1. 给出一个严格的接收方特异信息合约，将直接局部感知与实际递送、缓存有效的通信证据分离，并明确排除 pending、dropped、expired 与 simulator-global 信息。
2. 提出 PCRF-R2：一个仅含两来源的基线加冲突偏移融合结构，其动态项仅使用合法的来源可用性差异、内容分歧、通信 age 和 confidence。
3. 冻结匹配信息的主比较、终端失败感知的 RMTE 终点、物理 RMPE 次级终点、事件记录、checkpoint selector 和未访问确认性评估流程，为后续证据提供可复核边界。

## 2 相关工作与研究定位

### 2.1 受限通信下的多智能体协同

学习通信、集中训练分散执行和图表示已经广泛用于多智能体协同。它们说明交互结构能够影响策略学习，但不能替代执行期信息合法性的定义。本文不主张首次使用图网络、通信建模或感知/通信分离；本文的定位是将实际递送、缓存有效性与接收方特异可得性纳入 actor 的输入合约，并在该合约下比较不同表示。

### 2.2 面向无人机协同的图策略

图策略可将平台、目标、链路几何和角色上下文组织为节点与边。然而，图邻接为零只限制某一聚合通路，并不保证节点特征、残差、pooling 或共享观测中不存在相同信息。本文因此将“先过滤来源合法性、再构造节点和边、最后编码”作为实现顺序，并要求 PCRF-R2、single-R2 与 matched-nongraph-R2 在进入各自编码器前通过原始输入 hash/parity 审计。

### 2.3 失效协同与评价终点

已有失效韧性研究常报告任务是否完成、平均回报或恢复成功率。对预定失效暴露任务而言，这些指标可能掩盖恢复的时间过程，也可能因终端失败被错误当作普通 right-censoring 而产生乐观偏差。本文将首次稳定合法任务链建立定义为事件；collision、constraint violation 等不可逆终端结果在相应受限窗口内视为未建立，而不是从风险集删除。该选择服务于本任务的 RMTE estimand，不等同于把所有任务问题都改写为传统生存分析。

> **文献边界。** 本节的正式引文将在投稿前依据作者实际核验的原始论文补齐；不得用综述或未核验条目替代对具体方法的来源归属。

## 3 问题定义与信息合约

### 3.1 任务与执行语义

每个 actor 在执行时仅使用自身物理状态、合法本地任务上下文、直接感知 P、实际递送且缓存有效的 C，以及由这些字段构造的关系/几何特征。集中训练阶段的 critic 可使用共享训练状态，但 critic-only 信息不得返回 actor。实验中的中继节点在第 40 步开始失效并持续 80 步；稳定任务链事件要求连续 \(K=4\) 步满足预定义的合法链条件。

令 \(i\) 为接收方。其直接感知来源和通信来源分别记为

\[
G_i^P=\{x_i^{self},m_i^P,\widehat y_i^{direct},q_i^{direct}\},
\]

\[
G_i^C=\{x_i^{self},m_{ij}^C,p_{j\rightarrow i}^{delivered},
\operatorname{age}_{ij},\operatorname{confidence}_{ij}\}_{j\ne i}.
\]

其中，\(m_i^P\) 表示直接感知可用性；\(m_{ij}^C\) 仅在 packet 已实际递送且其目标声明仍在最大缓存年龄内时可用。超过 `max_target_message_age_steps` 的 packet 必须在 C 节点、C 邻接和 C 分支构造之前完全移除；其 payload 不得以“低 confidence”或“大 age”形式继续影响 actor。

共享上下文 \(z_i^{ctx}\) 仅包含接收方自状态、角色、局部任务状态、局部攻击可用性和固定能力信息。它不含目标估计、缓存目标估计、packet-derived age/confidence 或 teammate payload，从而避免来源经公共观察编码器旁路泄漏。

### 3.2 终点与结局分解

令 \(T_E\) 为故障开始后首次稳定合法任务链建立的时间。若在终端任务失败之前建立任务链，则 \(T_E\) 取建立时间；若 collision、constraint violation 或其他不可逆终端任务失败先发生，则令 \(T_E=\infty\)。对固定分析窗口 \(\tau\)，主要终点为

\[
\operatorname{RMTE}_{\tau}=\mathbb{E}[\min(T_E,\tau)],
\]

数值越小表示在窗口内越早建立任务链。本文预冻结 \(\tau=80\) 为主要窗口、\(\tau=220\) 为次级窗口。每个窗口同时报告 establishment incidence、terminal-failure incidence 与 active-but-unestablished proportion，而不使用语义混杂的单一 censoring rate。

RMPE\(_\tau\) 是独立的次级物理终点，描述故障开始后首次连续四步达到 physical-engagement-readiness 的时间。该事件只依赖评估器读取的物理状态和冻结阈值，不引用 `chain_closed`、PCRF 图/门控/关系或通信内部 predicate。RMPE 不进入 actor、reward 或 checkpoint selection，也不替代 RMTE 的主地位。

## 4 PCRF-R2 方法

### 4.1 两来源编码

PCRF-R2 为 P 和 C 设置独立的图编码器：

\[
h_i^P=m_i^P F_P(G_i^P),\qquad h_i^C=m_i^C F_C(G_i^C).
\]

关系掩码只在合法特征已经构造后用于图聚合；它不能被用作特征合法性的替代。P 或 C 不可用时，对应分支在进入编码前被掩蔽为零。若两类来源都不可用，\(h_i=0\)，策略只能依赖 \(z_i^{ctx}\)。

### 4.2 基线加冲突偏移融合

融合描述符仅由两来源的合法字段构成：

\[
c_i=[a_i^P-a_i^C,\ d_{PC},\ \operatorname{age}_C,\ 1-\operatorname{confidence}_C].
\]

其中 \(d_{PC}\) 是直接目标声明与已递送 C 目标声明之间的掩蔽内容分歧；它不是将不同端点类型强行比较得到的 adjacency Jaccard。令 \(\beta\) 为无动态输入的两 logit 基线，\(\Delta\) 为冲突偏移，则

\[
\ell_i=\beta+\Delta(c_i)-\Delta(0).
\]

因此在中性状态 \(c_i=0\) 时，\(\Delta(0)=0\) 且门控精确回到基线。可用性掩蔽后的融合为

\[
w_{ir}=\frac{m_i^r\exp(\ell_{ir})}{\sum_{s\in\{P,C\}}m_i^s\exp(\ell_{is})},\qquad
h_i=w_{iP}h_i^P+w_{iC}h_i^C.
\]

单一来源合法时其权重精确为一。该结构的目的不是声称在线修复物理通信，而是测试来源保留和合法冲突描述是否构成有用的表示归纳偏置。

### 4.3 公平比较

PCRF-R2、single-R2 与 matched-nongraph-R2 接收完全相同的 P/C/context 原始字段。single-R2 保留 P/C source tag、mask、age、confidence、几何和角色/任务上下文，但以一个统一编码器处理 \(P\cup C\)。matched-nongraph-R2 在来源保留 pooling 后不进行图消息传递。三者的隐藏维度分别为 128、147 与 152，以控制参数量差异；训练预算、环境、packet/cache semantics、验证事件与 selector 相同。

## 5 实验协议与结果位置

### 5.1 正式训练与 checkpoint 冻结

F1 对三个方法各训练 8 个正式 seed，共 24 个 runs。每个 run 使用 300 updates、8 个并行环境、128 rollout steps、4 个 PPO epochs，并在 update 1、10、20、\(\ldots\)、300 保存不可变 checkpoint、SHA256、episode-level validation event records 和 summary。训练期验证只用于预冻结 selector：依次比较较低 RMTE80、较高 establishment probability、较低 terminal-failure incidence、较低 RMTE220 和更早 update。F1 validation 不是 confirmatory evidence。

### 5.2 未访问确认性评估

F2 仅在 F1 的 24 个 selected checkpoint hash 全部冻结后，经单独授权执行。确认性 episode bank 与训练 seed、validation episode IDs 独立；每个 checkpoint 使用相同的配对 F2 episode 标识。主分析比较 PCRF-R2 与 single-R2，次级分析比较 matched-nongraph-R2。统计层级为 training seed \(\rightarrow\) paired evaluation episodes；结果应报告效应方向、hierarchical paired-bootstrap interval、establishment/terminal-failure/active decomposition 与预冻结的实际意义阈值。

### 5.3 结果待填充位置

| 证据问题 | 预冻结比较 | 允许写入的结论条件 | 当前状态 |
|---|---|---|---|
| 主表示比较 | PCRF-R2 vs single-R2 | 8 seed 同方向、bootstrap 支持较早 establishment，且无重大 establishment trade-off | 等待 F2 |
| 匹配信息非图比较 | PCRF-R2 vs matched-nongraph-R2 | 报告为次级 matched-information 证据 | 等待 F2 |
| post-onset 机制 | common-onset-state diagnostic | 与端到端 F2 一致时才加强 post-onset 解释 | 尚未授权执行 |
| 物理构念关联 | RMTE 与 RMPE | 仅支持 physical-engagement readiness，不得写 capture/mission completion | 等待 F2 |

## 6 讨论与结论（F2 前边界）

本文当前可成立的是方法与证据设计层面的结论：PCRF-R2 将合法直接感知与合法通信证据分离，比较方法接受匹配的原始 actor 信息，并以明确的 terminal-outcome 语义记录任务链建立时间。尚不可成立的是性能优越、冲突偏移的机制有效性、OOD 泛化或独立拦截成功主张。

在 F2 之后，若主比较和次级诊断均支持 PCRF-R2，论文可将结论限定为该冻结任务/协议下的证据；若端到端比较支持但 common-onset diagnostic 不支持，则只能报告端到端策略表现，不得归因于纯 post-onset conflict handling；若主比较不支持，则撤销 multi-source representation superiority 主张，同时完整报告结果与失败边界。

