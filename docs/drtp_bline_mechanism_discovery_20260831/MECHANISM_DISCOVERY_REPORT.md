# DRTP B 线机制发现 R0

**Decision:** `MECHANISM_DISCOVERY_NO_GO`.

这是零训练、证据层级的综合审计。它不重新解释任何历史 gate，也不将不同 cohort 合并为一个样本。训练 seed 是唯一独立单位；update、episode 和 shadow alarm 只用于时间对齐。

## 冻结判据

- **replication**：At least two adverse DRTP seeds show the same directional signal.
- **temporal_precedence**：The signal is present before task-performance degradation.
- **paired_utr_specificity**：The signal is absent or materially weaker in matched UTR and high-return DRTP controls.
- **continuous_chain**：The evidence connects update/training state to a non-equivalent policy/value/behavior layer and then to task outcome.
- **minimal_intervention_mapping**：One intervention can target the signal without simultaneously changing sampler, PPO, reward, network, or environment.

## 证据矩阵

| Route | replication | temporal_precedence | paired_utr_specificity | continuous_chain | minimal_intervention_mapping |

| --- | :---: | :---: | :---: | :---: | :---: |

| R1 forensic | False | False | False | False | False |
| B1 update sensitivity | False | False | False | False | False |
| B5 failure-credit telemetry | False | False | False | False | False |
| Selective-KLR P1 shadow audit | False | False | False | False | False |
| CV-DRTP dual-cohort pilot | False | False | False | False | False |

## 结论

没有任何一条候选机制链同时满足重复性、时间领先、UTR 特异性、连续中间层和单一最小干预映射。特别是，B1、B5 和 R1 均没有得到跨 seed 的一致前兆；P1 没有得到可推广的 rollback 效用信号；CV-DRTP 则在两个新鲜 cohort 中直接系统性破坏收益和下尾。

因此，此时设计任何新的 Reliable-DRTP 都将是无机制支持的猜测，而非可证伪的研究推进。该决定不否认 Original DRTP 的高收益潜力，也不影响主线 A；它只禁止继续 B 线的局部补丁、CV-v2 或任何新的训练候选。

## 后续边界

B 线转为 `MECHANISM_DISCOVERY_NO_GO`。除非出现新的、未被现有档案覆盖的可观测机制证据，否则不再授权 B 线训练。资源应转回主线 A 的投稿收敛与风险逐项解决。
