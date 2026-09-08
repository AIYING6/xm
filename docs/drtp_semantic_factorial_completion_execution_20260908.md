# DRTP 语义消融析因补全执行说明

本执行只补训 UTR 与原始 DRTP 各五个 10M 轨迹，种子固定为 80011--80015。已完成的
Fixed-DRTP 与 Random-DRTP 由已审计结果归档恢复，不会重训、续训或覆盖。完成后，四种方法
在同一冻结终点评价带上统一评估，训练种子是唯一独立统计单位。

## 上传文件

1. `DRTP_SEMANTIC_ABLATION_FACTORIAL_COMPLETION_10M_V1.zip`
2. `DRTP_SEMANTIC_ABLATION_FACTORIAL_COMPLETION_10M_V1.zip.sha256`
3. `drtp_semantic_ablation_nonpaired_10m_results.tar.gz`
4. `drtp_semantic_ablation_nonpaired_10m_results.tar.gz.sha256`

已审计的既有结果归档 SHA256：

`f088e5aae92c695d5acabdfb703fe49e0dda82b55c3f2be407c773d652b86ce9`

## 完成后的必备输出

- `SEMANTIC_FACTORIAL_COMPLETION_ENDPOINTS.csv`
- `SEMANTIC_FACTORIAL_COMPLETION_COHORT_SUMMARY.csv`
- `SEMANTIC_FACTORIAL_COMPLETION_PAIRED_DELTAS.csv`
- `SEMANTIC_FACTORIAL_COMPLETION_EFFECT_SUMMARY.csv`
- `SEMANTIC_FACTORIAL_COMPLETION_INTERACTION.csv`

报告不设性能导向的自动通过/失败门；它只验证完整性，并报告四个预先定义的析因对比：

1. Fixed-DRTP minus UTR；
2. Random-DRTP minus UTR；
3. DRTP minus Fixed-DRTP；
4. DRTP minus Random-DRTP。

不得将 episode 视为独立训练重复，也不得根据中途曲线改动算法或替换种子。
