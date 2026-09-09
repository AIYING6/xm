# P3B：1M pilot 因果对照与停止合同

**状态：** `P3B_CONTRACT_FROZEN_IMPLEMENTATION_PENDING`

## 1. 唯一目的

检验：在部署时无法直接观察通信失效原因的条件下，按**任务决策遗憾下降**决定是否执行一次合法探测，能否以更低或相当的探测代价获得高于通用不确定性探测的任务价值，并相对无显式诊断的 recurrent MAPPO 改善任务端点。

本 pilot 不是论文确认实验，也不用于调参搜索。

## 2. 三个冻结 arm

1. `recurrent_mappo`：容量匹配的循环策略；不接收故障真值，不使用显式 Bayesian belief 或外部 probe gate，可从合法历史自行选择探测动作。
2. `entropy_probe`：使用与完整方法完全相同的故障先验、观测核、belief 更新、一次性探测 option 和低层控制器；仅以预期 entropy reduction 减探测成本作为 gate。
3. `decision_relevant_probe`：除 gate 使用 DVOI（预期任务遗憾下降减时间/能量成本）外，与 `entropy_probe` 完全一致。

`entropy_probe` 与 `decision_relevant_probe` 是主要机制对照，因为二者共享 belief、探测动作和低层策略，唯一变化是 gate 的目标。`recurrent_mappo` 是实践基线，不被描述为严格的单变量因果消融。

## 3. 固定项

- 三架异构 UAV、3DOF 动力学和任务几何；
- 27 个低层飞行动作及同一个 relay-only probe option；
- actor/critic 隐藏宽度、循环状态维度、PPO 目标与优化器；
- 奖励、安全约束、最大回合长度和每条 1M environment-step 预算；
- recoverable range loss 与 hard relay failure 的支持集合；
- 每回合最多一次、持续 12 步的物理握手探测；
- fixed endpoint，不按回报选 checkpoint；
- 相同训练 seed 和独立 evaluation tape。

任何 arm 都不得把潜在故障标签、失败节点 ID 或 counterfactual outcome 输入 actor。

## 4. 预算与统计单位

- fresh training seeds：`83011, 83012, 83013`；
- 3 arms × 3 seeds × 1M steps = 9M environment steps；
- 独立统计单位是 training seed；
- episode 和 condition 只用于构造每个 seed 的端点，不能扩成独立样本量；
- fixed evaluation priors：recoverable probability `0.50` 与 `0.75`；
- balanced 与 biased prior 分开报告，不池化为扩大 n。

## 5. 主要端点

联合报告：

- mission return；
- success、timeout；
- collision、constraint violation；
- probe rate、平均 probe duration 与物理能耗；
- recoverable/hard-failure 分条件端点；
- 诊断正确率仅为辅助量，不能替代任务价值。

## 6. 继续与停止规则

完整方法只有同时满足下列条件才进入正式开发：

1. 相对 `recurrent_mappo`，任务 return 或 success/timeout 组合呈多数 seed 的正向趋势；
2. 相对 `entropy_probe`，不增加平均探测次数的情况下提高任务价值，或以明确更低探测成本保持相当任务价值；
3. 三个 seed 均无 probe-induced catastrophic collision/constraint failure；
4. probe rate 严格位于 0% 与 100% 之间；
5. 平衡先验与偏置先验不出现相互矛盾的策略退化；
6. 结果不是仅有诊断准确率提高而任务端点不变。

若不满足，路线停止；不做 v2/v3 gate 修补，不扫大量超参数。

## 7. 训练前尚需通过的实现门

- 三个 arm 的参数量、循环状态和可见输入审计；
- gate override 的 log-probability / PPO 归因合同；
- option 持续期间的动作与折扣语义审计；
- prior、likelihood 与 belief 更新的运行态序列化；
- fixed evaluation tape 哈希与 seed 去重；
- 32–128 步多环境 rollout + checkpoint replay；
- 旧环境和旧 DRTP 路线回归测试。

这些检查未通过前，`pilot_authorized=false`。

