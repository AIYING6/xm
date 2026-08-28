# DRTP 跨评价带可靠性诊断整合审计

**状态：** `COMPLETE_ZERO_TRAINING_DIAGNOSTIC`
**日期：** 2026-08-28

## 1. 审计目的

本审计检验正式 2301--2305 cohort 与独立 2401--2405 cohort 的方向差异是否可能主要由评价 tape 更换造成。该工作只重新使用既有最终 checkpoint，不训练、不恢复训练、不修改 checkpoint、不删除 seed，也不改写两批 cohort 原有结论。

## 2. 已核验证据

| 项目 | 结果 |
|---|---|
| 训练 cohort | 正式 2301--2305；独立 2401--2405 |
| 方法 | UTR-SG-MAPPO、DRTP-SG-MAPPO |
| 评价带 | tape490、tape500，均完成交叉评价 |
| 评价规模 | 48,000 条 raw episode records |
| checkpoint | 两批 cohort 的 20 个最终 checkpoint，加载 34/34 matching tensors |
| 技术状态 | `PASS`；无错误日志；完整 raw rows=48,000 |
| 统计边界 | cohort 分层；禁止合并为 n=10 |

主要端点的配对均值如下：

| cohort | tape | J_F0 | J_pert,mean | J_pert,worst |
|---|---|---:|---:|---:|
| formal_2301_2305 | 490 | +52.13 | +55.00 | +63.01 |
| formal_2301_2305 | 500 | +60.25 | +61.07 | +68.31 |
| independent_2401_2405 | 490 | -33.58 | -35.37 | -37.10 |
| independent_2401_2405 | 500 | -33.11 | -34.07 | -32.36 |

正式 cohort 在两张 tape 上均为正向，独立 cohort 在两张 tape 上均为反向；机器决策为 `COHORT_DIRECTION_PERSISTS_ACROSS_TAPES`。

## 3. 论文整合边界

该结果支持以下受限判断：评价 tape 更换不能单独解释两批 cohort 的方向反转，训练 cohort/seed 敏感性是更合理的实证定位。该结果不支持以下更强判断：

- 不识别具体 RNG source；
- 不证明进入了特定 policy basin；
- 不证明在线 adaptive weighting 相对于任意固定非均匀方案的必要性；
- 不把两批 cohort 合并为更大的独立样本；
- 不改写正式 cohort、独立 cohort 或历史裁决。

## 4. 文稿变更

主稿新增“跨评价带可靠性诊断”小节，报告四个 cohort×tape 单元的主要配对端点，并将“评价带更换”与“训练 cohort/seed 敏感性”明确区分。正文仍保留独立 cohort 的完整不利结果；没有将交叉诊断改写成新的 superiority experiment。

## 5. 复核资产

- `results/analysis/drtp_cross_tape_reliability/DRTP_CROSS_TAPE_RELIABILITY_REPORT.md`
- `results/analysis/drtp_cross_tape_reliability/DRTP_CROSS_TAPE_RELIABILITY_DECISION.json`
- `results/analysis/drtp_cross_tape_reliability/evaluation_manifest.json`
- `results/analysis/drtp_cross_tape_reliability/raw_episode_metrics.csv`

该整合属于 post hoc zero-training diagnostic，不授权任何新训练或后续实验。
