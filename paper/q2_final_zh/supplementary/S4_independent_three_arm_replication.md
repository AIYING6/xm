# 补充材料 S4｜独立三方法重复 cohort 与跨 cohort 可靠性

## S4.1 目的与证据边界

本补充材料完整披露 `DRTP-SNR-Q2-MECHANISM-COMPARATOR-TRAINING-V1` 及其最终 10M 评价结果。它是一个已完成的独立三方法 cohort，不是对正式主 cohort（UTR/DRTP，种子 2301--2305）的追加 seed，也不允许将两者拼接为表面上的 `(n=10)`。正式主 cohort 与本 cohort 的训练种子、评价 tape 和预注册目的不同；每个 cohort 内部的训练种子仍是唯一独立统计单位。

本 cohort 使用种子 2401--2405；UTR-SG-MAPPO、固定非均匀 SNR-SG-MAPPO 与 DRTP-SG-MAPPO 各五条从零开始、严格连续的轨迹，均训练至 10,000,128 环境步，并采用共同最终检查点规则。三种方法具有同一 SG actor/critic（116,728 参数）、PPO、环境、奖励、七个拓扑组、50% 正常工况锚点、运行时状态持久化和冻结评价协议。SNR 的六组故障权重由训练前固定的条件严重度构造；它不是训练后从 DRTP 轨迹或最终权重导出的静态对照。

评价使用独立 `500000–500099` tape，12 个条件、每条件 100 episode、共 18,000 条原始记录。所有存活至计划故障起始时刻的 episode 均正确触发；故障前碰撞继续计入总体回报和安全统计，不被删除或重新标记。源 archive 的 SHA256 为 `86a708244fa4d30935159a08d234c48feeb7a4c455208d58fbc58d308b4f4ae1`，tape SHA256 为 `c89f63bc5a11e3def88fa677356796ea681ca227d31e47dc584764a3a3084fc2`。

## S4.2 全部方法、全部种子与完整端点

表S4报告每种方法五个训练种子的平均值。`J_pert,mean` 是十个时机、持续时间和复合扰动条件的平均；`J_pert,worst` 是同一训练种子在这些条件中的最小任务得分，再在五个训练种子上平均。它们不是严格未见 OOD 指标。

| 方法 | n | J_nominal | J_F0 | J_pert,mean | J_pert,worst | 碰撞（故障均值） | 超时（故障均值） | 约束违规 | 风险集 trigger validity |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| UTR-SG-MAPPO | 5 | 225.70 | 199.40 | 200.48 | 181.98 | 0.009 | 0.646 | 0.000 | 1.000 |
| 固定非均匀 SNR-SG-MAPPO | 5 | 184.64 | 183.07 | 178.00 | 159.63 | 0.014 | 0.661 | 0.000 | 1.000 |
| DRTP-SG-MAPPO | 5 | 187.35 | 166.13 | 166.41 | 149.61 | 0.052 | 0.678 | 0.000 | 1.000 |

表S5保留 DRTP 相对 UTR 的每一个配对训练种子效应；不删除低分、反转或安全不利种子。

| 种子 | ΔJ_nominal | ΔJ_F0 | ΔJ_pert,mean | ΔJ_pert,worst | Δ碰撞 | Δ超时 |
|---:|---:|---:|---:|---:|---:|---:|
| 2401 | -25.16 | -49.30 | -54.26 | -51.66 | +0.199 | -0.009 |
| 2402 | -41.22 | +21.12 | +11.66 | +25.94 | -0.001 | -0.015 |
| 2403 | -115.41 | -141.57 | -123.87 | -131.50 | +0.010 | +0.143 |
| 2404 | -27.96 | -25.10 | -29.14 | -53.01 | -0.020 | +0.009 |
| 2405 | +18.02 | +28.52 | +25.26 | +48.41 | +0.024 | +0.031 |

| DRTP−UTR 汇总 | J_nominal | J_F0 | J_pert,mean | J_pert,worst |
|---|---:|---:|---:|---:|
| 配对均值 | -38.35 | -33.27 | -34.07 | -32.36 |
| 配对中位数 | -27.96 | -25.10 | -29.14 | -51.66 |
| 正向种子数 | 1/5 | 2/5 | 2/5 | 2/5 |
| 最差配对差值 | -115.41 | -141.57 | -123.87 | -131.50 |

## S4.3 解释限制

本 cohort 的完整方向与正式主 cohort 不同：UTR 的四个任务端点均高于 DRTP，DRTP 相对 UTR 出现一个既有规则下的灾难性种子；SNR 也未优于 UTR。该事实不能被写成“某个 episode tape 的偶然噪声”，因为记录完整、风险集触发有效且每个方法/种子/条件均保留。反过来，它也不回写、删除或改变正式主 cohort 的合同内事实。

因此，论文不将正式主 cohort 与本 cohort 合并计算均值、胜出数或显著性，不称 DRTP 的正式主 cohort 增益为跨 cohort 稳定复现，也不把 SNR 失败解释为全部静态非均匀方案均不可能有效。本 cohort 的作用是限制主张：当前证据只能支持“DRTP 的收益具有 cohort/训练初始化敏感性”，而不能支持普适、seed-stable 或跨 cohort 可靠的优越性。

## S4.4 可复查源数据

- `source_data/snr_independent_replication/raw_episode_metrics.csv`：18,000 条原始 episode 记录；
- `source_data/snr_independent_replication/per_seed_condition_summary.csv`：方法×种子×条件汇总；
- `source_data/snr_independent_replication/per_seed_endpoint_summary.csv`：论文端点的逐种子汇总；
- `source_data/snr_independent_replication/drtp_minus_utr_paired_seed_effects.csv`：表S5的机器可读来源；
- `source_data/snr_independent_replication/evaluation_manifest.json`：配置、最终 checkpoint 与 runtime-state 哈希；
- `source_data/snr_independent_replication/archive_provenance.json`：归档 SHA256、tape 哈希与抽取审计。

这些材料由 `scripts/integrate_drtp_snr_replication_evidence.py` 从原始归档无训练地抽取并校验；该脚本在 SHA256 不匹配、记录数不为 18,000、缺少三种方法或缺少 2401--2405 任一种子时 fail closed。
