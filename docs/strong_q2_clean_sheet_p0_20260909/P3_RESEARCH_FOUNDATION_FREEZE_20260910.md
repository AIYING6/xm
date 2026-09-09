# P3 研究地基冻结：训练前创新、机制与证据闭环

## 当前决策

P3 暂停在训练门外。Q0 已证明环境有效，Q0B 已证明信息会改变合理决策，但这两项仍不足以
授权 Q1。正式训练之前必须再完成两件事：一是完成系统的新颖性地图，二是冻结完整方法的数学
定义与四格受控实现。此次暂停不是算法失败，而是防止“训练完成后才发现创新重叠或消融不可
识别”。

## 论文唯一主问题

三架异构 UAV 在计划消息和确认消息可能延迟、丢失或过期时，如何仅依靠各自合法的本地通信
历史判断团队是否已经形成可执行的一致计划，并据此选择立即承诺、等待新信息或保守降级？

候选论文论题不是“处理通信延迟”，也不是“用 RNN 记忆历史”，而是：

> 将去中心化计划一致性不确定性显式纳入任务承诺，在收益期望与错误承诺下行风险之间进行
> 风险约束的 Bayes 期权价值决策。

## 新颖性边界

初步先验技术检索表明，以下概念已经存在，不能作为本文独占创新：

- delay-aware MARL 已经研究等待时间与通信收益/延迟代价的权衡；
- POMDP 与深度 RL 已经研究显式 belief representation；
- robust POMDP/MDP 已经研究 ambiguity set 和最坏情形决策；
- value-of-information planning 已经研究信息获取与后续行动价值。

因此，P3 只有在以下组合差异经更完整检索后仍成立时才有继续价值：它处理的不是一般网络延迟，
而是多智能体私有消息历史导致的“计划是否共同成立”不确定性；方法显式维护可辩护的一致性
假设集合，并在支持集下行约束内比较立即行动与等待后条件行动的期望期权价值；证据来自闭环
异构 UAV 协同，而不是离散通信玩具任务。

## 方法冻结目标

完整方法暂名 `Epistemic-Commitment MAPPO`，由两个可独立关闭的模块组成：

1. **显式一致性集合表示**：根据本地发送、接收、版本号和消息年龄，维护当前仍可能成立的
   团队计划一致性假设及其概率质量；不得读取 evaluator 的全局交付真值。
2. **认知承诺门**：在冻结的支持集下行约束内，比较 `commit`、`defer` 和 `fallback` 的
   posterior expected option value。它不是纯 maximin；Q0B 已证明纯 maximin 会立即 fallback，
   无法表达本文希望研究的信息价值权衡。

在公式、阈值来源、训练损失、执行期输入和参数容量全部冻结之前，`implementation_complete`
保持为 false。

## 四格机制消融

| 方法 | 显式一致性集合 | 认知承诺门 | 回答的问题 |
|---|---:|---:|---|
| Recurrent MAPPO | 否 | 否 | 容量匹配的历史编码基线 |
| Point-belief Commitment | 否 | 是 | 只有承诺门是否足够 |
| Information-set Direct Policy | 是 | 否 | 只有显式表示是否足够 |
| Epistemic-Commitment MAPPO | 是 | 是 | 两模块是否形成增量作用 |

四方法必须共享 PPO、物理环境、奖励、训练 cell、episode tape、物理步预算和固定终点评估。
训练 seed 必须完全配对。若四格方法不能做到容量与执行信息匹配，该消融不得启动。

## 训练前冻结指标

唯一主要端点是：每个训练 seed 在五个训练支持评价 cell 上的平均 `task_value`。训练 seed 是
独立统计单位；同一 seed 内的 episode 和 cell 不能扩充样本量。

可靠性指标单列：联合成功、错误走廊承诺、超时、恢复和保守降级率。碰撞、约束违规和能耗作为
安全指标单独报告，不能由任务得分代替。

机制指标在训练前固定为：无当前共享计划时的错误承诺率、已有当前共享计划时的错失承诺率、
ACK 到达后的动作切换率、信息集覆盖率、ACK 前后信息集宽度、观测等价状态对上的 oracle
regret，以及 defer 后转向 commit/fallback 的比例。遥测只能证明策略行为符合或不符合机制
预期，不能单独证明因果机制。

## 统计与预算

若进入正式比较，计划使用 8 个完全配对的训练 seed；报告逐 seed 差、均值、中位数、范围、
置信区间和精确配对随机化检验，并对三个预先冻结的主要对比做 Holm 校正。不允许看到结果后
追加 seed。

正式训练长度不继承 DRTP 的 10M 惯例。Q1 只用于观察 recurrent MAPPO 的学习曲线是否进入
稳定平台；在不知道候选方法标签的条件下据此冻结正式 endpoint。若 Q1 基线不可学习，任务
停止；若 Q1 已饱和，则先检查是否仍存在方法区分空间，而不是直接投入四方法训练。

## 结果解释在训练前写死

- 完整方法优于基线但不优于两个消融：支持任务收益，不支持模块必要性；
- set-only 与完整方法相当：显式表示可能有用，承诺门必要性未获支持；
- point-gate 与完整方法相当：承诺控制可能有用，集合表示必要性未获支持；
- 四方法相当：冻结任务与预算下没有经验增量价值；
- 得分提高但错误承诺增加：只能报告性能—可靠性权衡；
- 完整方法同时改善主要端点和两个模块对比：才支持完整机制。

这些分支不能保证结果为正，但能保证任何结果都回答预先提出的问题，不会在训练结束后才发现
对照不公平、指标不对应、消融不可识别或论文主张无处落脚。

## 当前阻塞项

1. 完成覆盖 delay-aware communication、belief MARL、robust POMDP、value of information 和
   decentralized agreement uncertainty 的系统检索与逐项差异表；
2. 写出完整方法的状态、假设集合更新、posterior、option value、下行约束和 PPO 联合损失；
3. 实现四方法并通过容量、信息边界、单步行为和 exact-resume 审计；
4. 之后才允许运行 Q1 基线可学习性 pilot。

当前 verdict：`P3_FOUNDATION_BLOCKS_TRAINING_PENDING_NOVELTY_AND_METHOD_FREEZE`。

## 初步先验技术锚点

- Yuan 等，*DACOM: Learning Delay-Aware Communication for Multi-Agent Reinforcement Learning*，
  已直接研究等待消息带来的通信收益与延迟成本权衡：<https://arxiv.org/abs/2212.01619>；
- Wang 等，*Learning Belief Representations for Partially Observable Deep RL*，已研究显式 belief
  representation 对部分可观测策略学习的作用：<https://openreview.net/pdf?id=4IzEmHLono>；
- Flaspohler 等，*Belief-Dependent Macro-Action Discovery in POMDPs using the Value of
  Information*，已使用 value of information 组织部分可观测决策：
  <https://proceedings.neurips.cc/paper/2020/hash/7f2be1b45d278ac18804b79207a24c53-Abstract.html>；
- Petrik 与 Russel，*Beyond Confidence Regions: Tight Bayesian Ambiguity Sets for Robust MDPs*，
  已讨论 Bayesian ambiguity set 与最坏情形决策：
  <https://proceedings.neurips.cc/paper/2019/hash/b994697479c5716eda77e8e9713e5f0f-Abstract.html>。

这些文献只构成第一轮定位锚点，不等于系统检索完成。
