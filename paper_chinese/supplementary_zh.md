---
title: "补充材料：面向故障后任务链恢复的异构无人机多关系任务图协同决策"
language: zh-CN
status: evidence-led supplementary draft
---

# 补充材料

本补充材料承接主稿的可复算统计和边界信息。它不引入新的实验、训练或主张；各数值仅来自锁定资产。除非另有说明，均值 ± 标准差的独立单位为 3 个训练 seed。

## S1 故障后恢复事件与生存分析

恢复时钟以节点故障开始为零点。事件为首个稳定任务链窗口的起点；在可用随访结束前未恢复的 episode 被右删失。主生存分析只使用 Early 与 Nominal 场景，因此每个 method × seed 含 200 个 failure-exposed episodes，合计每方法 600 个。\(\tau=220\) 是共同完整随访上限，\(\tau=80\) 是预先指定的节点故障活动窗口。

**表 S1｜RMST220 的逐 seed 结果（步）。**

| 方法 | seed 0 | seed 1 | seed 2 | 均值 ± SD |
|---|---:|---:|---:|---:|
| EA-RG Full | 17.36 | 11.19 | 14.85 | \(14.47\pm3.10\) |
| w/o Gate Prior | 35.77 | 14.60 | 95.08 | \(48.48\pm41.72\) |
| w/o Task-Support | 20.90 | 57.04 | 10.79 | \(29.57\pm24.31\) |
| w/o Role-Pair | 11.49 | 18.09 | 11.33 | \(13.63\pm3.86\) |
| No Graph | 44.36 | 72.23 | 117.50 | \(78.03\pm36.91\) |
| Single Graph | 12.11 | 18.29 | 174.45 | \(68.28\pm91.99\) |
| 宽单图 | 26.37 | 10.32 | 12.80 | \(16.49\pm8.64\) |
| HAPPO | 12.72 | 12.19 | 17.52 | \(14.14\pm2.94\) |
| MAPPO | 18.58 | 28.86 | 13.74 | \(20.39\pm7.72\) |

**表 S2｜预设时间窗的 RMST 敏感性（3 个 seed 均值，步）。**

| \(\tau\) | EA-RG | MAPPO | HAPPO | 宽单图 |
|---:|---:|---:|---:|---:|
| 50 | 11.16 | 14.27 | 12.30 | 12.24 |
| 80 | 11.81 | 15.51 | 13.52 | 13.84 |
| 100 | 12.21 | 16.32 | 14.02 | 14.87 |
| 150 | 13.18 | 18.32 | 14.14 | 16.33 |
| 190 | 13.92 | 19.68 | 14.14 | 16.49 |
| 220 | 14.47 | 20.39 | 14.14 | 16.49 |

Full−MAPPO 在 \(\tau=50,80,100\) 的逐 seed 差异分别为 \((-3.09,-4.57,-1.66)\)、\((-2.64,-7.27,-1.21)\) 和 \((-2.42,-9.07,-0.84)\) 步，对应的分层配对 bootstrap 95% 区间为 [−4.71,−1.70]、[−7.16,−1.05] 和 [−8.84,−0.57]。这些预设窗口的 bootstrap 采用 10,000 次重采样：先抽取训练 seed，再在 seed × scenario 内重采样匹配 episode 索引（RNG 20260807）。

完整九方法 KM 曲线和每 seed 的 EA-RG/MAPPO KM 曲线使用 `docs/statistics/survival_results_v1_1/km_recovery_curve_primary.png` 与 `km_recovery_curve_primary_per_seed.png` 导出；主稿只显示按图表契约筛选的四方法曲线。

## S2 终局指标与组件比较

主稿表 1、表 2 中的 Recovery、Success 和条件平均 \(t_{rec}\) 来自锁定 held-out 的 3 seed 汇总。\(t_{rec}\) 只在 failure-exposed 且已恢复的 episode 中定义；它不替代包含右删失的 RMST。`Wilson95` 的计算与跨 seed 汇总定义尚未完整记录，因此不在主稿或本补充材料中报告。

组件结果的解释严格限于表观性能支持：Gate Prior 对应结构化初始化，Task-Support 对应任务相关关系，静态 Role-Pair 调制未显示稳定独立增益。本文不以这些消融结果宣称在线故障自适应、消息剪枝或已证实的故障后关系重组机制。

## S3 零样本分布变化的完整审计入口

零样本 OOD 使用冻结的 7-cell equal-weight Full−MAPPO RMST80 estimand，包含 8,400 个 episode（4 个方法 × 3 个训练 seed × 7 个 cell × 100 个 episode）。主稿报告 family-level 边界；以下锁定文件提供完整可审计输入和输出：

- `docs/statistics/p3a_ood_results_v1_1/p3a_ood_stats_lock_memo.md`：估计量、bootstrap 区间与家族级结论；
- `docs/statistics/p3a_ood_results_v1_1/p3a_ood_raw_results_audit.md`：输入完整性；
- `docs/statistics/p3a_ood_results_v1_1/p3a_ood_raw_results.csv`：逐 episode 的冻结结果；
- `docs/statistics/p3a_ood_results_v1_1/p3a_ood_sanity_audit_v1_0.md`：早期端点上限饱和的审计。

M1、M2 和 J1 的 RMST80 上限饱和意味着在该窗口内恢复事件近乎为零；该现象不能被解释为方法等价。P3-B 校准、oracle 和结构诊断属于后续研究准备工作，不是本论文的补充性科学结果。

## S4 邻近扰动与计算成本

全量 R00–R09 邻近通信/失效扰动的描述性结果位于 `docs/paper_assets_v1_5/canonical_results_v1_5.csv` 与 `docs/paper_assets_v1_5/table3_robustness.md`。它们基于多个条件的 3-seed 汇总，未形成预设多重比较推断，故不被解释为 OOD 泛化证明。

效率 profile 位于同一 canonical CSV 的 `table4_efficiency` 部分，当前记录为 \(n=1\)。在补齐硬件、预热、重复 block 与聚合协议前，只能将其作为单次成本披露，不进行方法间统计性速度比较。

## S5 图表、代码与数据溯源

主稿图 1 是代码事实示意图，主图发布包由 `scripts/render_publication_main_figures.py` 生成；事实来源为 `docs/figure_contracts/FACT_MANIFEST_METHOD_FIGURE.md`。主稿图 2 从冻结 held-out 输入只读重绘，并由同一发布脚本输出。两图的交付格式、输入/事实指纹和图元核验记录分别位于 `paper_chinese/figures/publication/`、`publication_figure_provenance.txt` 和 `docs/figure_redesign/PUBLICATION_FIGURE_EVIDENCE_AUDIT.md`。

脚本、配置、锁定结果和证据优先级的总入口为 `docs/PAPER_EVIDENCE_PACK.md`、`docs/EVIDENCE_STATUS_REGISTRY.csv` 与 `docs/NUMERIC_PROVENANCE_AUDIT.md`。正式投稿前，作者需按目标期刊政策提供数据与代码可用性声明。
