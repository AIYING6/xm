# P0H 强二区新课题候选卡

## 候选一：不可靠通信下的认知一致性任务承诺

**暂定题目：** 面向通信不可靠异构无人机协同的认知一致性任务承诺学习

**一句话科学问题：** 当不同 UAV 无法确认队友是否获得同一任务信息时，如何在不假定可靠补发消息的条件下，对高收益联合动作、延迟承诺和安全降级作出一致决策？

**新决策对象：** 每个 agent 不只是选择物理动作，还选择 `commit / defer / fallback` 任务承诺状态；承诺只能基于可合法获得的局部历史与保守的共同信念下界。

**为何不是 DRTP/TATG/active diagnosis：**

- 不改变训练故障组采样；
- 不以历史编码恢复故障标签；
- 不主动探测故障原因；
- 核心损失不是回报加正则，而是避免不同私有信念下的联合动作不一致，并控制由保守降级产生的机会损失。

**必须成立的解析反例：** 两个局部历史对 agent 1 完全相同，但 agent 2 是否收到任务承诺不同；高收益联合动作只有双方执行才成功，单边执行产生严格损失。可靠 ack 不可用，因此普通 memory 无法消除信息等价类。若没有该反例，候选关闭。

**候选方法靶点：** 学习一个保守共同信念集合和任务承诺策略，在给定一致性风险阈值下最大化任务价值；理论目标是给出行动不一致概率或相对集中式 oracle 的性能损失上界。具体算法尚未冻结。

**最强近邻：** MACKRL；arXiv:2512.20778 的 inconsistent-belief action consistency；RA-L 2026 的 communication-value decision。

**非措辞性剩余差异要求：** 不允许通过选择性通信恢复一致 belief；研究对象必须是通信暂时不可用时的具身任务承诺与安全降级。若全文审计发现近邻已覆盖该设置，立即 NO-GO。

**环境闭环：**

1. 解析 electronic-mail/coordination game，用于证明信息等价类与一致性风险；
2. UAV 3DOF 任务加入需要同步承诺的侦察—中继—打击窗口，并冻结丢包/分区过程；
3. 可选社区环境：Hanabi 或 Level-Based Foraging 的 unreliable-ack wrapper。自建 wrapper 必须公开且与 UAV 使用同一数学问题。

**主要对照：** recurrent MAPPO、MACKRL/common-knowledge policy、selective-communication method、always-commit、always-fallback、centralized-information oracle。

**P1 成本：** 零训练；理论反例、合法信息审计、近邻全文审计和随机策略饱和检查。

**质量潜力：** 强二区高；若获得非平凡一致性界和第二环境，可冲击更高。  
**风险：** 理论要求高；与 2025 inconsistent-belief 工作可能重合。  
**当前裁决：** `CONDITIONAL_GO_TO_P1_NOVELTY_AND_COUNTEREXAMPLE_GATE`。

---

## 候选二：面向突发能力退化的反事实图干预规划

**暂定题目：** 基于反事实团队动力学的异构 UAV 突发能力退化恢复

**一句话科学问题：** 在未见的节点/链路能力损失发生后，策略能否在不在线更新参数的情况下，通过预测有限组合法图干预的任务后果选择恢复方案？

**新决策对象：** 选择一个可执行的 contingency option，而不是预测故障标签或更新采样概率。

**候选方法靶点：** 学习具有干预语义的团队 world model；对候选节点/链路能力干预进行短视野 counterfactual rollout，并使用模型不确定性拒绝不可信方案。

**必须避免的退化形式：**

- transformer world model + MAPPO 的模块组合；
- 通过 centralized state 泄漏真实故障；
- 把预测更准直接等同于恢复更好；
- 用在线 finetuning 替代决策时规划。

**严格反例：** 构造两个未见故障，使 model-free recurrent policy 的合法历史相同，但候选 contingency 的后果不同；同时证明至少一个可观测干预结果能改变恢复方案排序。若只能靠故障标签区分，候选关闭。

**最强近邻：** Collaborative Adaptation、Fastap、Relational Q-Functionals、分散 multi-agent world model、GalilAI。

**环境闭环：** UAV + MPE/VMAS capability-loss benchmark；需重新采集模型训练数据，不能使用现有 DRTP 遥测冒充 world-model 数据集。

**主要对照：** recurrent MAPPO、Collaborative Adaptation 类方法、latent-context adaptation、无干预 world model、oracle dynamics planner。

**质量潜力：** 强二区中高。  
**成本：** 很高，预计 200--400M steps，并需要模型校准和规划时延实验。  
**风险：** 最容易变成架构堆叠；“反事实”若无结构干预定义会被审稿人否定。  
**当前裁决：** `HOLD_HIGH_COST_REQUIRE_STRICT_INTERVENTION_GAP`。

---

## 候选三：带可行性证书的多层任务降级

**暂定题目：** 动态失效下异构无人机团队的可验证任务服务降级学习

**一句话科学问题：** 当当前团队能力不足以完成全部任务要求时，如何选择仍可满足的最高服务层，并避免继续执行已不可行的联合任务？

**新决策对象：** 从预先定义的任务服务层中选择 `full / reduced / safe-return`，并输出与该选择对应的可行性证据。

**候选方法靶点：** 学习任务层可达概率的保守下界，并将其作为 option selector；低层控制器固定或共享。算法价值必须来自有限样本下的保守可行性选择，而非重新做 task allocation。

**最强近邻：** 多层机器人任务控制、mission abort、resilient task allocation、CBF shield 与 conformal risk control。

**严格反例：** 同一物理状态下，不同能力集合使 full mission 的可行性跨越阈值，但 reduced mission 仍可行；继续 full mission 必须造成可测的超时或约束代价。

**环境闭环：** UAV 主环境 + 标准 multi-robot task-allocation/warehouse 环境。需明确定义服务层和任务规范，环境改动大。

**质量潜力：** 机器人期刊强二区中等；若只有仿真和经验阈值，退化为工程论文。  
**成本：** 中高；训练成本可控，但形式化任务规范、保证和第二环境成本高。  
**风险：** 与任务分配、abort 和 graceful degradation 文献高度拥挤，且可能偏离用户追求的 MARL 算法主线。  
**当前裁决：** `NO_GO_UNLESS_FORMAL_CERTIFICATE_IS_PRIMARY_CONTRIBUTION`。

## 候选排序

| 排名 | 候选 | 新问题清晰度 | 新颖性余量 | 可识别性 | 预计成本 | 强二区潜力 | 决策 |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | 认知一致性任务承诺 | 高 | 中 | 高（可先做解析反例） | 中高 | 高 | 进入 P1 零训练门 |
| 2 | 反事实图干预规划 | 中高 | 中 | 中 | 很高 | 中高 | 暂缓 |
| 3 | 可验证任务降级 | 高 | 低--中 | 高 | 中高 | 中 | 条件不足，不启动 |

