# Q0-R1：异构多频率连续控制 MARL 直接近邻红队

状态：`Q0_R1_PARTIAL__DIRECT_NEIGHBOR_GAP_PLAUSIBLE_BUT_NOT_ESTABLISHED`

日期：2026-08-11

## 1. 候选问题（冻结表述）

研究对象不是普通异步通信，也不是宏动作本身，而是：

> 多个异构 agent 在连续控制中具有不同、固定或状态相关的决策/执行频率时，CTDE 的轨迹对齐、回报归因和策略更新如何保持协同一致性。

候选问题必须同时包含：异构 agent、agent-specific control frequency、decentralized continuous control 和 CTDE。仅给 observation 加时间戳、把宏动作换个名称，不能算该问题的独立实例。

## 2. 直接近邻红队

| 工作 | 已覆盖内容 | 与候选问题的剩余差异 | 红队判断 |
|---|---|---|---|
| ACAC（ICML 2025） | 处理宏动作造成的异步经验；使用 agent-centric 编码、集中式 critic 注意力聚合及异步 GAE/PPO。 | 重点是 temporally-extended macro-action 的异步轨迹与回报对齐，不等同于异构 agent 的物理控制频率/执行周期不同。 | **强近邻，不能声称“首次异步 MARL”** |
| Xiao 等（2025）异步 MARL under partial observability | 在 decentralized、centralized 和 CTDE 范式下处理宏动作异步决策，并给出异步策略梯度。 | 仍以宏动作持续时间造成的异步为核心；尚未直接等同于 agent-specific multi-rate continuous plant control。 | **强近邻，必须做结构差异** |
| Heterogeneous-Agent RL（JMLR 2024） | 异构 agent 的优势分解、顺序更新和异构策略/基准。 | 关注 agent heterogeneity 与更新顺序，不以不同物理控制频率为核心。 | **异构性近邻，但非多频率近邻** |
| EvoControl（ICML 2025） | 单智能体高频连续控制中的 slow policy / fast controller 多频率双层控制。 | 不是多智能体 CTDE；没有团队级跨 agent 频率错位、联合 credit assignment 问题。 | **控制频率近邻，非 MARL 近邻** |
| 异步多机器人协同探索（2023） | 指出机器人原子动作耗时不同会破坏同步 MARL 的现实假设。 | 主要是异步执行应用与系统建模，未给出本候选所需的异构多频率连续 CTDE 算法缺口。 | **应用动机近邻** |
| Multiagent model-based credit assignment for continuous control（2021） | 连续控制中的去中心化 agent 建模和 agent-specific credit assignment。 | 未处理 agent-specific control frequency 引起的跨速率 return/advantage 对齐。 | **credit-assignment 近邻** |

## 3. 红队结论

当前文献支持“异步/宏动作 MARL”和“多频率连续控制”分别都已有成熟先例；因此以下表述被永久禁止：

* “首次研究 asynchronous MARL”；
* “首次研究 multi-rate control”；
* “现有方法没有处理异步经验”。

检索后仍留下一个**可能但尚未证明**的交叉缺口：固定或状态相关的 agent-specific control frequency 作为物理执行约束时，如何在连续控制 CTDE 中进行跨速率 trajectory/advantage alignment，并保持 decentralized policy 的协同。ACAC 和宏动作异步方法是必须正面比较的近邻；EvoControl 说明单智能体 multi-frequency 不能作为 MARL 新颖性依据。

因此本阶段不放行算法实现，裁决为：

> `Q0_R1_PARTIAL__DIRECT_NEIGHBOR_GAP_PLAUSIBLE_BUT_NOT_ESTABLISHED`

## 4. 放行条件（尚未满足）

只有在下一轮文献核验能把下列差异写成明确的机制定义，才可进入标准 benchmark 现象审计：

1. **频率语义**：区分宏动作持续时间与 agent 的独立物理决策/执行周期；
2. **训练对象**：说明现有异步 GAE、macro-action value 或顺序更新为何不能直接处理该周期错位；
3. **可证伪现象**：在不改 UAV 的标准连续多智能体 benchmark 上，同频与异频条件之间出现可重复的 coordination/credit degradation；
4. **最小机制**：候选算法只能针对跨速率对齐或更新，不得先堆叠 memory、graph、通信或层级模块。

在这些条件满足前，禁止代码、训练和 UAV 任务改动。下一状态最多为 `Q1_MULTIRATE_MARL_PHENOMENON_AUDIT`，不能直接进入方法实现。

## 5. 来源

* ACAC：<https://proceedings.mlr.press/v267/jung25a.html>
* 异步 MARL under partial observability：<https://journals.sagepub.com/doi/abs/10.1177/02783649241306124>
* Heterogeneous-Agent RL：<https://www.jmlr.org/papers/v25/23-0488.html>
* EvoControl：<https://openreview.net/forum?id=JAWKe4vg0l>
* 异步多机器人探索：<https://arxiv.org/abs/2301.03398>
* 连续控制中的多 agent credit assignment：<https://arxiv.org/abs/2112.13937>

