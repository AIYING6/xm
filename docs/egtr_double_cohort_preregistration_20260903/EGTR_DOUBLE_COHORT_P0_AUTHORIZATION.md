# EGTR 双 cohort 前瞻性复制：P0 授权边界

本文件记录 `EGTR_DOUBLE_COHORT_PREREGISTRATION_AUDIT` 的唯一授权：执行零训练预注册审计。该审计冻结 EGTR 的既有 sampler-only 定义、fresh seed registry、fresh development-only evaluation registry、成熟预算和机器可执行的双 cohort 决策规则。

P0 禁止 UTR、Original DRTP 或 EGTR 的训练、历史 checkpoint 的性能重跑、任何 1M/3M/10M 轨迹、评估、打包、阈值调节、自动续跑或算法修改。

2501–2503 的 EGTR P3 结果只能作为已见 development evidence；不得参与阈值、seed 或最终 confirmatory 判断。数值门槛仅复用早于 EGTR 的 KLR 复制合同中由非 EGTR cross-tape variation 冻结的噪声与安全界限。

P0 的唯一可接受结论为：`EGTR_DOUBLE_COHORT_PREREGISTRATION_READY`、`EGTR_PREREGISTRATION_THRESHOLD_UNRESOLVED`、`EGTR_PREREGISTRATION_EVIDENCE_CONTAMINATION` 或 `EGTR_PREREGISTRATION_CONTRACT_INCOMPLETE`。即便 READY，也不构成任何训练授权。
