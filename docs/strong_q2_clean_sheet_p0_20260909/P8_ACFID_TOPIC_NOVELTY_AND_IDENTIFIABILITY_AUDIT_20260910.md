# P8 ACFID 选题新颖性与可识别性审查

## 决策

**锁定 ACFID 为新主线，但目前只授权 P0 零训练交互门，不授权 9M 学习实验。**

暂定题目：**面向未见组合故障的异构多无人机零样本协同恢复：动作条件故障交互分解**。

该题比 DRTP 和 TC-CRC 更接近用户要求的“强二区下限、一区上限”：它研究的不是训练样本如何重加权，也不是冻结策略如何选择性部署，而是一个新的决策学习问题——如何从低阶故障经验中恢复未见高阶组合故障下的动作排序。

## 最近邻结论

截至 2026-09-10 的检索支持以下边界：

1. UAV 故障恢复和容错 MARL 已存在。NRHG 已使用异构图网络和 MARL 调度幸存 UAV，应对级联失效后的覆盖与吞吐恢复（DOI: 10.1016/j.ress.2026.112320）。因此，“用 MARL 做多 UAV 故障恢复”不是创新。
2. UAV 故障鲁棒策略已覆盖掉队、通信中断、传感噪声和执行器故障。动作—观测条件递归网络也已出现。因此，“action-conditioned”不能泛指把上一动作送入 RNN；本文必须限定为**恢复动作条件的故障交互项**。
3. 零样本组合泛化是成熟问题，未见复合故障诊断也已有专门模型。因此，“测试未见组合”本身不是创新。
4. MARL 的价值分解、协调图和潜在交互价值已有长期积累。因此，不能把普通 agent-wise value decomposition 或图混合网络改名为 fault interaction decomposition。
5. 当前检索尚未发现同时满足以下组合的直接近邻：面向异构多 UAV 协同恢复；按 primitive fault set 分解；交互项随恢复动作变化；训练排除高阶组合；以 held-out compound-fault action regret 为主要端点；以任务依赖结构约束交互。这个组合构成目前可守住的研究缺口，但仍需在正式论文检索中继续核验。

主要核验来源：

- Network recovery for UAV-assisted IoTs after cascading failures with heterogeneous graph neural networks: https://doi.org/10.1016/j.ress.2026.112320
- Multi-source plume tracing via multi-agent reinforcement learning under common UAV-faults: https://doi.org/10.1016/j.mlwa.2025.100737
- Environment Generation for Zero-Shot Compositional Reinforcement Learning: https://openreview.net/forum?id=CeByDMy0YTL
- Understanding Value Decomposition Algorithms in Deep Cooperative Multi-Agent Reinforcement Learning: https://arxiv.org/abs/2202.04868
- Collaborative Multiagent Reinforcement Learning by Payoff Propagation: https://jmlr.org/papers/v7/kok06a.html
- A Survey of Zero-shot Generalisation in Deep Reinforcement Learning: https://arxiv.org/abs/2111.09794

## 必须修正的两个地基问题

### 1. 故障可观测性

原方案没有明确控制器是否知道故障身份。若直接输入 held-out 组合的类别 ID，所谓零样本可能退化为显式标签上的函数插值；若完全不知道任何故障迹象，则任务同时包含诊断和恢复，无法识别交互分解的贡献。

冻结方案研究**检测后的恢复**：策略只能获得执行时因果可得的 primitive degradation signatures 与局部任务状态，不获得组合类别 ID、未来信息或最优动作。论文不能声称解决零样本故障诊断。

### 2. 任务依赖图的角色

任务依赖图必须在实验前由系统接口定义并冻结。它只用于正则化或屏蔽候选交互，不能由最终性能反推；同时必须设置 unstructured second-order interaction 对照，否则无法区分“二阶模型有效”和“结构先验有效”。

## 问题—方法—证据—结论闭环

| 环节 | 冻结内容 |
|---|---|
| 问题 | 基础故障组合数量指数增长，组合效应可能改变恢复动作排序 |
| 方法 | 学习 nominal、单故障主效应与动作条件二阶交互；用预注册任务依赖图正则化交互支持 |
| 主要对照 | Fault-aware MAPPO、additive fault value、unstructured second-order、graph-regularized ACFID |
| 主要端点 | 未见组合上的 recovery-action regret，而非只看平均 return |
| 机制证据 | 非加性、动作排序变化、additive 失配、二阶 held-out 预测、结构对齐 |
| 可允许结论 | 在冻结任务与故障族中，低阶动作条件交互是否提高未见组合恢复决策 |
| 不允许结论 | 普遍解决复合故障、零样本诊断、所有高阶交互都很小、现实飞行可靠性保证 |

## 为什么它不是“二阶展开换皮”

只有同时满足四项，ACFID 才成立：

1. 交互对象是 fault set，不是 agent-wise value mixing；
2. 交互随 recovery action 改变，并以动作排序或 regret 验证；
3. 高阶组合严格从训练、验证和调参流程中排除；
4. 任务依赖结构相对无结构二阶模型带来可识别的泛化或样本效率收益。

如果第 2 或第 4 项失败，论文创新会明显降级，必须按冻结停止规则终止，而不是训练后包装。

## P0 设计

P0 不训练神经策略。它在可克隆决策状态上枚举恢复动作，对 nominal、single、pair 及 held-out compound fault 做共同随机数的短时或完整时域 rollout，估计：

\[
I_{ij}(s,a)=Q(s,a,\{i,j\})-Q(s,a,\{i\})-Q(s,a,\{j\})+Q(s,a,\varnothing).
\]

必须同时通过 G1–G6：基础可学习性、非加性、动作决策相关性、加性模型不足、二阶 held-out 泛化和结构对齐。详细阈值与停止规则见 `configs/p8_acfid_final_topic_freeze_20260910.json`。

## 理论边界

若所有动作的近似价值误差满足 `|Q-\hat Q|<=epsilon`，则基于 `\hat Q` 的贪心动作相对真实最优动作的 regret 不超过 `2 epsilon`。这是一条通用近似决策结论，只能作为理论起点，不能单独支撑一区创新。

“无共享后继变量时交互为零”或“交互随任务图距离指数衰减”必须在明确的转移、奖励、策略耦合与有限时域假设下证明；证明完成前统一标记为研究目标。

## 对 P7 TC-CRC 的处理

TC-CRC 的 Stage 0/1 结果保留为未来可能的部署风险层，不再作为新主线。尚未运行的稀疏支持 Stage 2 暂停，避免在主问题已经切换后继续消耗研究注意力。

## 最终判断

- 创新上限：高于 DRTP 和 TC-CRC；具备强二区设计空间。
- 一区资格：取决于结构性稀疏理论、强组合泛化证据，以及高保真/实体验证，当前不能保证。
- 技术风险：高，但可以被 P0 在训练前暴露。
- 当前动作：建设最小 6-UAV 环境与反事实交互审计，不启动 RL。
