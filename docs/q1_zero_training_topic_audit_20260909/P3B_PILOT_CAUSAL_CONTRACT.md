# P3B：1M pilot 因果对照与停止合同

**状态：** `P3B_STAGED_PREFIX_AND_CALIBRATION_AUTHORIZED`

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
- 27 个低层飞行动作、同一个 relay-only probe option 及 attacker-only prior-guided fallback option；
- actor/critic 隐藏宽度、循环状态维度、PPO 目标与优化器；
- 奖励、安全约束、最大回合长度和每条 1M environment-step 预算；
- recoverable relay--terminal range loss 与 hard terminal communication failure 的支持集合；
- 每回合最多一次、持续 12 步的物理握手探测；
- fixed endpoint，不按回报选 checkpoint；
- 相同训练 seed 和独立 evaluation tape。

任何 arm 都不得把潜在故障标签、失败节点 ID 或 counterfactual outcome 输入 actor。

## 4. 预算与统计单位

- fresh training seeds：`83011, 83012, 83013`；
- 3 arms × 3 seeds × 1M steps = 9M environment steps；
- 独立统计单位是 training seed；
- episode 和 condition 只用于构造每个 seed 的端点，不能扩成独立样本量；
- fixed evaluation priors：recoverable probability `0.50` 与 `0.90`；后者用于检验高置信先验下方法能否拒绝低价值探测；
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

## 7. 分阶段执行门

- `0–0.25M`：三个 seed 分别训练一个 recurrent MAPPO 公共前缀；
- 前缀后：每个 seed 执行 64 个固定策略校准回合，完整覆盖 16 个几何 seed × 2 个潜在故障模式 × 2 个恢复 option；
- 校准期间 PPO 更新数固定为 0，校准 simulator steps 与 1M 性能预算分开报告；
- 只有三个 seed 均通过 estimator 有限误差、held-out gate 决策一致率和 balanced-prior decision relevance 检查，才允许从同一个前缀分叉三个 `0.75M` arm；
- 任一 seed 校准失败即写出 `P3B_CALIBRATION_STOP`，不启动 arm-specific 训练，也不据此修改算法；
- arm 训练通过后才运行固定端点评估，禁止按回报选择 checkpoint。

因此，当前授权只覆盖公共前缀和校准。`performance_pilot_authorized=false` 表示三个完整性能 arm 尚未无条件授权，不表示 runner 未实现。

## 8. 2026-09-09 实现门进展

以下组件及统一 runner 已经通过真实环境技术审计：

- 候选假设枚举式 task-value estimator；真实故障标签只选择监督单元，不进入部署查询；
- estimator、优化器、输入归一化和监督 replay 的完整序列化；
- 三个 arm 参数量一致的 role-graph GRU actor 与 snapshot centralized critic；
- 32 步、2 环境的时间顺序 replay、回合槽位清零和 8 步 truncated BPTT；
- gate 强制 option 对应 agent-time 的 actor loss 归因屏蔽；
- recurrent model、优化器、hidden state 与辅助运行态 checkpoint 恢复；
- 三个 arm 均完成 64 步 × 2 环境 rollout 和一次有限 PPO 更新；
- sampled action 与 executed action 双轨保存，外部 option 的 agent-time 不进入 actor loss；
- 真实 completed episode return 写入 task-value 监督缓存；
- probe-then-recovery 校准完整覆盖模式 × option 因子设计，且 actor 参数逐位不变；
- DVOI 查询只读取中继机 deployment-legal actor 局部观测，禁止读取 centralized critic `share_obs`；
- 固定评价 tape 唯一且与训练 seed 不相交。

这些结果证明集成实现和因果归因合同成立，但不证明 DVOI 的任务收益。审计使用的短校准只检查控制流，其 balanced-prior decision relevance 为 false，禁止将其解释为性能失败或成功。下一道科学门是运行冻结的 `0.25M` 公共前缀后校准；只有其通过，才自动进入三个 arm 的 `0.75M` 分叉训练。
