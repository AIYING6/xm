# 主线 B 治理合同

## 唯一目标

形成一个相对 Original DRTP 同时具备“高收益保留”和“低下尾风险”的稳定方法，而不是只让统计方差变小。

## 与主线 A 隔离

- 主线 A 的算法、formal/independent cohort、cross-tape、unseen evaluation、论文和投稿时间表全部冻结；
- B 线的 development seeds、tape、checkpoint 和报告不得并入 A 线主证据；
- B 线失败不得阻止或延迟 A 线投稿；
- B 线只有经过独立 mature confirmation 后，才可作为未来新方法论文或审稿修回储备，不能追溯性改写 A 线结果。

## 单一候选规则

当前唯一候选是 `DRTP-KLR`。禁止同时开发 KL 阈值变体、learning-rate 变体、sampler anchor、EGTR、R-DRTP、reward/网络/PPO 联合修改或 Stable-v2a/v2b sweep。

`target_kl=0.02` 来自已冻结的 `clip_coef^2/2`，不得根据 pilot 性能修改。候选失败后关闭本候选，不以 0.01/0.03 重跑。

## Pilot 必须同时通过的科学门槛

| 维度 | 必要条件 |
|---|---|
| 高收益保留 | 三 seed 平均 `J_pert_mean` 相对 Original DRTP 的下降不超过预先冻结的同 tape 评价噪声 `epsilon_J` |
| 下尾保护 | 不新增 catastrophic seed，且 Stable-v2 的 worst paired gain 不低于 Original DRTP |
| 方向一致性 | 至少 2/3 seed 的 `Stable-v2 - Original DRTP >= -epsilon_J` |
| 上尾保留 | Original DRTP 明显优于 UTR 的 seed，不得被 Stable-v2 压低超过 `epsilon_J` |
| 跨 seed 可靠性 | range 与 sample SD 均不得增大；MAD/IQR 作为辅助，不允许用单一离散度指标掩盖 bimodal failure |
| 安全 | pooled collision/timeout 劣化均不超过 0.05；任一 seed-condition 劣化不超过 0.10；constraint violation 不增加 |
| 机制活动 | 至少一次正常 rollback，pooled intervention rate 不超过 10%；0 次或超过 10% 均 NO-GO，且不得调阈值补救 |
| 完整性 | 9 条冻结轨迹全部保留，统一 final checkpoint，无 promotion、换 seed、性能重跑或自动续训 |

只有所有必要条件同时成立，才允许提出“继续同轨迹到更高 development budget”的人工审查。平均分更高但最差 seed 更坏，不算成功；方差更小但上尾被削平，也不算成功。

## 阶段停止线

1. D1 技术实现与 synthetic audit：已 PASS；
2. D2 零训练 pilot 合同冻结：待执行；
3. D3 云端 `UTR / Original DRTP / DRTP-KLR × 3 clean seeds × 0.5M`：待人工授权；
4. 只有 D3 全 gate PASS，才讨论 1M；
5. 只有 1M 仍全 gate PASS，才讨论 3M；
6. 只有独立 5-seed development/confirmation 证明收益、下尾和安全同时成立，才讨论成熟长预算。

任何阶段 NO-GO 都不得通过换 seed、改阈值或新增模块救结果。
