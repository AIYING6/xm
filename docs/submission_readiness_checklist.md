# 投稿前检查清单

日期：2026-07-13

## 1. 当前论文主线

建议主线：

```text
面向有限通信无人机协同追逃的边特征增强角色图多智能体强化学习方法
```

建议方法名：

```text
EA-RG-MAPPO-S
```

主张边界：

```text
可以主张：有限通信下更稳定、碰撞率更低、跨半径鲁棒性更好。
不要主张：高精度目标意图识别、完整 6DOF 空战系统、导弹/雷达/有人机协同已经验证。
```

## 2. 已有材料

### 2.0 复现与证据链

```text
docs/reproducibility_manifest.md
docs/claim_evidence_matrix.md
docs/manuscript_evidence_reference_audit.md
docs/bilingual_numeric_consistency_audit.md
docs/latex_reference_integrity_audit.md
docs/bilingual_manuscript_completeness_audit.md
docs/submission_action_register.md
docs/experiment_extension_decision_plan.md
docs/reproducibility_checksum_manifest.md
docs/reproducibility_checksum_verification.md
docs/supplemental_data_readme.md
docs/evidence_chain_status.md
docs/runtime_environment_report.md
docs/checkpoint_inventory.md
docs/paper_asset_build_report.md
docs/submission_readiness_report.md
docs/submission_package_manifest.md
docs/english_manuscript_readiness_audit.md
docs/figure_asset_audit.md
docs/evaluation_budget_audit.md
docs/method_naming_audit.md
docs/supplemental_csv_schema_audit.md
docs/result_provenance_audit.md
docs/journal_target_shortlist.md
docs/journal_template_migration_plan.md
docs/lag_jsbsim_migration_probe.md
docs/lag_role_graph_adapter_test.md
docs/lag_role_graph_wrapper_test.md
scripts/check_reproducibility_artifacts.py
scripts/build_paper_assets.py
```

### 2.1 方法说明

```text
docs/paper_method_section_draft.md
docs/paper_direction_revision_after_intent_diagnostic.md
docs/english_abstract_and_contributions.md
docs/english_introduction_draft.md
docs/english_related_work_draft.md
docs/english_problem_method_draft.md
docs/english_experiments_draft.md
docs/english_discussion_conclusion_draft.md
docs/english_manuscript_draft.md
```

### 2.2 实验说明

```text
docs/paper_experiment_section_draft.md
docs/current_progress_and_next_plan.md
```

### 2.3 主结果表

```text
results/paper_result_tables.md
results/paper_comm_results.csv
results/latex_main_comm_table.tex
results/final_comm_300_summary.csv
results/latex_final_comm_300_table.tex
results/final_300_paired_statistics.csv
results/final_300_paired_statistics.md
results/latex_final_300_paired_ci_table.tex
results/comm_dropout_robustness_eval.csv
results/comm_dropout_robustness_summary.csv
results/comm_dropout_robustness_notes.md
results/latex_comm_dropout_robustness_table.tex
results/comm_dropout_paired_statistics.csv
results/comm_dropout_paired_statistics.md
results/latex_comm_dropout_paired_ci_table.tex
results/aggregate_robustness_summary.csv
results/aggregate_robustness_summary.md
results/latex_aggregate_robustness_table.tex
results/claim_evidence_matrix.csv
results/manuscript_evidence_reference_audit.csv
results/bilingual_numeric_consistency_audit.csv
results/latex_reference_integrity_audit.csv
results/bilingual_manuscript_completeness_audit.csv
results/submission_action_register.csv
results/experiment_extension_decision_plan.csv
results/reproducibility_checksum_manifest.csv
results/reproducibility_checksum_verification.csv
results/radius_interpolation_eval.csv
results/radius_interpolation_summary.csv
results/radius_interpolation_notes.md
results/latex_radius_interpolation_table.tex
results/figure_asset_audit.csv
results/evaluation_budget_audit.csv
results/method_naming_audit.csv
results/supplemental_csv_schema_audit.csv
results/result_provenance_audit.csv
results/lag_role_graph_adapter_test.csv
results/lag_role_graph_wrapper_test.csv
results/latex_training_settings_table.tex
results/latex_ablation_comm_table.tex
results/latex_speed_robustness_table.tex
results/latex_edge_feature_ablation_table.tex
```

### 2.4 附录结果

```text
results/per_seed_comm_appendix.md
results/per_seed_comm_appendix.csv
results/speed_robustness_summary.csv
results/edge_feature_ablation_summary.csv
```

### 2.5 图表

```text
results/figures/method_overview_ea_rg_mappo_s.png
results/figures/comm_success_rate.png
results/figures/comm_collision_rate.png
results/figures/per_seed_success_scatter.png
results/figures/per_seed_collision_scatter.png
results/figures/trajectory_ri_advantage_r4.png
results/figures/trajectory_ri_advantage_r10.png
results/figures/ri_attention_heatmap_r4.png
results/figures/ri_attention_heatmap_r10.png
results/figures/speed_robustness_success_r4.png
results/figures/speed_robustness_collision_r4.png
results/figures/speed_robustness_success_r8.png
results/figures/speed_robustness_collision_r8.png
results/figures/comm_dropout_success_rate.png
results/figures/comm_dropout_collision_rate.png
results/figures/radius_interpolation_success_rate.png
results/figures/radius_interpolation_collision_rate.png
results/figures/edge_feature_ablation_delta.png
```

### 2.6 诊断材料

```text
results/visualization_and_intent_diagnostics.md
results/intent_confusion_ri_staged_r8.csv
results/intent_confusion_ri_balanced_seed1_r8.csv
```

## 3. 已完成的关键证据

### 3.1 全方法 3-seed 主表

已覆盖：

```text
MAPPO
GAT-MAPPO
RI no-edge / RG-MAPPO
RI edge fixed-r8 / EA-RG-MAPPO
RI edge staged / EA-RG-MAPPO-S
```

评价设置：

```text
target_policy = mixed
target_speed = 0.75
communication_radius = 4, 6, 8, 10
episodes = 100 per seed
seeds = 0, 1, 2
```

### 3.2 可解释可视化

已覆盖：

```text
1. 通信半径-成功率曲线
2. 通信半径-碰撞率曲线
3. per-seed scatter
4. 成功/失败轨迹案例
5. RI attention heatmap
```

### 3.3 风险诊断

已发现并记录：

```text
当前 intent head balanced accuracy 不足，不能作为强主张。
```

这个诊断反而能提升论文叙事可信度：说明方法主线已经从不可靠的“意图识别”修正为更有证据支撑的“边特征角色图有限通信鲁棒性”。

## 4. 投稿前最小还需补充

### Priority 1：正文初稿

需要将以下文档整合为论文初稿：

```text
docs/paper_method_section_draft.md
docs/paper_experiment_section_draft.md
results/paper_result_tables.md
```

建议先写中文，再转英文。

### Priority 2：方法命名统一

当前代码和结果中仍有历史命名：

```text
RI-GMAPPO
RI edge staged
RI edge fixed-r8
```

论文中建议统一映射：

```text
RI no-edge        -> RG-MAPPO
RI edge fixed-r8  -> EA-RG-MAPPO
RI edge staged    -> EA-RG-MAPPO-S
```

代码目录可以暂时不改，论文表述统一即可。

### Priority 3：图表润色

需要检查：

```text
1. 图中文字是否适合论文；
2. 颜色是否区分清楚；
3. 线宽、字号是否够；
4. 中文论文/英文论文对应字体是否统一。
```

当前图可作为研究版，投稿前建议再导出 PDF/SVG。

### Priority 4：统计可信度增强

已完成增强版：

```text
3 seeds, 300 episodes per seed for MAPPO/GAT/EA-RG-MAPPO-S final comparison
```

最低可接受：

```text
3 seeds, 100 episodes per seed
```

更稳妥：

```text
3 seeds, 300 episodes per seed
```

最好但成本更高：

```text
5 seeds, 300 episodes per seed
```

现实建议：

```text
先不补 5 seeds。
当前 300 episodes per seed 已足够支撑主表，除非目标期刊要求更强统计显著性。
```

当前复现 artifact 检查已通过：

```text
required files checked: 50
required scripts checked: 16
OK
```

### Priority 5：LAG/6DOF 小验证

当前不是必须，但如果时间允许，可以做一个最小迁移验证：

```text
LAG/JSBSim 中 2v2 NoWeapon 场景
只迁移 role graph + edge feature encoder
不加入导弹和雷达
```

这会显著增强论文应用价值，但调试成本较高。建议在二维结果和论文初稿稳定后再做。

## 5. 暂时不建议继续投入的方向

### 5.1 不建议继续短期硬修 intent head

原因：

```text
balanced loss 诊断没有明显提升 balanced accuracy。
问题更可能是标签定义和可观测性，而不是简单训练不足。
```

除非重新设计：

```text
1. 短时历史输入；
2. 目标转弯率/速度变化特征；
3. 更均衡的目标策略采样；
4. balanced accuracy 作为主指标。
```

否则不应把 intent 作为主创新。

### 5.2 不建议马上上完整 6DOF + 导弹 + 雷达

原因：

```text
系统复杂度会掩盖当前算法贡献。
调试周期长，容易拖慢论文产出。
```

更合理顺序：

```text
二维论文结果定稿 -> 小规模 LAG 迁移 -> 再扩展导弹/雷达/有人机协同。
```

## 6. 下一步推荐执行

当前已具备完整 LaTeX 草稿工程：

```text
paper_latex/main.tex
paper_latex/sections/
paper_latex/references.bib
paper_latex_en/main.tex
paper_latex_en/sections/
```

当前最建议下一步：

```text
1. 在装有 xelatex 的环境中编译 PDF 并检查版面；
2. 继续润色英文/中文表达，尤其是摘要、引言和实验分析；
3. 若投稿目标较高，再考虑补 5 seeds 或 LAG/JSBSim 小规模迁移验证。
```

然后再决定是否补 300-episode 评估。

已具备 LaTeX 主结果表：

```text
results/latex_main_comm_table.tex
results/latex_final_comm_300_table.tex
results/latex_ablation_comm_table.tex
```
