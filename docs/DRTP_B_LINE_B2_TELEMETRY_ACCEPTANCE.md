# DRTP B线 B2：行为遥测技术验收

状态：`B2_TECHNICAL_PASS`  
执行范围：短 CPU smoke；未启动新 cohort、云端长训练、诊断 tape 或算法修改。

## 验收结果

| 检查 | 结果 | 证据 |
|---|---|---|
| 随机策略下遥测开/关等价性 | PASS | 同一 seed、DRTP sampler 与 PPO 配置下，256 个环境转移的动作、奖励、终止和故障状态逐项一致；最终模型 SHA256 相同。 |
| PPO 与 sampler 不变性 | PASS | `train_log.csv` 与 `drtp_topology_sampler_log.csv` 逐行完全相同。 |
| 中途保存/恢复 | PASS | 连续两次更新与一次更新后从 runtime state 恢复再运行一次更新，模型、优化器、环境、随机状态、sampler 与 telemetry state 逐状态一致。 |
| actor/critic 信息边界 | PASS | writer 仅在 `env.step` 之后读取状态并写 JSONL；不向 actor、critic、reward、PPO 或 sampler 返回任何值。 |
| 并行隔离与 provenance | PASS | 记录包含 method、training seed、env index、episode index 和确定性 episode id；B2 固定 seed 为 2601。 |
| schema 与缺失值 | PASS | 事件窗口含动作、奖励分量、终止原因、合法边、direct/relay/no-path、cache、attack-window、任务支持、三机/目标位置及显式 pairwise geometry；非有限值以 JSON `null` 表示。 |

## 验收中发现并修复的证据完整性问题

1. 环境把 cache relay route 表示为路径字符串（例如 `0-1-2`），旧 writer 错误地尝试按浮点数解析。现改为保留路径字符串的语义，并仅据其是否为有效路径判断 relay 状态。
2. 旧 writer 对部分环境数组仅保留 NumPy 视图；后续环境 transition 或运行态恢复可能改写已缓存的事件窗口行。现全部保存不可变副本。

这两项均属于**日志层**修复；B2 的 on/off 等价性证明它们不改变训练轨迹。此前 2601--2603 的 V1 云端资产仍因 seed provenance 不一致永久保持 `TECHNICAL_INVALID`，不得重新解释为有效机制结果。

## Gate 结论

`B2_TECHNICAL_PASS` 只授予“可以讨论 B3 exploratory pilot 合同”的资格；它不构成机制发现，不授权 Stable-DRTP、不授权 3M/10M，也不改变 A 线投稿稿件。
