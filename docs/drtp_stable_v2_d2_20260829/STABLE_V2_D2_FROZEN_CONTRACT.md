# Stable-v2 D2 冻结 pilot 合同

## 科学目标

本 pilot 只回答：DRTP-KLR 能否在保留 Original DRTP 平均收益和高收益 seed 的同时，改善最差 seed、减少 catastrophic downside 并降低跨 seed 离散度。

它不用于证明大 KL update 是既有不稳定的唯一根因，也不进入主线 A 论文证据。

## 冻结设计

- arms：`UTR / Original DRTP / DRTP-KLR`；
- paired clean training seeds：`3101 / 3102 / 3103`；
- 每条：`1,953 updates = 499,968 environment steps`；
- 共 9 条 trajectory，云端并发固定为 9；
- milestone：`250k / final 500k`，只用于持久化，不允许 promotion；
- DRTP-KLR：Original DRTP sampler + `target_kl=0.02` post-step actor rollback；
- UTR 与 Original DRTP：guard 均为 `none`；
- tape：`550000–550099`，5 conditions × 100 episodes，hash `25ff4eb5764cd2d590fba719a9c6c43b290ee3466a63075fd7e7184b049c4859`；
- `epsilon_J = downside margin = 7.874919837916801`，沿用同 evaluator、同 conditions、同每条件 100 episodes 的 S0 同 checkpoint cross-tape P90，不根据新结果重估。

## 全部必要 gate

1. `J_nominal / J_F0 / J_pert_mean / J_pert_worst` 四个跨 seed 均值均不得低于 Original DRTP 超过 `epsilon_J`；
2. worst paired `J_pert_mean` gain 相对 Original DRTP 改善超过 downside margin，且 catastrophic seed 数不得增加；
3. Stable-v2 gain 的 range 和 sample SD 均小于 Original DRTP；
4. 至少 2/3 seed 的 `KLR−Original >= -epsilon_J`；
5. Original DRTP 明显优于 UTR 的 upper-tail seed 必须存在，且 KLR 不得压低超过 `epsilon_J`；
6. 对 UTR 和 Original DRTP 两个参考，pooled collision/timeout 劣化均不超过 0.05，任一 seed-condition 劣化不超过 0.10，constraint violation 不增加；
7. rollback 至少触发 1 次，pooled trigger/attempt rate 不超过 10%；
8. 9 条轨迹、4,500 条 raw records、统一 final checkpoint、telemetry 和 provenance 全部完整。

只有全部通过才输出 `PILOT_GO_SIGNAL`。任一失败输出 `PILOT_NO_GO`；不会自动续到 1M，也不允许更换 seed、调 `0.02`、重跑或 checkpoint promotion。

## 与主线 A 隔离

本目录、配置、训练输出和未来 pilot 结果均属于 `results/development/drtp_stable_v2_pilot`。主线 A 的论文、formal cohort、independent cohort、cross-tape 和 unseen evaluation 不被修改，也不等待 B 线结果。
