# P3B 统一 runner 实现审计

**结论：** `P3B_INTEGRATED_RUNNER_PASS`

审计对象为真实 `ActiveDiagnosisTrainableUAVEnv`，不使用合成 rollout。三个冻结 arm 各执行 64 步 × 2 环境 rollout 和一次 PPO 更新；另执行中途 option checkpoint 恢复、短终止回合监督写入以及 2 几何 × 2 模式 × 2 option 校准烟测。

通过项包括：

- 三个 arm 的 recurrent actor/critic 参数结构一致；
- 三个 arm 的 PPO 更新均有限，执行动作均合法；
- ungated arm 无外部动作归因，两个 gated arm 均保存不同的 sampled/executed 轨迹；
- gate 接管的 agent-time 被 actor loss 屏蔽，critic 和 GAE 仍消费真实转移；
- probe option 中途保存后，下一段真实 rollout 精确复现；
- 完成的训练回合以真实回报形成监督记录；
- 校准完整覆盖故障模式 × 恢复 option，且不改变 actor；
- task-value estimator 只使用中继机 actor 局部观测，不使用 critic 的集中式状态；
- 固定评价 tape 的 episode ID 唯一并与训练 seed 不相交。

机器可读证据位于 `artifacts/active_diagnosis_p3b/P3B_INTEGRATED_RUNNER_RESULT.json`。本审计只授权公共前缀与校准阶段，不构成算法性能证据。
