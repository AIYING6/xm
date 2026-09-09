# P1D：训练前算法与证据合同

## 当前决策

`P1D_CONDITIONAL_PASS_TO_IMPLEMENTATION_AUDIT_ONLY`

P1A 的最近邻差异、P1B 的最小信息反例和 P1C 的 UAV 具身语义均已通过。下一步只允许实现和审计候选机制，不允许直接启动性能训练。

## 唯一允许研究的决策问题

在当前任务窗口内无法依靠额外可靠通信恢复共同认知时，智能体应依据其合法局部历史，在 `commit / defer / fallback` 三种任务模式之间决策。目标不是估计隐藏的全局投递真值，而是在不可消除的接收不确定性下控制单边承诺风险与机会损失。

## 候选机制的最低数学定义

候选方法必须显式处理同一合法局部历史对应的接收状态等价类。对智能体 \(i\) 的局部历史 \(h_i\)，定义队友已进入兼容承诺状态的概率区间

\[
\mathcal P_i(h_i)=[\underline p_i(h_i),\overline p_i(h_i)].
\]

部署决策不得直接读取真实投递、ack 或队友 belief，而应在该合法信息集上比较三种任务模式的风险调整价值：

\[
m_i^*=\arg\max_{m\in\{C,D,F\}}
\inf_{p\in\mathcal P_i(h_i)}
\left(\mathbb E[V_m\mid p]-\lambda R_m(p)\right).
\]

其中 \(C,D,F\) 分别表示 commit、defer 和 fallback；\(R_m\) 必须包含可观测定义的单边承诺代价，而不能用隐藏真值在执行期修正动作。

## 不能退化成的实现

以下任一情形出现即 P1D 失败：

- 仅在 MAPPO 后增加一个 commitment 分类头；
- 仅增加 belief/ack 预测辅助损失，但部署动作仍由原策略直接给出；
- actor 输入真实消息投递状态、全局 ack、队友隐状态或集中式 belief；
- 通过新增可靠通信轮消除 P1B 中冻结的不确定性；
- 只做 reward shaping、阈值扫描或动作 mask；
- 用更大网络容量替代信息结构机制。

候选方法必须在部署时真实改变 `commit / defer / fallback` 的选择，并能通过反事实单元测试证明：保持物理状态和局部历史不变，仅改变合法的接收不确定性区间时，决策边界按 P1B 的解析顺序变化。

## 必须冻结的匹配对照

| 对照 | 目的 | 公平性要求 |
|---|---|---|
| Recurrent MAPPO | 检查普通历史记忆是否已足够 | 相同 actor 参数预算、局部历史和训练步数 |
| Risk-matched recurrent MAPPO | 排除仅由风险惩罚造成的收益 | 使用相同单边承诺代价，但不使用信息集决策层 |
| Common-information/communication baseline | 对齐最近邻方法类别 | 不允许额外可靠 ack；相同通信机会与消息预算 |
| Oracle upper bound | 量化信息损失，不作为公平主基线 | 仅评估时读取投递真值，明确标为上界 |
| Always-commit / always-fallback | 检查任务是否被常数策略支配 | 相同评估带 |

拟议方法与主基线的网络参数差异必须控制在 5% 内；若无法做到，则使用容量匹配的 dummy layers 并同时报告参数量。

## 主要端点

训练 seed 是唯一独立统计单位。每个 seed 在固定终点评估中同时报告：

1. 任务回报与成功率；
2. 单边承诺率；
3. 双边承诺成功率；
4. defer 与 fallback 率；
5. 机会损失（可安全承诺却降级）；
6. 碰撞、约束违规和超时；
7. 与 oracle 的价值差距；
8. 决策一致性风险。

不能将同一训练 seed 的 episode、条件或智能体数量当作独立重复。

## P2 小试验预算与停止规则

- 3 个全新训练 seed；
- 每个方法每 seed 最多 1M environment steps；
- 总训练预算不超过 15M environment steps；
- 所有方法使用同一冻结 evaluation tape；
- 不根据中间曲线挑 checkpoint，使用固定终点；
- pilot 前冻结阈值，不因结果调整。

在训练前必须先通过以下实现审计：

1. 私有信息无泄漏；
2. 反事实决策边界与 P1B 一致；
3. recurrent baseline 容量匹配；
4. 常数策略均不支配；
5. 随机策略和脚本策略能够覆盖成功、单边承诺与安全降级；
6. 日志能按 seed 还原全部主要端点。

P2 只有在三 seed 中至少两 seed 同时满足以下条件时才允许进入正式实验：相对容量匹配 recurrent MAPPO 降低单边承诺率，任务回报不发生灾难性下降，且增益不是由 always-fallback 导致。否则停止，不扫阈值、不追加 seed。

## 仍未解决的风险

- 与 action-consistency/common-knowledge 最近邻的算法差异仍需在实现后逐行复核；
- 概率区间如何从合法历史校准尚未冻结；
- 影子任务价值是可识别性构造，不是现实任务标定；
- 单一 UAV 环境不足以支撑强二区，后续仍需第二个非 UAV 协调基准或理论界，但只有 P2 通过后才值得投入。
