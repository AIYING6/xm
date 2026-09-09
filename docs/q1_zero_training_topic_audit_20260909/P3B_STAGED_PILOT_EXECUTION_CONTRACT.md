# P3B 分阶段 1M pilot 执行合同

## 执行顺序

1. 对 `83011–83013` 各训练 976 个 update 的公共 recurrent MAPPO 前缀；每 update 为 4 环境 × 64 步。
2. 对每个前缀运行 64 个固定策略校准回合；12 个几何 seed 用于 estimator 拟合，4 个几何 seed 只用于验证。
3. 汇总三个校准报告。任一 seed 未通过质量检查即停止，不启动性能 arm。
4. 全部通过时，从每个 seed 的相同公共前缀分别训练 `recurrent_mappo`、`entropy_probe`、`decision_relevant_probe` 2931 个 update。
5. 只评估固定 1M 端点，在 prior 0.50/0.90 × recoverable/hard 四个 cell 各运行 100 回合。
6. 以 training seed 为独立统计单位，prior 分开汇总。

## 预算解释

整数 rollout 布局使每个 arm 的逻辑预算为 `(976+2931)×4×64=1,000,192` environment steps。校准 simulator steps 单列，不计入任何 arm 的 PPO 性能预算。公共前缀只计算一次，但在因果比较中作为三个 arm 完全相同的前 0.25M 初始化。

## 校准质量门

必须同时满足：完整因子覆盖、actor 未变化、PPO 更新为 0、验证误差有限、held-out gate 决策一致率不低于 75%，以及 balanced prior 下存在经验 decision-relevant case。未通过时的 `P3B_CALIBRATION_STOP` 是预先定义的低成本科学停止，不是 runner 崩溃，也不触发算法修补。

## 证据边界

该 pilot 用于小规模筛选 active-diagnosis 假设。三 seed 结果只能支持是否值得进入正式 fresh cohort 的决策，不能直接支持论文中的稳定性、泛化性或普遍优越性主张。
