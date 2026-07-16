# 论文证据链状态

日期：2026-07-13

## 1. 当前主张

论文当前最稳主张：

```text
EA-RG-MAPPO-S 在有限通信无人机协同追逃任务中，相比 MAPPO 和 GAT-MAPPO，
具有更稳定的跨通信半径性能和更低碰撞率。
```

不应主张：

```text
1. 已实现高精度目标意图识别；
2. 已验证完整 6DOF 空战、导弹、雷达和有人机协同系统；
3. 方法在所有可能场景下全面优于所有基线。
```

## 1.1 LAG/JSBSim 扩展证据边界

已新增 LAG 状态到 EA-RG-MAPPO-S role graph 的 duck-typed 适配层和 26 项 smoke test：

```text
envs/lag_role_graph_adapter.py
envs/lag_role_graph_wrapper.py
scripts/test_lag_role_graph_adapter.py
scripts/test_lag_role_graph_wrapper.py
docs/lag_role_graph_adapter_test.md
docs/lag_role_graph_wrapper_test.md
results/lag_role_graph_adapter_test.csv
results/lag_role_graph_wrapper_test.csv
```

它能支撑的说法是：当前方法的图输入接口已经按 LAG-like 6DOF 状态结构预留，后续可接入真实 JSBSim reset/step。它不能支撑的说法是：已经完成真实 LAG/JSBSim 训练或完整 6DOF 空战验证。

## 2. 主结果证据

文件：

```text
results/final_comm_300_eval.csv
results/final_comm_300_summary.csv
results/latex_final_comm_300_table.tex
```

实验设置：

```text
methods = MAPPO, GAT-MAPPO, EA-RG-MAPPO-S
target_policy = mixed
target_speed = 0.75
communication_radius = 4, 6, 8, 10
episodes = 300 per seed
seeds = 0, 1, 2
```

支撑的结论：

```text
1. EA-RG-MAPPO-S 成功率最高或接近最高；
2. EA-RG-MAPPO-S 碰撞率显著低于 MAPPO/GAT-MAPPO；
3. EA-RG-MAPPO-S 标准差更小，说明稳定性更好。
```

关键数字：

| Radius | EA-RG Success | EA-RG Collision |
|---:|---:|---:|
| 4 | 0.926 ± 0.004 | 0.054 ± 0.007 |
| 6 | 0.919 ± 0.012 | 0.064 ± 0.006 |
| 8 | 0.890 ± 0.021 | 0.083 ± 0.012 |
| 10 | 0.879 ± 0.017 | 0.086 ± 0.020 |

主张-证据矩阵：

```text
docs/claim_evidence_matrix.md
results/claim_evidence_matrix.csv
claims_checked = 9
failures = 0
```

该矩阵把每条论文可写主张绑定到具体 CSV、表、图和推荐措辞边界，后续写作应以此作为主张上限。

稿件证据引用审计：

```text
docs/manuscript_evidence_reference_audit.md
results/manuscript_evidence_reference_audit.csv
references_checked = 51
failures = 0
```

该审计检查中英文 LaTeX 稿件是否实际引用主张矩阵需要的表、图、数值和边界声明，防止证据链只存在于工程文档而没有进入稿件。

双语数值一致性审计：

```text
docs/bilingual_numeric_consistency_audit.md
results/bilingual_numeric_consistency_audit.csv
numeric_markers_checked = 47
failures = 0
```

该审计从结果 CSV 派生关键数值，并检查这些数值是否同时出现在中英文 LaTeX 稿件中，降低双语稿件数字漂移风险。

LaTeX 标签引用完整性审计：

```text
docs/latex_reference_integrity_audit.md
results/latex_reference_integrity_audit.csv
reference_checks = 86
failures = 0
```

该审计检查中英文 LaTeX 的关键表图 label 是否存在、关键 label 是否被正文引用，以及是否存在重复 label 或无法解析的 ref。

双语稿件完整性审计：

```text
docs/bilingual_manuscript_completeness_audit.md
results/bilingual_manuscript_completeness_audit.csv
checks = 36
failures = 0
action_items = 8
```

该审计检查中英文稿件的章节、摘要、关键词、图表、引用、关键边界标记和投稿前行动项。作者、数据可用性、基金/利益声明和期刊 BibTeX 样式暂列为 action item。

投稿行动项清单：

```text
docs/submission_action_register.md
results/submission_action_register.csv
items = 10
blocked = 2
deferred = 1
open = 7
```

该清单把 PDF 工具链、期刊模板、作者信息、声明、补充材料、可选扩展种子和 LAG/JSBSim 阻塞事项集中管理。它不削弱当前证据边界，只用于投稿执行规划。

实验扩展决策计划：

```text
docs/experiment_extension_decision_plan.md
results/experiment_extension_decision_plan.csv
options = 7
blocked = 1
deferred = 3
ready = 3
```

该计划明确 5-seed 扩展、真实 LAG reset 探针、重训结构消融、通信 dropout 加长评估、完整 6DOF 训练和导弹/雷达/有人机协同扩展的优先级与触发条件。

稳定 artifact checksum 清单：

```text
docs/reproducibility_checksum_manifest.md
results/reproducibility_checksum_manifest.csv
docs/reproducibility_checksum_verification.md
results/reproducibility_checksum_verification.csv
artifacts_hashed = 169
artifacts_verified = 169
failures = 0
```

该清单记录稳定复现包文件的 SHA256 和 size，并新增反向校验报告用于确认文件未损坏或被替换。动态构建报告、schema/provenance 自身、checksum 自身和 checksum verification 输出被排除，避免循环哈希。

## 3. 消融证据

文件：

```text
results/paper_comm_results.csv
results/latex_ablation_comm_table.tex
```

实验设置：

```text
methods = RG-MAPPO, EA-RG-MAPPO, EA-RG-MAPPO-S
episodes = 100 per seed
seeds = 0, 1, 2
```

支撑的结论：

```text
1. 相对边特征能降低 radius=4 下碰撞率；
2. 固定半径 edge-aware 训练在 radius=10 泛化不足；
3. staged random-radius fine-tuning 改善 radius=10 泛化，使跨半径表现更均衡。
```

注意：

```text
消融表是 100 episodes per seed，不应和 300-episode final table 混用为同一张主表。
```

## 4. 可视化证据

文件：

```text
results/figures/final_300_success_rate.png
results/figures/final_300_collision_rate.png
results/figures/per_seed_success_scatter.png
results/figures/per_seed_collision_scatter.png
results/figures/trajectory_ri_advantage_r4.png
results/figures/trajectory_ri_advantage_r10.png
results/figures/ri_attention_heatmap_r4.png
results/figures/ri_attention_heatmap_r10.png
```

支撑的结论：

```text
1. 主曲线图支撑跨半径成功率/碰撞率趋势；
2. per-seed scatter 支撑 seed 稳定性；
3. 轨迹图支撑定性成功/失败案例；
4. 注意力热力图支撑通信半径改变图信息聚合。
```

图表资产审计：

```text
docs/figure_asset_audit.md
results/figure_asset_audit.csv
figures_checked = 22
warnings = 0
```

该审计只证明图像文件存在、尺寸合理且不是近似空白图，不评价图表美观性或科学结论强弱。

实验预算一致性审计：

```text
docs/evaluation_budget_audit.md
results/evaluation_budget_audit.csv
budget_groups_checked = 6
failures = 0
```

该审计用于防止 300-episode 主表、100-episode 附录实验、50-episode 诊断和 30-episode 机制诊断在正文中被混用。

方法命名一致性审计：

```text
docs/method_naming_audit.md
results/method_naming_audit.csv
publishable_files_checked = 27
failures = 0
```

论文投稿材料统一使用 `EA-RG-MAPPO-S` 作为最终方法名；`ri_gmappo_edge_stage2_rand_seed*_20` 仅作为代码/结果目录映射保留在复现材料中。

补充 CSV schema 审计：

```text
docs/supplemental_csv_schema_audit.md
results/supplemental_csv_schema_audit.csv
csv_files_checked = 31
failures = 0
```

该审计用于检查补充 CSV 的字段、行数、关键取值域和 rate 列范围，避免后续结果整理时出现格式漂移。

结果溯源审计：

```text
docs/result_provenance_audit.md
results/result_provenance_audit.csv
artifacts_checked = 54
failures = 0
```

该审计用于记录每张投稿表、图和关键报告对应的源数据与生成脚本，降低后续补充材料打包或论文改稿时出现“图表来源断链”的风险。

## 5. Edge Feature 机制诊断

文件：

```text
results/edge_feature_ablation_eval.csv
results/edge_feature_ablation_summary.csv
results/edge_feature_ablation_notes.md
results/figures/edge_feature_ablation_delta.png
```

实验设置：

```text
method = EA-RG-MAPPO-S
target_policy = mixed
target_speed = 0.75
communication_radius = 4, 8
episodes = 30 per seed
seeds = 0, 1, 2
mode = evaluation-time feature masking, no retraining
```

当前结论：

```text
1. 评估时单独屏蔽位置、距离、方位或速度边特征时，30-episode 均值变化较小；
2. 屏蔽 comm_reachable/target_node_flag 时，在 radius=4 和 radius=8 下均出现小幅成功率下降和碰撞率上升；
3. 屏蔽全部 edge feature 后没有灾难性退化，说明 node feature、adjacency mask 和局部观测存在冗余；
4. 因此该实验只能作为机制诊断，主消融证据仍应使用训练期消融表。
5. `edge_feature_ablation_delta.png` 可作为附录级可视化，展示不同 edge feature 分组被屏蔽后的 delta。
```

论文使用边界：

```text
可以写：评估时边特征屏蔽显示出弱敏感性，其中通信/目标标记分量退化最一致。
不能写：评估时置零结果单独证明某类边特征训练机制最优。
```

## 6. Target Speed 泛化证据

文件：

```text
results/speed_robustness_eval.csv
results/speed_robustness_summary.csv
results/speed_robustness_notes.md
results/figures/speed_robustness_success_r4.png
results/figures/speed_robustness_collision_r4.png
results/figures/speed_robustness_success_r8.png
results/figures/speed_robustness_collision_r8.png
```

实验设置：

```text
methods = MAPPO, GAT-MAPPO, EA-RG-MAPPO-S
target_policy = mixed
target_speed = 0.60, 0.75, 0.90
communication_radius = 4, 8
episodes = 100 per seed
seeds = 0, 1, 2
mode = evaluation only, no retraining
```

关键结论：

```text
1. radius=4, target_speed=0.90 时，EA-RG-MAPPO-S 成功率为 0.867，碰撞率为 0.097；
   MAPPO/GAT-MAPPO 对应碰撞率分别为 0.240/0.237。
2. radius=8, target_speed=0.90 时，EA-RG-MAPPO-S 成功率为 0.837，碰撞率为 0.130；
   MAPPO/GAT-MAPPO 对应碰撞率分别为 0.300/0.203。
3. 随目标速度升高，三种方法成功率均下降，但 EA-RG-MAPPO-S 在两个通信半径下保持最低碰撞率。
```

论文使用边界：

```text
可以写：速度泛化附录评估表明，EA-RG-MAPPO-S 的低碰撞优势不只来自单一 target_speed 设置。
不能写：该 100-episode 附录评估替代了 300-episode 主表。
```

## 7. 通信 dropout 退化诊断证据

文件：

```text
results/comm_dropout_robustness_eval.csv
results/comm_dropout_robustness_summary.csv
results/comm_dropout_robustness_notes.md
results/latex_comm_dropout_robustness_table.tex
results/comm_dropout_paired_statistics.csv
results/comm_dropout_paired_statistics.md
results/latex_comm_dropout_paired_ci_table.tex
```

实验设置：

```text
methods = MAPPO, GAT-MAPPO, EA-RG-MAPPO-S
target_policy = mixed
target_speed = 0.75
communication_radius = 4, 8
communication_dropout_prob = 0.00, 0.25, 0.50
episodes = 50 per seed
seeds = 0, 1, 2
mode = evaluation-time communication link dropout, no retraining
```

关键结论：

```text
1. dropout=0.50, radius=4 时，EA-RG-MAPPO-S 碰撞率为 0.047；
   MAPPO/GAT-MAPPO 对应碰撞率为 0.300/0.167。
2. dropout=0.50, radius=8 时，EA-RG-MAPPO-S 碰撞率为 0.053；
   MAPPO/GAT-MAPPO 对应碰撞率为 0.293/0.173。
3. 在该轻量诊断的全部半径和 dropout 概率下，EA-RG-MAPPO-S 的平均碰撞率均低于两个基线。
4. 新增 seed-paired 描述性置信区间表，作为附录级稳健性补充证据；由于 n=3，不应写成决定性显著性结论。
```

论文使用边界：

```text
可以写：通信链路随机丢失诊断进一步支持 EA-RG-MAPPO-S 的低碰撞鲁棒性。
不能写：该 50-episode 诊断替代 300-episode 主结果，或证明真实无线链路/复杂网络干扰已被完整验证。
```

## 7.1 跨条件综合鲁棒性摘要

文件：

```text
results/aggregate_robustness_summary.csv
results/aggregate_robustness_summary.md
results/latex_aggregate_robustness_table.tex
```

定义：

```text
final_cross_radius = 300-episode final evaluation across radii 4, 6, 8, 10
dropout_diagnostic = 50-episode dropout diagnostic across radii 4/8 and dropout 0/0.25/0.5
mean_margin = mean_success - mean_collision
conservative_margin = worst_success - worst_collision
```

关键结果：

```text
Final cross-radius:
EA-RG-MAPPO-S mean_success=0.903, mean_collision=0.072, conservative_margin=0.793.
MAPPO conservative_margin=0.479, GAT-MAPPO conservative_margin=0.606.

Dropout diagnostic:
EA-RG-MAPPO-S mean_success=0.892, mean_collision=0.070, conservative_margin=0.747.
MAPPO conservative_margin=0.273, GAT-MAPPO conservative_margin=0.580.
EA-RG-MAPPO-S worst_collision=0.107, MAPPO worst_collision=0.320, GAT-MAPPO worst_collision=0.187.
```

论文使用边界：

```text
可以写：综合摘要进一步压缩展示 EA-RG-MAPPO-S 的跨半径和通信退化稳定性。
不能写：该综合 margin 是新的优化目标、标准 benchmark 指标或可替代逐条件主表。
```

## 7.2 通信半径插值诊断

文件：

```text
results/radius_interpolation_eval.csv
results/radius_interpolation_summary.csv
results/radius_interpolation_notes.md
results/latex_radius_interpolation_table.tex
```

实验设置：

```text
methods = MAPPO, GAT-MAPPO, EA-RG-MAPPO-S
target_policy = mixed
target_speed = 0.75
communication_radius = 5, 7, 9
episodes = 50 per seed
seeds = 0, 1, 2
mode = evaluation at unseen radii, no retraining
```

关键结果：

```text
radius=5: EA collision=0.067, MAPPO collision=0.227, GAT-MAPPO collision=0.113.
radius=7: EA collision=0.100, MAPPO collision=0.200, GAT-MAPPO collision=0.140.
radius=9: EA collision=0.067, MAPPO collision=0.153, GAT-MAPPO collision=0.173.
```

论文使用边界：

```text
可以写：未见通信半径诊断支持 EA-RG-MAPPO-S 的跨半径低碰撞趋势。
不能写：该 50-episode 插值诊断替代 300-episode 主表，或证明所有通信半径均已充分覆盖。
```

## 8. 负面诊断证据

文件：

```text
results/intent_confusion_ri_staged_r8.csv
results/intent_confusion_ri_balanced_seed1_r8.csv
results/visualization_and_intent_diagnostics.md
```

结论：

```text
当前 intent head balanced accuracy 接近随机水平。
因此 intent branch 只能作为辅助探索，不能作为主创新点。
```

## 9. 自动一致性检查

文件：

```text
scripts/check_paper_claim_consistency.py
scripts/check_paper_text_risk.py
```

当前检查：

```text
1. 主结果：EA-RG-MAPPO-S 在 radius=4/6/8/10 下碰撞率低于 0.10，且低于 MAPPO/GAT-MAPPO；
2. 速度泛化：target_speed=0.90 时，EA-RG-MAPPO-S 在 radius=4/8 下碰撞率低于 MAPPO/GAT-MAPPO；
3. Edge feature 诊断：屏蔽 comm_reachable/target_node_flag 时成功率下降、碰撞率上升，同时 full edge masking 不出现灾难性退化。
4. 通信 dropout 诊断：EA-RG-MAPPO-S 在 radius=4/8、dropout=0/0.25/0.5 下平均碰撞率低于 MAPPO/GAT-MAPPO。
```

用途：

```text
该脚本用于防止后续改表、重跑实验或扩写正文时出现关键数字主张漂移。
文本风险审计用于防止发布稿中出现旧路线残留、完整 6DOF 已验证、高精度意图识别或全面最优等过度主张。
```

## 10. 当前缺口

投稿前仍建议补：

```text
1. 正式期刊/会议引用，减少 arXiv-only 引用；
2. 目标期刊模板适配；
3. PDF 编译和版式检查；
4. 可选 LAG/JSBSim 小规模迁移验证。
```

当前不紧急：

```text
1. 5-seed 主表；
2. 继续短期微调 intent head；
3. 完整 6DOF + 导弹 + 雷达系统。
```

## 11. LAG/JSBSim 迁移准备证据

文件：

```text
scripts/probe_lag_jsbsim_migration.py
docs/lag_jsbsim_migration_probe.md
results/lag_jsbsim_migration_probe.csv
```

当前结论：

```text
1. LAG MultipleCombat 相关 env/task/base env/simulator wrapper 文件存在；
2. LAG 动作空间为 MultiDiscrete([41, 41, 41, 30])，当前 2D 9 动作头不能直接复用；
3. 观测结构可支撑 6DOF role graph 构造，包含姿态、速度、相对对象信息；
4. 已有 synthetic LAG graph smoke 结果为 400 行，未出现 NaN/Inf；
5. 真实 JSBSim 验证尚未完成，阻塞点是 envs/JSBSim/data 子模块缺失以及 multiplecombat_env 的 human_task 导入缺口。
```

论文使用边界：

```text
可以写：本文方法的图表示层具备迁移到 LAG/JSBSim 的接口基础。
不能写：本文已经完成真实 LAG/JSBSim 或 6DOF 空战验证。
```
