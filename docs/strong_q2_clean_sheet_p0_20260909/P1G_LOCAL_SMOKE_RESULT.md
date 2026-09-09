# P1G：本地优化与断点恢复 smoke 结果

## 结论

`P1G_LOCAL_OPTIMIZER_AND_RESUME_SMOKE_PASS`

候选和容量/风险匹配 recurrent 主对照均完成本地短程优化；参数更新、端点日志、固定 checkpoint 保护和逐位一致的断点续跑全部通过。现在可以构建 P2 pilot 的正式 runner 与云端包，但本地 smoke 数值不得作为性能证据。

## 已验证内容

- 两个方法使用相同两阶段 episode、critic、Adam 配置、PPO clipped objective 和区间校准目标；
- 候选及 recurrent actor 均发生真实参数更新；
- 每次更新均记录任务价值、双边承诺率、单边承诺率、defer、fallback、stale-token commit、碰撞、约束违规、actor loss、critic loss 和 calibration loss；
- 所有日志字段有限，无 NaN/Inf；
- checkpoint 包含 actor、critic、两个 optimizer、动作采样 RNG、方法、seed、batch size 和 update index；
- 已存在的固定 checkpoint 会拒绝覆盖；
- 从 checkpoint 恢复后的下一次 metrics、actor 参数和 critic 参数与不中断运行逐位一致；
- 低层 3DOF 控制器固定，高层 actor 只输出三种任务模式。

## Smoke 规模

- optimizer updates：5；
- episode：60；
- 3DOF 物理步：960；
- performance training：未启动；
- scientific evidence：否。

审计中出现的单次随机初始化回报差异不具有统计意义，不得用于候选与 recurrent 方法比较。

## 下一步边界

下一步只允许：把已审计 runner 扩展为固定 62,500 episode/run 的 P2 runner，增加训练 manifest、固定终点评价、汇总与云端 preflight。不得修改 P1F 的方法、奖励、seed、模糊半径、损失权重或继续阈值。

## 可追溯文件

- smoke runner：`scripts/run_epistemic_commitment_p1g_smoke.py`
- 审计：`scripts/audit_epistemic_commitment_p1g_smoke.py`
- 测试：`tests/test_epistemic_commitment_p1g_smoke.py`
- 机器结果：`docs/strong_q2_clean_sheet_p0_20260909/P1G_RESULT.json`
