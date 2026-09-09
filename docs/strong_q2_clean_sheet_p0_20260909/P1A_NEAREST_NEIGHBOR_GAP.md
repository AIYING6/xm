# P1A：认知一致性任务承诺最近邻差异门

**裁决：** `P1A_CONDITIONAL_PASS_NARROW_GAP_ONLY`

## 1. 最近邻全文核验后的结论

最直接近邻 arXiv:2512.20778 已经显式研究 Dec-POMDP 中的不一致 belief，并给出联合动作一致性和相对 open-loop MPOMDP 性能的概率/确定性保证。其选择算子在最优动作概率不足时触发通信；当数据共享发生时，文中假设共享无噪声且瞬时。因此以下宽泛主张已经不成立：

- “首次研究不一致 belief 下的多机器人协调”；
- “首次提供联合动作一致性保证”；
- “首次根据一致性风险决定是否通信”；
- “公共知识不足导致协调失败”本身是新发现。

MACKRL 又已经证明可重建的 common knowledge 可用于分散联合策略。因此，新课题只剩一个较窄、但具有执行意义的缺口：

> 当可靠通信或补发在当前任务窗口内不可用时，agent 不能用 `COMM` 消除不一致 belief；它必须在具身任务层选择承诺、延迟或安全降级，并承担相应机会损失与单边承诺风险。

## 2. 实质差异矩阵

| 维度 | MACKRL | Dec-OAC-POMDP-OL (2512.20778) | P0H 候选 |
|---|---|---|---|
| 信息起点 | 可形成/重建 common knowledge | agents 持有不一致 belief | agents 持有不一致 belief |
| 通信语义 | common knowledge 可自然出现 | 需要时可触发无噪声、瞬时共享 | 当前任务窗口内通信可能不可用，不能依赖补发 |
| 决策对象 | 分层 joint policy tree | joint action 或 `COMM` | 具身 `commit / defer / fallback` |
| 保证对象 | 经验协调性能 | MRAC/MROAC 与性能概率 | 单边承诺风险与保守降级机会损失（尚未证明） |
| 方法范式 | model-free actor-critic | 显式 belief-space planning | 待定义；必须可扩展学习且不泄漏投递真值 |
| 机器人语义 | 矩阵游戏、SMAC | 双机器人 fire detection simulation | 具有时限和安全后果的异构 UAV 任务 |

## 3. 放行边界

P1A 只是条件通过：差异不是“UAV 应用”，而是**通信不能作为立即恢复一致性的可用动作时，任务层承诺本身成为决策对象**。后续若发现已有工作同时覆盖 unreliable delivery、具身 commit/defer/fallback 和对应风险保证，则路线立即关闭。

P1A 不授权命名算法或训练。下一门是 P1B 解析反例与 P1C UAV shadow semantics。

