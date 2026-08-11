# v1.6R R3 Behavior-Retention Protocol

状态：`R3_PARTIAL__ACQUISITION_RETENTION_WITHOUT_MISSION_GAIN`

## 假设

R2R 已显示：BC policy 能在闭环中进入 attack geometry，而原 PPO 更新会破坏该行为。R3 只检验一个假设：

> 在合法 target evidence 已存在的状态，限制 PPO policy 相对冻结 BC/reference policy 的 guidance 偏离，可以保留物理上有用的 pursuit 行为，并允许 PPO 继续改进。

## 唯一机制

对 evidence mask 为 1 的 rollout 状态，增加：

```text
L_retention = mean(||mu_current(o) - mu_reference(o)||²)
```

其中 `mu_reference` 是冻结的 BC actor deterministic continuous guidance，`mu_current` 是当前 PPO actor deterministic guidance。`evidence_mask` 只来自 rollout 时 recipient 的合法 local sensing / delivered-valid cache；过期、缺失或 pending evidence 不启用 retention。

本机制不改变：

- reward、3DOF physics、mission endpoint；
- actor information contract；
- action space、horizon、GAE、PPO clip；
- 无 evidence 状态下的 PPO policy loss；
- critic 输入与训练协议。

## 公平比较

- Vanilla PPO：同一 BC 初始化、同一 batch/seed/updates；
- Retention PPO：只新增 evidence-masked retention term；
- BC-Frozen：不更新，仅作能力上界/保持参照；
- 两个 development seeds：`17301 / 17302`；
- 60 updates；同一冻结 evaluation episode seeds；
- 不增加 seed、updates 或调参救结果。

`retention_coef=1.0` 在 pilot 前冻结，不根据结果调整。该系数只作为机制强度配置，不宣称理论最优。

## GO/NO-GO

PASS 需要两个 seed 相比 vanilla PPO：

1. evidence 后 geometry acquisition 不再系统性退化；
2. evidence-to-range latency 不恶化；
3. 至少一个 mission endpoint 同方向改善；
4. retention loss 有效但不导致策略冻结。

若只保持 BC、没有超过 vanilla PPO 或没有 mission 改善，判为 PARTIAL；若两个 seed 均无 acquisition 保持/改善，判为 NO-GO，并关闭当前 v1.6R 算法线。
