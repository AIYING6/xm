# Stable-v2 D0 Design Audit

## 决策

`D0_STABLE_V2_CANDIDATE_SELECTED`

唯一候选为：

> `DRTP-KLR = Original DRTP + deterministic post-step actor KL rollback`

本次只完成设计审计。没有实现、训练、rollout、checkpoint evaluation、参数搜索或 Stable-v2 pilot。

## 科学起点

R1 与 Stage-2 的 `MECHANISM_INCONCLUSIVE` 永久保留：Conservative-DRTP 在五个新 seed 上 NO-GO；sampler、value loss、advantage 波动和 gradient norm 均未形成跨坏 seed 重复、时间领先且成功 seed 不存在的机制链。因此 DRTP-KLR 不被描述为“修复已知 PPO/critic 根因”，而是一个不依赖精确病因的条件式训练保护设计。

Stable-v2 从 Original DRTP 出发。S1/S2/R1 已失败的 TR + 20% uniform anchor 不进入候选。

## 源码与静态证据结论

1. 当前有 PPO objective clip (`0.2`) 和全模型 gradient clipping (`0.5`)；
2. R1 的 `target_kl=None`，没有 post-step trust region 或 rollback；
3. 94.664% 的既有 update raw gradient norm 大于 0.5，说明 gradient clipping 已高频工作但不足以消除 seed 分叉；
4. actor/critic actual Adam update norm 在全部 58,605 行中均不可用；
5. actor/critic 是分离模块，但使用同一个 Adam；optimizer state 按 parameter 保存，可为 actor 做精确事务恢复；
6. runtime checkpoint 已保存 model、optimizer、RNG、environment 和 sampler state，为 deterministic save/resume 技术验收提供基础；
7. 普通 PPO 路径缺少 non-finite optimizer transaction guard。

## 三类候选裁决

### A — SELECTED

Post-step KL rollback 是一个核心修改、无需已知根因、保持 on-policy 数据边界，并能在正常更新不触发时完整保留 Original DRTP。阈值由既有 clip coefficient 推导，不做 sweep。

### B — REJECTED

Bounded Adam displacement 与 gradient clipping 确实不同，但现有日志没有 actual displacement。若现在拍阈值，违反 threshold provenance；若先跑 calibration，又会扩大阶段并产生新的结果驱动选择。因此 D0 不选择 B。

### C — REJECTED

Evaluation-only EMA 不是训练稳定化；rollout policy 与 optimized policy 分离会引入 off-policy 语义；永久 averaging 又有削平上尾风险且需要 decay 参数。D0 不选择 C。

## 为什么该选择不针对 seed3004 调参

seed3004 只提供设计 sanity boundary：永久保守化可能把 Original 的正收益变成 catastrophic。DRTP-KLR 的阈值没有使用 3004 reward 或崩溃时点，而由 `clip_coef` 推导；3004 只支持“条件介入优先于永久压制”的设计原则。

## 风险与证伪性

本选择不表示 DRTP-KLR 会成功。现有 mean pre-step KL 最大值低于 0.02，而且未来 guard 使用不同的 post-step metric，因此 intervention 可能为零。Pilot 已把“零 activity”“过高 intervention”“上尾受损”“catastrophic 不降”全部定义为可导致关闭候选的结果，且禁止修改阈值补救。

## 下一道门

D0 后立即 STOP。下一步若获人工授权，只能先实现并执行技术审计；技术 PASS 后再单独冻结 clean seeds、development tape 与 `epsilon_J`。本决策不授权任何训练。
