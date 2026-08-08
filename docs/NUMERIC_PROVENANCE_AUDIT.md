# 数字溯源审计（P4，v1.6）

**审计日期：** 2026-08-08
**范围：** 当前英文证据稿 `paper_latex_3d_en/` 的主张、表格与图注；不重算、不改写任何原始结果。
**结论：** 当前论文只能使用 v1.6 生存分析锁、v1.5 canonical CSV 与 P3-A OOD 锁中彼此不冲突的数字。训练 seed 是独立统计单位；episode 仅是 seed 内评估样本。

## 1. 来源优先级与使用规则

| 优先级 | 证据源 | 可用于 | 不可用于 |
|---|---|---|---|
| A | `docs/statistics/P1B_DECISION_MEMO_V1_1.md`、`docs/statistics/survival_results_v1_1/`、`docs/statistics/survival_protocol_v1_1.md` | P1 的 KM、RMST(220)、RMST80、早期窗口 bootstrap、统计单位与删失定义 | 用 recovered-only 均值代替主要恢复速度证据 |
| A | `docs/statistics/p3a_ood_results_v1_1/p3a_ood_stats_lock_memo.md` 与 raw-results audit | P3-A 的 7-cell OOD aggregate、CI、family 边界与 episode 数 | 将 bootstrap 概率称为 frequentist p 值；将 OOD 说成普适泛化 |
| B | `docs/paper_assets_v1_5/canonical_results_v1_5.csv` | held-out 终局可靠性、recovered-only 条件均值、组件消融、稳健性、效率描述 | 覆盖 v1.6 中对恢复时间的 KM/RMST 判定 |
| C | `docs/P0_PROVENANCE_LOCK_V1_5.md`、`docs/P0_PROVENANCE_LOCK_V1_6_PROPOSED.md`、`docs/SCIENTIFIC_CLAIM_STATE_LEDGER.md` | 锁版本、方法标签与允许叙事 | 作为原始数字的替代来源 |
| 禁用 | `docs/gate1_safety_fx60_manuscript_consistency_audit.md` 及其固定更新五 seed 数字；2D 结果；P3-B 校准/Oracle 结果 | 历史记录或后续课题 | 当前中文主稿的数字、表格或核心结论 |

`canonical_results_v1_5.csv` 是 v1.5 终局指标的单一数字源；对故障后时间分布，v1.6 生存分析结果覆盖其 `t_rec` 解释。若两个来源的叙事冲突，采用 A 级来源。

## 2. P1：允许进入主文的核心数字

| 论断/数字 | 可报告数值 | 精确来源 | 独立单位与样本结构 | 允许表述 |
|---|---:|---|---|---|
| matched-exposure primary population | 每方法/seed 200 个 exposed episodes | `survival_protocol_v1_1.md` §1、`rmst_seedwise.csv` | 3 个独立训练 seed；每 seed 为 Early+Nominal 各100，合计200 | “主生存分析限于暴露构成完全匹配的 Early 与 Nominal 场景。” |
| Full 对 MAPPO 的 early recovery | RMST80：11.81 vs 15.51 steps | `survival_results_v1_1/sensitivity_rmst.csv` | n_seed=3；每 seed 内按 episode 与 scenario 配对 | “在故障仍持续的 80-step 窗口，Full 的 RMST80 低于 MAPPO。” |
| early-window consistency | Full−MAPPO（seed 0/1/2）= −2.64/−7.27/−1.21；95% bootstrap CI [−7.16, −1.05] | `P1B_DECISION_MEMO_V1_1.md` §4；`hierarchical_bootstrap.csv` 仅作 CI 交叉核对 | 10,000 次 hierarchical paired bootstrap；RNG 20260807 | “三颗训练 seed 的差异方向一致；该预设窗口的 bootstrap 区间不含0。” |
| Full primary RMST | 14.47 ± 3.10 steps | `rmst_summary.csv` | 三个 seed 的均值±样本 SD；每 seed 200 exposed episodes | “RMST(220) 为 14.47 ± 3.10 steps（mean ± sample SD over seeds）。” |
| Full vs MAPPO full horizon | MAPPO 20.39 ± 7.72；Full−MAPPO seed delta −1.22/−17.67/+1.12；CI [−17.03, +2.15] | `rmst_summary.csv`、`hierarchical_bootstrap.csv` | 同上 | “平均值更低，但 full-horizon 区间跨0、seed 差异并非同向。” |
| Full vs HAPPO full horizon | HAPPO 14.14 ± 2.94；Full−HAPPO +4.64/−1.00/−2.67 | 同上 | 同上 | “与 HAPPO 在全时域表现接近，不构成统一优越。” |
| Full vs wider single graph | 16.49 ± 8.64；Full−baseline −9.01/+0.87/+2.06 | 同上 | 同上 | “平均 RMST 较低但三 seed 不一致；不作稳定优越结论。” |
| held-out terminal recovery | Full 0.970569 ± 0.021256 | `canonical_results_v1_5.csv`, `table1_held_out` | 三 seed 均值±sample SD；全 held-out suite | “终局 recovery 为 0.971 ± 0.021（描述性终局指标）。” |
| recovered-only latency | Full 10.817259 ± 0.589251 steps | 同上 | 仅 failure-exposed 且恢复的 episode；seed 均值±sample SD | 只能称“已恢复 failure-exposed episodes 的条件平均恢复时间”；不可作主要时间端点或与 HAPPO 计算 headline 百分比。 |

### 组件数字（P2 supporting，不能升级为必要性或机制证明）

| 组件 | 可报告数值 | 来源 | 受限解释 |
|---|---:|---|---|
| Gate Prior 移除 | RMST220：48.48 ± 41.72；Full−w/o prior：−18.41/−3.41/−80.23 | `rmst_summary.csv`、P1B §6 | 平均损失大但 seed 异质性大；支持“在该架构内改善优化稳定性/一致性”，不支持“必要模块”或在线故障响应。 |
| Task-Support 移除 | RMST220：29.57 ± 24.31；Full−w/o relation：−3.54/−45.85/+4.07；终局 recovery 0.892 ± 0.160 | 同上及 canonical `table1_held_out` | 经验性支持；不声称已证明故障后关系重组机制。 |
| Role-Pair Modulation 移除 | RMST220：13.63 ± 3.86；Full−w/o RPG：+5.88/−6.90/+3.53；终局 recovery 0.990 ± 0.005 | 同上 | 独立收益有限且全时域不稳定；只作一次中性披露或补充材料。 |

## 3. P3：允许进入主文的 OOD 边界数字

| 论断/数字 | 可报告数值 | 精确来源 | 单位与样本结构 | 允许表述 |
|---|---:|---|---|---|
| 数据完整性 | 8,400 rows；84 method×seed×cell blocks；每 cell 100 episodes | `p3a_ood_raw_results_audit.md` | 4 methods×3 seeds×7 cells×100 episodes | “零样本评估包含 8,400 episodes。” |
| 主要 estimand | 7-cell equal-weight Full−MAPPO RMST80 aggregate | `p3a_ood_stats_lock_memo.md` §2 | 先按每 seed 等权平均7 cells，再在3 seed 间平均 | 必须完整定义等权 aggregate；不得挑选 family/cell 后重算 headline。 |
| aggregate | +2.565 ± 5.567 steps | 同上 | n_seed=3 | “aggregate 的方向不一致，平均差为 +2.565 ± 5.567 steps。” |
| uncertainty | bootstrap mean +2.532；95% CI [−2.362, +8.435]；P(Δ<0)=0.1749 | 同上 §4 | 10,000 hierarchical paired bootstrap；RNG 20260807 | “bootstrap 95% CI 跨0，bootstrap estimate of P(Δ<0)=0.1749。”不能写“p=0.175”或“not significant”。 |
| family decomposition | Geometry −1.08；Communication +10.06；Maneuver 0；Joint 0 | 同上 §4 | 仅解释性 family 汇总 | “几何变化保留部分优势；通信拓扑变化可反转比较；机动/联合场景在 RMST80 发生 ceiling saturation。” |
| saturation | M1/M2/J1 的 RMST80=80 主要因 window 内 recovery event 近乎0 | 同上 §6 | 非“方法相等”证据 | “在该早期端点上各方法均近乎无法恢复”；详细例外、per-cell 值放补充材料。 |

## 4. 已发现的冲突、过期项与数字使用风险

| 级别 | 位置 | 问题 | 处理要求 |
|---|---|---|---|
| P0 | `docs/gate1_safety_fx60_manuscript_consistency_audit.md` | 写有固定 update-60、五 seed、88.6% 等旧主线；与当前三 seed v1.6 生存锁冲突。 | 标记为历史；不得被中文稿、图表或自动生成脚本引用。 |
| P1 | `paper_latex_3d_en/sections/05_experiments.tex` RQ7 | “aggregate is not significantly different from zero”将 bootstrap CI/probability误写成显著性检验结论。 | 改为“区间跨0且 seed 方向不一致”；如保留概率，明确为 bootstrap 估计概率。 |
| P1 | `paper_latex_3d_en/tables/table1_held_out.tex` 与正文 | `t_rec` 列虽在正文定义为 recovered-only，但表题/列头未直接说明条件集合；容易与 RMST 混淆。 | 中文主表写全“条件平均恢复时间（仅已恢复且暴露 episode）”，或移至补充材料；P1 时间主证据只用 KM/RMST。 |
| P1 | `table1_held_out.tex` 的 `Wilson95` | 未给出每 seed Wilson lower bound 的计算/聚合定义；不能仅据表题推断。 | 除非补充计算定义、单位与用途，否则中文主文删除该列。 |
| P1 | `table2_rmst.tex` | 只列均值，虽 caption 说 3 seeds，却没有 SD、per-seed difference、CI 或 source-data 指向。 | 主表应保留 n=3、mean±SD，正文对 Full–MAPPO 给出预设 τ=80 的 three deltas 与 CI；其他精细差异转补充。 |
| P1 | `section 05`, RQ1 | “lowest conditional recovery latency among all methods”是 recovered-only selection 后的描述，易被误读为完整速度比较。 | 保留“描述性、条件均值”，同句转向 RMST；不能作算法全面更快的证据。 |
| P1 | `section 06` 首句 | “improves reliability--recovery-speed trade-off”暗示 trade-off 被统一改善，但 Full 的 terminal recovery 低于 HAPPO/wider/RPG ablation。 | 改为“相对 MAPPO 改善早期恢复时序；终局可靠性与全时域恢复具竞争性”。 |
| P1 | `section 05` RQ6、`section 06` | Gate correlation 0.962 vs 0.562、AUC 等机制数值没有在本审计所检查的 canonical CSV/生存锁内出现，且图已被 `PAPER_ASSET_SPEC.md` 标为 Full curve 缺失。 | 禁止作为主文定量证据，直到单独的机制资产、统计单位和图形修复得到审计确认。 |
| P2 | `table3_robustness.tex` / RQ4 | 十个条件、多个方法、每项 n=3；无 interval、comparison-family 或 multiplicity说明。 | 转 Supplementary；仅作描述性 robustness map，不作为 Role-Pair 机制的显著性证据。 |
| P2 | `table4_efficiency.tex` / RQ5 | canonical CSV 将每项标为 n=1 profile；历史锁描述“5 methods×5 blocks”与表中 n=1 不足以判定可重复层级。 | 只报告 profiling description，并说明硬件、计时协议、block 聚合与是否可重复；不作统计优越性比较。 |
| P2 | OOD table / RQ7 / Discussion / Conclusion | 详细 cell、exception、RNG、Gate C 与不重调参规则在三处反复出现，负结果占比过高。 | 正文只保留 aggregate + 一句 family boundary；per-cell、saturation、audit移至 Supplementary，删除“Gate C”术语。 |
| P2 | `survival_results_v1_1/hierarchical_bootstrap.csv` 的 `observed_delta` | 脚本在各 \(\tau\) 行复用了 RMST220 的 observed point estimate；早期 CI 计算仍在对应 \(\tau\) 内执行，但该字段本身不能代表 RMST80 点估计。 | 不改写已锁定主结果；中文稿的 RMST80 点估计和 per-seed 差异只引用 `sensitivity_rmst.csv` 与 P1B memo。后续重新发布 Supplementary 数表前，修复并单独复核该字段。 |

## 5. 数字写作底线

1. `±` 若未另行注明，一律为 **训练 seed 间 sample SD**，不是 episode-level SEM、CI 或 bootstrap SD。
2. `n=3` 必须在首次主结果表/统计方法中定义为 **independent training seeds**；episode 是 seed 内评估样本，不可报为 10,800 个独立实验重复。
3. RMST 的“更低”表示到恢复事件的受限平均等待时间更短；它整合了 right-censoring，不能与 `t_rec` 互换。
4. Early+Nominal 之外的 Delayed/Late 具有 method-dependent exposure，不能并入 primary survival estimand。
5. 所有 bootstrap 结果应写明 paired hierarchy、B=10,000、RNG=20260807、估计量和 CI；`P(Δ<0)`是 bootstrap directional probability，不自动等同于 p 值。
6. 不能创造百分比速度提升、显著性、effect size、power 或多重比较校正结论。缺少的信息以 `AUTHOR_INPUT_NEEDED` 标记。
