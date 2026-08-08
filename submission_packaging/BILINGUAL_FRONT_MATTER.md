# 《航空学报》匿名稿双语前置字段锁定稿

本文件是匿名 Word 模板稿的唯一双语前置字段来源。译文仅对应已冻结中文稿，不增加方法、数值、机制或结论。

## Title

**中文：** 异构无人机故障后任务链恢复的多关系图决策<br>
**English:** Multi-relational graph decision-making for post-failure task-chain recovery in heterogeneous unmanned aerial vehicles

## Abstract

**中文：** 见 `paper_chinese/manuscript_zh.md` 的“摘要”段；该段为投稿主源。<br>
**English:** Critical relay failures can interrupt task chains in heterogeneous UAV formations operating with intermittent sensing and constrained communication. Terminal success alone does not reveal when usable coordination returns while the failure persists. We study post-failure task-chain recovery and propose Edge-Aware Role-Graph MAPPO (EA-RG). Under centralized training and decentralized execution, EA-RG represents perception, environment-delivered communication and task support as three relations, which are aggregated by relation-specific edge-aware graph attention and a union-graph residual path. In a locked nominal held-out evaluation with matched failure-exposed episodes, we used Kaplan–Meier curves and restricted mean survival time (RMST). Across three independent training seeds, EA-RG had an RMST of 11.81 steps versus 15.51 steps for MAPPO in the pre-specified 80-step node-failure window; the hierarchical paired-bootstrap 95% interval for their contrast was [−7.16, −1.05] steps. At the common 220-step follow-up horizon, EA-RG remained lower than MAPPO, whereas comparisons with HAPPO and a wider single-graph baseline were not directionally consistent. Component ablations provided limited support, and zero-shot shifts were shift-family dependent. Thus, the contribution is restricted to earlier task-chain recovery under the locked nominal condition, not universal baseline or out-of-distribution superiority.

## Keywords

| 中文 | English |
|---|---|
| 异构无人机 | heterogeneous unmanned aerial vehicles |
| 多智能体强化学习 | multi-agent reinforcement learning |
| 故障后恢复 | post-failure recovery |
| 任务图 | task graph |
| 多关系图注意力 | multi-relational graph attention |
| 受限通信 | constrained communication |
| 生存分析 | survival analysis |

## Bilingual figure and table titles

| 项目 | 中文题名 | English title |
|---|---|---|
| 图 1 | 故障后协同的三关系任务图 | Fig. 1 Three-relation task graph for post-failure coordination |
| 图 2 | 匹配失效暴露下的早期任务链恢复 | Fig. 2 Early task-chain recovery under matched failure exposure |
| 表 1 | 锁定 held-out 的主要结果 | Table 1 Primary results on the locked held-out evaluation |
| 表 2 | 受控组件消融 | Table 2 Controlled component ablation |
| 表 3 | 零样本 OOD 的必要边界 | Table 3 Required boundary from zero-shot OOD evaluation |

## English figure legends

**Fig. 1.** (a) Scout–Relay–Attack–Target heterogeneous task scenario and the three relations. (b) Three-relation task graphs before and after relay failure; the failure makes the corresponding relations unavailable, and the attack window is not a fourth relation. (c) Local observations and available graphs are processed by relation-specific edge-aware attention, Gate Prior, static Role-Pair modulation and union-graph residual fusion before decentralized actor execution. Blue dotted, green dashed and orange dash-dotted lines denote perception, environment-delivered communication and task support, respectively. Relation adjacency is an aggregation mask, not a learned physical communication switch.

**Fig. 2.** (a) Full Kaplan–Meier recovery curves for EA-RG, MAPPO, HAPPO and the wider single-graph baseline; the fine dashed line marks the end of the pre-specified active node-failure window at 80 steps. (b) Detail from 0 to 35 steps, where the primary separation occurs. (c) Seed-level RMST80 differences between EA-RG and MAPPO and the pooled hierarchical paired-bootstrap 95% interval; negative values indicate earlier recovery by EA-RG. Curves summarize three independent training seeds and 600 failure-exposed episodes per method; unrecovered episodes are right-censored.

## English table legends

**Table 1.** Recovery and Success are means ± sample standard deviations over three independent training seeds. Conditional mean recovery time is defined only for failure-exposed episodes that recovered and cannot replace RMST with right censoring. RMST80 is the pre-specified P1 comparison between EA-RG and MAPPO; other RMST80 values are reported in the Supplementary Information.

**Table 2.** Means ± sample standard deviations are based on three independent training seeds. Conditional time and RMST target different estimands; mechanism traces and seed-level details are reported in the Supplementary Information.

**Table 3.** Values are locked family-level summaries used only to describe shift dependence; they are not p values or evidence of universal generalization.
