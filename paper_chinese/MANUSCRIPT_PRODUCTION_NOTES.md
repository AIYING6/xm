# 中文主稿生产台账

本文件不属于论文正文；它记录主稿对象的证据来源、当前可用性和投稿前仍需补齐的元数据。

| 主稿对象 | 状态 | 权威来源 |
|---|---|---|
| 图 1：三关系方法图 | 已重绘并目视核验 | `docs/figure_contracts/FACT_MANIFEST_METHOD_FIGURE.md`（MF01–MF10）；`figures/fig1_three_relation_task_graph.provenance.txt` |
| 图 2：精简 KM/RMST | 已从锁定 held-out 输入重渲染并目视核验 | `docs/statistics/survival_results_v1_1/`；`docs/statistics/P1B_DECISION_MEMO_V1_1.md`；`figures/fig2_early_recovery_km.provenance.txt` |
| 表 1：主结果 | 数值已锁定 | `docs/paper_assets_v1_5/canonical_results_v1_5.csv`；P1B memo |
| 表 2：消融 | 数值已锁定，解释受限 | P1B memo；`docs/STATISTICAL_PROVENANCE_AUDIT.md` |
| 表 3：OOD 边界 | 数值已锁定 | `docs/statistics/p3a_ood_results_v1_1/p3a_ood_stats_lock_memo.md` |
| Gate Prior 轨迹 | 禁止使用 | `docs/FIGURE_EVIDENCE_AUDIT.md`（现有图缺 Full-with-Prior 曲线） |

## 投稿前待补

- 目标期刊和最终 Word/LaTeX 模板；
- 作者、单位、基金、贡献、利益冲突、数据及代码可用性；
- 若要保留 Gate Prior 轨迹，须用锁定双组资产重渲染并记录独立统计单位、汇总规则和脚本；
- `Wilson95` 的定义未完整记录，不得进入正文；
- 效率 profile 的 canonical `n=1`，只能作为补充材料中的单次成本披露，除非补齐硬件与重复计时协议；
- 参考文献将从已核验的 `paper_latex_3d_en/references.bib` 按目标期刊样式导出。
