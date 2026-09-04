# TGTR-PPO C1 同批 rollout 机制验证协议（未授权执行）

## 1. C1 只回答一个问题

在完全相同的同步固定分层 training rollout、checkpoint、actor/critic、Adam state 和 RNG 状态下，TGTR 能否把 ordinary PPO 中可重复的逐组局部伤害修正掉，同时保留非零更新、nominal 与平均 surrogate，并满足逐组 full-policy KL？

C1 不是 policy performance evaluation。

## 2. 开发单元

- 5 个固定 source training states；允许使用已见 development seed，因为 C1 不产生性能 claim；
- 每个 state 收集一个 24 × 64 的 training-only synchronized rollout；
- A：matched Sync-UTR ordinary PPO；
- B：TGTR-PPO；
- A/B 从完全相同 snapshot 和 batch 分叉；
- critic update、reward、环境和 rollout 均完全一致；
- 不读取 formal、independent 或 held-out evaluation tape。

## 3. 必须输出

- batch SHA256 与每组 graph/stream count；
- A/B 的 per-group design surrogate change；
- A/B 的 per-group held-stream certificate surrogate change；
- A/B 的 per-group full-categorical KL；
- active group、QP residual、correction norm；
- backtrack alpha、zero-step flag；
- nominal、pooled failure、overall surrogate；
- actor/critic displacement与 Adam transaction exactness；
- wall time和 peak GPU memory。

## 4. C1 结论

`TGTR_C1_MECHANISM_PASS` 仅当：

1. 5/5 exact batch pairs、每次七组齐全；
2. ordinary candidate 至少在 2/5 source states 出现 held-stream mean 为负的逐组伤害，否则机制没有足够 actuation evidence，结论为 inconclusive；
3. 对所有 actuation states，TGTR 消除 held-stream group harm，且没有制造新的 nominal/failure mean harm；
4. 5/5 无逐组 KL 越界、无非 finite、无 optimizer state 污染；
5. 至少 4/5 接受非零 actor step；总体 zero-step rate不超过 25%；
6. 至少 4/5 的 certificate overall surrogate 不低于 ordinary；
7. wall-time倍率不超过 4×，显存适配当前云端 GPU。

若 ordinary 伤害事件少于 2 个，返回 `TGTR_C1_INCONCLUSIVE`；不得靠人为制造更坏 checkpoint 或扩大 trial 数补足。

任一合法性、nominal、KL、zero-step 或成本硬门失败，返回 `TGTR_C1_NO_GO`。

## 5. 只有 C1 PASS 后的精简路线

后续不再拆成大量 PASS：

1. **Development：** 3 个全新 seed，Sync-UTR vs TGTR，0.5M；只筛明显方向、catastrophic 与训练可行性。
2. **Independent validation：** 5 个全新 seed，成熟预算；冻结算法后验证 mean、majority、worst、dispersion、safety/OOD。
3. **Final confirmation：** 第二批 5 个全新 seed；算法、预算、tape、判定均不改。

只有两批成熟验证同方向才停止开发并写算法论文。任何一批不得与另一批 pooled 后掩盖反转。
