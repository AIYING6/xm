# DRTP B 线 H2 独立确认：0.5M 最终决策

状态：`H2_NO_GO`（永久关闭 H2 假设）。

## 证据完整性

- 归档：`drtp_h2_confirmation_stage1_05m_results.tar.gz`；
- SHA256：`74667ad8504ca9c2d542efa5dccc5bd812543ec27de50042111674b88a6a1956`；
- 冻结方法：UTR-SG-MAPPO / original DRTP-SG-MAPPO；
- 新 paired development seed：2801–2805；
- Stage-1：10 条轨迹均到 update 1,953，即每条 **499,968 environment steps**；
- 资源调度：作者授权的 10 路并发；不影响任何科学定义；
- 训练后执行冻结的 H2 0.5M gate，并在 gate 后停止；未发生 1M continuation、
  seed replacement、checkpoint promotion 或 DRTP 修改。

## 冻结判据与结果

每个 DRTP seed 必须同时具备：早期 optimization/critic signature、自适应 q shift，
以及相对 paired UTR 的 tau=60 行为/任务支持退化，才计作完整 H2 signature。
预注册门槛为至少 2/5。

| seed | optimization | adaptive q shift | behavior/support | 完整 H2 signature |
|---:|:---:|:---:|:---:|:---:|
| 2801 | 否 | 否 | 否 | 否 |
| 2802 | 否 | 是 | 否 | 否 |
| 2803 | 否 | 否 | 否 | 否 |
| 2804 | 否 | 否 | 否 | 否 |
| 2805 | 是 | 否 | 否 | 否 |

因此重复完整 signature 为 **0/5**，低于 `≥2/5` 门槛。不同 seed 只出现了
彼此脱钩的单层变化：2802 有 q shift 但没有对应早期 optimization 或支持层退化；
2805 有 early optimization 信号但没有 q shift 或支持层退化。这直接反驳将 H2
各层视为可重复时间链的解释。

## 冻结动作

- 不续训至 1M；
- 不重跑、不换 seed、不放宽阈值；
- 不设计或实现 H2 intervention；
- 不引入 Stable-DRTP、EGTR、R-DRTP、trust region、confidence gate 或其他
  DRTP 稳定化修改。

该结论仅关闭 H2，即“early policy/critic vulnerability × adaptive sampling”作为
DRTP cohort/seed reversal 的可重复主机制；它不改写 A 线论文的既有 DRTP 结果，
也不将未证实的 q 偏离表述为病因。
