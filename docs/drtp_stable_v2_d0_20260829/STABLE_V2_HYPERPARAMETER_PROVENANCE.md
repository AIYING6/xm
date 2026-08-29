# Stable-v2 超参数来源

## 冻结原则

Stable-v2 不使用 seed3001–3005 的最终 reward、catastrophic 标签或 milestone 胜负选择阈值。R1 日志只用于确认现有量级和遥测缺口。

## 选中设计的阈值

选中设计 DRTP-KLR 使用：

\[
\tau_{KL}=\frac{\epsilon_{clip}^{2}}{2}
=\frac{0.2^{2}}{2}=0.02.
\]

- `epsilon_clip=0.2` 是 Original DRTP 已冻结的 PPO 参数，不是 Stable-v2 新调出的数值；
- `tau_KL` 是从现有 clip radius 得到的局部二阶尺度，不引入独立可调 scalar；
- 该映射是设计尺度，不声称 PPO clipping 在数学上保证 KL 小于 0.02；
- 未来实现必须直接计算 post-step full-batch empirical approximate KL，并以 0.02 作硬接受边界；
- 禁止根据 pilot 结果把 0.02 改成 0.01、0.005 或其他值。

现有 R1 `approx_kl` 的 pooled P99 为 0.004298、最大值为 0.016054，均低于 0.02；但该字段是四个 pre-step epoch KL 的均值，与未来 post-step guard metric 不完全相同。因此这些数值只说明新 guard 预期是稀有条件干预，不能用于估计实际 intervention rate，也不参与阈值选择。

## 新增参数纪律

| 项目 | 冻结值 | 类型 | 来源 |
|---|---:|---|---|
| `clip_coef` | 0.2 | existing scalar | Original DRTP PPO config |
| `target_kl` | 0.02 | existing config field, newly enabled | `clip_coef^2/2` |
| guard mode | `post_step_actor_rollback` | categorical switch | selected algorithm semantics |
| rollback interpolation factor | 不存在 | — | 只接受或精确回滚，不做 backtracking sweep |
| EMA/anchor/TR | 禁止 | — | R1/S1/S2 证据边界 |

该设计新增 0 个独立 scalar hyperparameter。`target_kl` 字段虽从 `None` 改为 0.02，但其数值完全由已有 `clip_coef` 决定。

## 被拒候选的阈值问题

Candidate B 需要 actor/critic actual Adam displacement threshold。R1 的 `actor_update_norm` 与 `critic_update_norm` 在 58,605 行中全部为 `NOT_AVAILABLE`；raw gradient norm 又不能替代 Adam displacement。因此不存在可审计、label-free、同量纲的冻结阈值。

Candidate C 至少需要 EMA decay 或 slow-policy mixing coefficient。现有合同没有对应参数，且无法从不看性能标签的现有 telemetry 唯一导出，故不冻结。
