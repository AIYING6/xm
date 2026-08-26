# DRTP 与 MAPPO-NoGraph 外部参考比较：独立归档审计

**状态：** `EXTERNAL_REFERENCE_COMPLETE`

本审计针对归档 `drtp_mappo_nograph_external_5seed.tar.gz` 独立执行。归档 SHA256 为 `2f8b5f1e3025221e70652a6c4d0bcaa05d239cc81f5c70d59301d4f9e66afad5`，与随附校验文件一致。五个训练种子 2301–2305 均标记为 `completed`，每条轨迹达到 39,063 updates、10,000,128 环境步；训练错误日志为空。MAPPO-NoGraph 的参数量为 35,771，而 UTR/DRTP 的 SG 主干均为 116,728，因此此处是外部参考而非同构因果消融。

该分析将新训练的 MAPPO-NoGraph 与已冻结的 UTR/DRTP 正式五种子结果置于同一 490000–490099 评价 tape。五个 MAPPO-NoGraph cell 共保留 6,000 条原始 episode 记录，tape SHA256 `84e31ed185ced0608a30c9cb9f9659c7423c952e4603aac53cf691c54fc64ac2` 与正式参考一致。
UTR–DRTP 仍是同构训练设计下的主消融；MAPPO-NoGraph 是外部参考，架构差异不得用于归因 DRTP 的自适应加权效应。

## 汇总性能

| 方法 | J_nominal | J_F0 | J_OOD_mean | J_OOD_worst | 碰撞(故障均值) | 超时(故障均值) |
|---|---:|---:|---:|---:|---:|---:|
| utr_sg | 174.3 | 144.6 | 144.7 | 124.4 | 0.005091 | 0.8742 |
| drtp_sg | 207.8 | 196.8 | 199.7 | 187.4 | 0.008 | 0.6938 |
| mappo_ng | 206.6 | 193.7 | 190.1 | 179.8 | 0.002 | 0.6005 |

## MAPPO-NoGraph 的配对差（MAPPO − reference）

| 对比 | 指标 | mean | median | wins/5 | worst |
|---|---|---:|---:|---:|---:|
| mappo_ng_minus_utr_sg | J_nominal | 32.29 | 46.81 | 3/5 | -23.75 |
| mappo_ng_minus_utr_sg | J_F0 | 49.06 | 69.99 | 3/5 | -18.58 |
| mappo_ng_minus_utr_sg | J_OOD_mean | 45.37 | 73.62 | 3/5 | -24.45 |
| mappo_ng_minus_utr_sg | J_OOD_worst | 55.33 | 91.06 | 3/5 | -41.11 |
| mappo_ng_minus_drtp_sg | J_nominal | -1.195 | -33.28 | 1/5 | -50.04 |
| mappo_ng_minus_drtp_sg | J_F0 | -3.076 | -21.6 | 1/5 | -53.62 |
| mappo_ng_minus_drtp_sg | J_OOD_mean | -9.633 | -26.58 | 1/5 | -57.45 |
| mappo_ng_minus_drtp_sg | J_OOD_worst | -7.677 | -26.33 | 1/5 | -70.89 |

所有五个训练种子、最终 10M checkpoint 与全部已计划 episode 均被保留；本报告不改写历史 DRTP/UTR 正式结论，也不授权后续训练。MAPPO-NoGraph 在碰撞和超时上均低于 DRTP，故外部结果只能支持受限的任务端点定位，不能被写成全指标绝对优越性。
