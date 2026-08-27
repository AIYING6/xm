# DRTP 跨评价带可靠性诊断合同

**状态：** `AUTHORIZED_ZERO_TRAINING_DIAGNOSTIC`
**日期：** 2026-08-27
**触发问题：** 正式 2301--2305 cohort 与独立 2401--2405 cohort 的 UTR--DRTP 方向不同，同时两者使用了不同的评价 tape。该诊断用于区分“方向是否随评价带改变”与“方向是否在同一训练 cohort 内跨评价带保持”。

## 1. 范围与禁止事项

本诊断只重新评价已完成的最终 10M checkpoint，不训练、不续训、不改算法、不改 PPO、不改环境、不改奖励、不选中间 checkpoint，也不删除种子。它不是新的 confirmatory training experiment，不能改写下列既有结论：

- 正式 2301--2305 cohort 的合同内结果；
- 独立 2401--2405 三方法 cohort 的合同内结果；
- 历史 development / held-out 的不利结论；
- `n=10` 不得作为同质训练重复池化的边界。

## 2. 冻结资产

| 训练 cohort | 方法 | 种子 | checkpoint | 原始评价带 |
|---|---|---|---|---|
| formal_2301_2305 | UTR-SG-MAPPO、DRTP-SG-MAPPO | 2301--2305 | 最终 10M | 490000--490099 |
| independent_2401_2405 | UTR-SG-MAPPO、DRTP-SG-MAPPO | 2401--2405 | 最终 10M | 500000--500099 |

归档 SHA256 必须分别为：

```text
formal:      cc3e2d29f382c332563c33957f5c109bbee4f42abb91b0d06b2b26cd3e618bdd
independent: 86a708244fa4d30935159a08d234c48feeb7a4c455208d58fbc58d308b4f4ae1
```

每一个 checkpoint 在运行前必须由对应 `run_manifest.json` 的最终 checkpoint SHA256 复核。

## 3. 固定 2 × 2 评价矩阵

每一个 UTR/DRTP checkpoint 都在两个已冻结的 12 条件、每条件 100 episode 的 tape 上评价：

| 训练 cohort | tape-490（490000--490099） | tape-500（500000--500099） |
|---|---:|---:|
| formal_2301_2305 | 原合同参考 | 新增零训练交叉评价 |
| independent_2401_2405 | 新增零训练交叉评价 | 原合同参考 |

总量为 `2 cohorts × 2 methods × 5 seeds × 2 tapes × 12 conditions × 100 episodes = 48,000` 条原始评价记录。训练 seed 仍是唯一独立单位；episode 仅用于同一 seed 的条件估计。

## 4. 预先定义的端点与解释

逐 cohort、逐 tape、逐训练 seed 计算：

- `J_nominal`；
- `J_F0`；
- `J_pert_mean`：十个训练 support 内跨扰动条件的均值；
- `J_pert_worst`：十个训练 support 内跨扰动条件的最差值；
- 故障条件平均 collision、timeout 与 constraint violation；
- `D_F0 = J_nominal - J_F0` 与 `D_pert_worst = J_nominal - J_pert_worst`。

`J_c/J_nominal` 只可作为补充描述，不能作为鲁棒性优越性或技术有效性的硬门槛，因为其分母会随正常工况能力变化。

对于每个 endpoint，报告 DRTP--UTR 的五个配对差、mean、median、wins/5 和 worst。风险集触发有效性、所有 episode 保留及 onset 前碰撞计数沿用原评价语义。

## 5. 预定义解释规则

本诊断不产生“方法 PASS/FAIL”裁决，只输出以下事实分类：

1. `COHORT_DIRECTION_PERSISTS_ACROSS_TAPES`：同一训练 cohort 内，两个 tape 上端点方向一致；这排除“仅由评价带变更造成方向反转”的解释，但不能单独证明某一具体训练随机源因果。
2. `TAPE_SENSITIVITY_OR_INTERACTION_OBSERVED`：至少一个 cohort 的两个 tape 间主要端点方向改变；这表明评价带或其与 checkpoint 的交互不可忽略。
3. `MIXED_ENDPOINT_PATTERN`：不同端点给出不同模式；只报告逐端点事实，不简化为单一机制。

无论结果如何，两个 cohort 不合并为 `n=10`；若进行描述性跨 cohort 汇总，必须分层显示 cohort，不得报告为同质总体效应。

## 6. 输出与停止规则

输出目录必须是新的 `results/analysis/drtp_cross_tape_reliability/`，并至少包含 raw records、逐条件汇总、逐 seed 端点、逐 cohort×tape 配对效应、machine-readable decision 和 Markdown report。完成报告后停止；任何 static baseline、参数匹配 NoGraph 或新故障组合训练均需单独授权。
