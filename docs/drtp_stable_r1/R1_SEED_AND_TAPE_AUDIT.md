# R1 seed 与 tape 审计

审计日期：2026-08-29（零训练）。

## Training seeds

候选 `3001, 3002, 3003, 3004, 3005` 通过以下两项独立检查：

1. 在 `results/`、`artifacts/`、`archival/`、`tmp/` 与 `output/` 下不存在名称精确等于 `seed3001` 至 `seed3005` 的结果目录；
2. 在 `configs/`、`scripts/`、`docs/`、`algorithms/`、`envs/` 与 `paper/` 的非生成内容中，不存在将该数字作为 seed、manifest seed 或命令行 `--seed` 使用的显式记录。

因此这五个 seed 在本仓库可见证据中为 clean candidates。该审计不把训练日志行号、update 编号或 episode ID 中偶然出现的相同数字误判为 seed 使用。

## Evaluation tape

`540000–540099` 不在此前冻结 development、formal、independent 或 additional-unseen namespaces 中；R1 tape 显式禁止历史命名空间 `420000–440099`、`490000–510099` 与 `530000–530099`。每种条件复用相同 100 个 base IDs，仅改变冻结的 failure tuple。

该 tape 只用于 R1 development；不能升级为 confirmatory/held-out tape，也不能用于历史 cohort 重评价。
