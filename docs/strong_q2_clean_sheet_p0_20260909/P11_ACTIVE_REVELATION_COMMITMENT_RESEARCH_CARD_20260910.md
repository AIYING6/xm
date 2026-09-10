# P11 主动需求揭示—联盟承诺研究卡

## 1. 当前判定

`P11A_ANALYTIC_PASS / P11B_CONDITIONAL_PASS / P11C_STOP / NO_TRAINING`

泛化的“动态任务—角色联合分配”不予采用。近期工作已经覆盖动态任务到达、异构资源、时窗、联盟形成、在线重分配和任务—轨迹联合决策。P11 只保留一个更窄、可证伪的候选问题：

> 当任务的能力需求尚未揭示、专业 UAV 又具有稀缺的未来机会价值时，团队应何时主动侦察需求，何时立即承诺专业平台，何时保留该平台？

## 2. 为什么不是普通任务分配

普通动态任务分配主要在已知任务属性上优化 UAV—任务匹配、路径、时窗或联盟。P11 的决策对象包含一个会改变后续可行动作的信息获取操作：

1. `commit`：立即把稀缺专业平台投入当前任务；
2. `reserve`：放弃当前不确定任务，保留专业能力；
3. `inspect`：先由侦察平台揭示能力需求，再形成联盟。

因此，核心耦合是“信息价值—截止时间—稀缺能力机会成本”，而不是把不确定性作为网络输入后继续做一次分配。

## 3. 最近邻风险

| 最近邻 | 已覆盖内容 | 对 P11 的威胁 | P11 必须证明的差异 |
|---|---|---|---|
| Rossano et al., 2026, uncertainty-aware MRTA | 未知任务能力需求；让潜在专业平台靠近不确定任务 | **高**：几乎覆盖稀缺能力预留动机 | P11 必须包含显式、可选择、会消耗时间的主动需求揭示动作，而非仅优化邻近部署 |
| Choudhury et al., dynamic MRTA under uncertainty | 动态任务、完成不确定性、时窗、在线分配 | 中高 | 证明信息动作改变 belief 和可行联盟，而非一般随机任务结果规划 |
| Gosrich et al., online coordination with precedence | 在线重分配、联盟、任务依赖 | 中 | 研究对象必须是潜在需求揭示和承诺机会成本，不是 precedence 调度 |
| SCoBA / auction / coalition literature | 时窗、联盟、在线调度 | 中 | 受控比较应隔离 active revelation，而非只与简单 greedy 比较 |
| Dynamic coalition formation via RL | 联盟和路径联合学习 | 中高 | 不能把 GNN/MARL 架构本身写成创新 |

检索入口：

- Uncertainty-Aware Multi-Robot Task Allocation With Strongly Coupled Inter-Robot Rewards: https://arxiv.org/abs/2509.22469
- Dynamic Multi-Robot Task Allocation under Uncertainty and Temporal Constraints: https://arxiv.org/abs/2005.13109
- Online Multi-Robot Coordination and Cooperation with Task Precedence Relationships: https://arxiv.org/abs/2509.15052
- Dynamic Coalition Formation and Routing for MRTA via RL: https://www.marmotlab.org/publications/56-ICRA2024-MRTA.pdf
- Heterogeneous MRTA for Long-Endurance Missions in Dynamic Scenarios: https://ieeexplore.ieee.org/document/11219201

## 4. P11-A 解析可识别性

P11-A 在运行前冻结 120 个组合条件：需求信念、未来专业能力价值、侦察成本和截止时间余量。总任务价值固定，不训练网络。

| 指标 | 结果 | 门槛 | 判定 |
|---|---:|---:|---|
| commit 最优 | 51.67% | 每类≥10% | PASS |
| reserve 最优 | 17.50% | 每类≥10% | PASS |
| inspect 最优 | 30.83% | 每类≥10% | PASS |
| 同几何、异信念决策分叉 | 20.00% | ≥20% | PASS |
| oracle 相对最佳常数策略增益 | 1.387 | ≥0.500 | PASS |

最佳常数策略为 always-commit，平均价值 10.000；逐条件 oracle 为 11.387。主动侦察具有正价值但并非普遍最优，避免了“always inspect”饱和。

## 5. P11 预期贡献结构

当前只能写成待核验命题，不能写成既成创新：

1. **问题贡献候选：** 将潜在能力需求下的主动信息获取与稀缺 UAV 联盟承诺统一为序贯决策问题；
2. **方法贡献候选：** 学习 belief-conditioned revelation/commitment policy，同时显式表示专业能力机会成本；
3. **证据贡献候选：** 在同一环境中控制任务、路径、能力和训练预算，只改变是否建模信息动作及长期承诺价值。

## 6. 预先设计的因果对照

- `Reactive-known-only`：不侦察，需求揭示后才响应；
- `Always-inspect`：所有不确定任务均侦察；
- `Uncertainty-aware allocation without active sensing`：知道需求分布，但没有信息动作；
- `Myopic active sensing`：只计算当前任务的信息价值，不计未来专业能力机会成本；
- `P11 full`：主动揭示与跨任务承诺价值联合决策。

关键消融已经在训练前定义：去掉主动信息动作、去掉未来机会价值、去掉 belief 更新。若这些差异不能分别对应可观测失败模式，P11 不进入训练。

## 7. 下一门与停止条件

P11-B 必须精读并建立最近邻差异矩阵，尤其是 Rossano et al. 2026。只有同时满足以下条件才建环境：

- 最近邻没有同时建模“可选择的主动需求揭示 + 揭示时延 + 稀缺能力未来机会成本 + 联盟承诺”；
- 差异能由受控 baseline/ablation 识别；
- 不依赖“用于 UAV”或“换成 MARL”作为新颖性；
- 任务需求的隐藏与揭示具有现实传感语义，而不是人为隐藏标签。

任一项失败，则 P11 在文献门关闭，不写环境、不训练。

## 8. 当前证据边界

P11-A 只证明一个解析决策问题可以形成三类非平凡最优区域，不能证明真实 UAV 环境可学、方法新颖或能提升性能。训练授权仍为 `false`。

## 9. P11-C 最终选题判定

P11-C 将抽象的 `inspect` 替换为具身过程：侦察 UAV 必须飞抵当前任务区域并驻留观测，观测带噪声，信息到达后依据 Bayes 后验决定是否承诺稀缺专业 UAV；飞行时间、任务截止时间、未来任务距离和机会价值均进入效用。对照包含立即承诺、保留专业平台，以及允许专业平台在外生揭示期间选择最优前摄位置的 AURA-style 强基线。

冻结的 288 个组合中，几何变化在 25.00% 的固定价值/信念组内改变最优动作，噪声观测在 24.31% 的条件中改变后续承诺，说明任务不是静态标签分类。然而，主动揭示的最优占比为 0，击败最佳非主动策略的条件占比为 0，平均价值差为 -0.943。信息动作确实改变了信息状态，但其时间、能量和噪声代价没有产生可识别的净任务价值。

因此 P11 不能作为真正的新选题进入训练。这里不通过调整侦察成本、外生揭示延迟或任务先验来制造正结果；这种事后调参会把研究问题退化为人为构造。P11 正式关闭，已用环境步数和 PPO 更新数均为 0。
