# EGTR P3 — 1M Development 评估与阶段门报告

**裁决：** `P3_1M_TECHNICAL_AND_MECHANISM_PASS__SAFETY_REVIEW_REQUIRED`。

本报告仅覆盖 development-only 的 1M 可学习性/机制筛查，不构成论文 superiority、confirmatory 或 held-out 结论。未发生 checkpoint promotion，本次汇总未启动 3M 续训。

## 完整性与 evaluator 有效性

- 要求的 final-checkpoint cells：`9/9`；原始记录：`10800/10,800`。
- 冻结 development tape SHA256：`4e4ebe743aa4b38c18374ba43eb0cb4faaa7e078b49adfec7c9d408c4f0cbb20`；未使用 canonical 或 held-out。
- 9 条 manifest 均记录 from-scratch 的 1,000,192-step completion、116,728 参数、final checkpoint only 和 runtime-state persistence：`True`。
- 对于 alive-at-onset risk set 的 trigger success：`True`。所有未暴露记录均为 onset 前 collision：`True`。

| Arm | Seed | Risk set / scheduled | Survival to onset | Triggered / risk set | Pre-trigger collisions |
|---|---:|---:|---:|---:|---:|
| drtp_sg | 2501 | 1100/1100 | 1.000 | 1100/1100 | 0 |
| drtp_sg | 2502 | 1100/1100 | 1.000 | 1100/1100 | 0 |
| drtp_sg | 2503 | 1100/1100 | 1.000 | 1100/1100 | 0 |
| egtr_sg | 2501 | 1100/1100 | 1.000 | 1100/1100 | 0 |
| egtr_sg | 2502 | 1082/1100 | 0.984 | 1082/1082 | 18 |
| egtr_sg | 2503 | 1076/1100 | 0.978 | 1076/1076 | 24 |
| utr_sg | 2501 | 1100/1100 | 1.000 | 1100/1100 | 0 |
| utr_sg | 2502 | 1072/1100 | 0.975 | 1072/1072 | 28 |
| utr_sg | 2503 | 1100/1100 | 1.000 | 1100/1100 | 0 |

onset 前 collision 保留在所有无条件 return 与 safety 指标中；没有被删除，也没有被重新标记为 failure exposure。

## 每个 seed 的 1M final-checkpoint 指标

| Arm | Seed | J nominal | J F0 | J pert mean | J pert worst | Collision | Timeout |
|---|---:|---:|---:|---:|---:|---:|---:|
| utr_sg | 2501 | 148.587 | 137.772 | 137.493 | 127.655 | 0.196 | 0.652 |
| utr_sg | 2502 | 58.281 | 51.435 | 51.783 | 49.044 | 0.059 | 0.923 |
| utr_sg | 2503 | 101.990 | 113.786 | 109.448 | 98.915 | 0.003 | 0.940 |
| drtp_sg | 2501 | 71.980 | 95.391 | 94.639 | 88.070 | 0.001 | 0.981 |
| drtp_sg | 2502 | 82.684 | 66.509 | 65.074 | 58.771 | 0.029 | 0.971 |
| drtp_sg | 2503 | 43.300 | 46.393 | 45.126 | 35.769 | 0.000 | 1.000 |
| egtr_sg | 2501 | 118.594 | 110.528 | 114.696 | 103.393 | 0.105 | 0.750 |
| egtr_sg | 2502 | 112.830 | 87.417 | 79.842 | 65.005 | 0.139 | 0.861 |
| egtr_sg | 2503 | 108.140 | 115.160 | 112.992 | 103.098 | 0.144 | 0.729 |

## EGTR 相对 paired UTR

| Seed | ΔF0 | Δpert mean | Δpert worst | Δcollision | Δtimeout | Existing catastrophic definition |
|---:|---:|---:|---:|---:|---:|---|
| 2501 | -27.244 | -22.797 | -24.262 | -0.092 | 0.098 | False |
| 2502 | 35.982 | 28.058 | 15.960 | 0.080 | -0.062 | False |
| 2503 | 1.374 | 3.544 | 4.183 | 0.141 | -0.211 | False |

既有 catastrophic definition 原样保留；它在 EGTR 的 1M 结果中没有触发。但 seed2503 的 collision 明显上升（`0.141`），同时 timeout 下降。这是 safety trade-off，不是 evaluator defect，也不能被 pooled return 掩盖。

## 冻结的 1M 机制审计

已完成的训练审计记录了每个 EGTR seed 在 122 个 boundary 中有 118 次 adaptive sampler update，存在非零但有界的 uniform 偏移，无 simplex/trust-region 违规，并且 runtime state 已持久化。因此 EGTR 既不是静默的 uniform fallback，也不是 technical invalid 实现。本次评估补齐了完整且 risk-set-valid 的性能和 safety records。

## 阶段门解释与停止状态

`P3_1M_TECHNICAL_AND_MECHANISM_PASS__SAFETY_REVIEW_REQUIRED` 表示 1M 的 technical 与 mechanism 部分有效，但 P3 合同没有量化“明显 safety warning”的判据。seed2503 已观察到的 collision trade-off 阻止我们把它自动写成 clean safety PASS；不得在看到结果后临时发明新的冻结阈值。

因此本报告**不授权 3M**。后续必须依据既有冻结合同作出明确决定：要么把已记录的 collision trade-off 视为合同中的 safety warning 并停止 P3；要么在任何续训前以 prospective amendment 明确 safety decision rule。两种路径均不允许调参、替换 seed、checkpoint promotion 或 EGTR-v2。
