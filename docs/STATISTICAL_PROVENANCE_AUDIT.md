# 统计报告与主张溯源审计（P4，v1.6）

**审计范围：** `survival_protocol_v1_1.md`、`survival_results_v1_1/`、`P1B_DECISION_MEMO_V1_1.md`、P3-A OOD 统计锁、v1.5 canonical CSV，以及当前英文稿的结果/讨论/结论。
**不包含：** 原始结果重算、模型重新训练或论文正文改写。
**统计结论：** 现有设计可支持一个窄而清晰的 P1 主张——在 locked nominal held-out 的 matched exposure 下，EA-RG 相对 MAPPO 更早恢复；它不能支持 Full 对 HAPPO、wider single-graph 或所有方法的统一全时域优越，也不能支持普适 OOD 泛化。

## 1. 研究设计与独立单位

| 分析层 | estimand / endpoint | 独立实验单位 | episode 层级 | 可作推断的范围 |
|---|---|---|---|---|
| P1 primary survival | 每 seed 的 KM RMST(220)，Early+Nominal | 训练 seed（n=3） | 每 method×seed 有200 failure-exposed episodes；Early、Nominal 各100 | Full 与各 comparator 的 full-horizon recovery dynamics |
| P1 sensitivity | RMST(50/80/100/150/190/220) 的 Full−comparator paired difference | 训练 seed（n=3） | seed 后、episode 前的层级配对重采样；同 episode index 配对 | 预设时间尺度上的方向与不确定性；核心为 Full–MAPPO at τ=80 |
| terminal held-out | recovery、success、recovered-only `t_rec` 等 | 训练 seed（n=3） | 全 locked suite；每个方法 3×4×100=1,200 episode（全方法合计10,800） | 描述性可靠性与条件时间；不替代 RMST |
| P3-A OOD | 每 seed 7-cell equal-weight Full−MAPPO RMST80 | 训练 seed（n=3） | 每 method×seed×cell=100；4×3×7×100=8,400 rows | 零样本迁移的 aggregate 边界，不是 universal generalization test |
| robustness | recovery degradation from R00 | 训练 seed（n=3） | 多条件的 seed 内评估 | 描述性 supporting evidence；当前信息不足以作多比较统计结论 |
| efficiency | profile metrics | 未确认（canonical row `n=1`） | 未明确 | 描述性成本披露，非 inferential comparison |

## 2. 已核验的统计做法

- **时间零点与事件：** `t=0` 为 failure start；event time 为第一个稳定 task-chain window 的起点减 failure start；未恢复 episode 在可用 post-failure follow-up 处 right-censor。这避免把四步稳定窗口的确认末端误用为恢复时间。
- **primary population：** Delayed/Late 情形存在 pre-failure termination，且 exposure 依方法不同。主分析限定 Early+Nominal 的 54/54 method×seed×scenario cells，每 cell 100 exposed episodes，避免 landmark-selection bias。
- **RMST：** τ=220 是 primary populations 可共享的完整 follow-up；τ=80 是预设 sensitivity horizon，且有“失效节点活动时长=80”这一任务定义。
- **不确定性：** Full–comparator 采用 seed→episode-within-seed×scenario 的 10,000 次 hierarchical paired bootstrap，保留配对 episode index；RNG 是 20260807。
- **OOD：** primary aggregate、cell、τ、equal weights 与检验 checkpoint 均在结果后锁定；P3-A raw-results audit 确认 8,400/8,400 rows 唯一、完整、无 exposure violation。

这些做法与正确的层级相符：不能把同一个训练策略下的大量 episode 当成成千上万个独立策略训练重复。主要限制是 n_seed=3，故应强调 effect estimate、区间及 seed-direction，而不作强因果或 SOTA 式断言。

## 3. 主张—统计分析映射

| P层级 | 可用主张 | endpoint / comparison | 报告最小集 | 禁止升级为 |
|---|---|---|---|---|
| P1_CORE | Full 相对 MAPPO 在故障活动窗口更早恢复 | paired RMST80, Full−MAPPO | 11.81 vs 15.51；three seed deltas；95% CI [−7.16, −1.05]；n_seed=3 | “所有方法中最快”、“全时域最优”或已证明因果机制 |
| P1_CORE | Full 的全时域表现具竞争性 | RMST220, Full vs MAPPO/HAPPO/wider SG | Full 14.47±3.10；MAPPO 20.39±7.72；HAPPO 14.14±2.94；seed deltas 的 mixed status | 对 HAPPO/wider SG 统一优越 |
| P2_SUPPORTING | Gate Prior 与优化稳定性/跨 seed 一致性相关 | removal 的 RMST/reliability + 已另锁的轨迹资产 | 只在资产统计单位、曲线完整性经复核后使用机制数值 | “必要组件”、“在线故障响应”或饱和门控机制 |
| P2_SUPPORTING | Task-Support 有经验性性能支持 | Full vs w/o relation | Full 14.47±3.10 vs 29.57±24.31，且三 seed 并非全同向 | 已证明故障后关系重组 |
| P3_BOUNDARY | 零样本 OOD transfer 随 shift family 改变 | 7-cell equal-weight RMST80 Full−MAPPO | +2.565±5.567；CI [−2.362,+8.435]；三 seed mixed | “OOD 有效/无效”的普适结论或 p-value claim |
| P4_DIAGNOSTIC | Role-Pair 独立收益有限 | Full vs w/o RPG | 14.47±3.10 vs 13.63±3.86；mixed deltas | role-pair 为核心验证创新，或“速度–可靠性 trade-off”机制 |

## 4. 稿件报告问题与修复优先级

### P0 — 投稿前必须修复

1. **OID aggregate 被误表述为“not significantly different from zero”。**
   - 位置：`paper_latex_3d_en/sections/05_experiments.tex` 的 RQ7。
   - 证据：P3-A 给出 hierarchical bootstrap CI 与 `P(Delta<0)=0.1749`，没有报告 frequentist test/p-value。
   - 修复：改为“aggregate 的 bootstrap 95% CI 跨0，三个训练 seed 的方向不一致”。若保留 `0.1749`，完整写作“bootstrap estimate of P(Delta<0)=0.1749”。

2. **主表没有在列头声明 recovered-only 的选择条件。**
   - 位置：`tables/table1_held_out.tex` 的 `t_rec`。
   - 风险：读者可能将 10.8 与 RMST 混作同一 estimand，或将只在恢复者中定义的条件时间用作完整恢复速度比较。
   - 修复：列头/表注写“条件平均恢复时间（仅 failure-exposed 且 recovered 的 episode）”；结果首次出现时说明 RMST 是主要时间端点。

3. **Gate Prior 图与其定量机制叙事尚无可提交的图形证据。**
   - 位置：RQ6、Discussion、Conclusion，以及 `PAPER_ASSET_SPEC.md`。
   - 证据：资产规格说明当前图缺少 Full-with-prior curve；0.962/0.562、AUC、首次达到阈值等数值不在本轮确认的 canonical/survival 数字源中。
   - 修复：在完整曲线、原始数据、n 定义、汇总规则与生成脚本被单独审计前，不将这些数字放入主文；可先保留不带数字的受限文字，或移至待验证状态。

### P1 — 强烈建议修复

1. **RMST 主表的精度信息不足。** 当前 `table2_rmst.tex` 只列均值，不能让读者判断 n=3 的不确定性。
   - 修复：主表至少写 `mean ± sample SD over training seeds (n=3)`；核心 Full–MAPPO RMST80 在表注/正文配套给出 per-seed deltas 与 bootstrap CI；全 comparison matrix 转 Supplementary。

2. **`Wilson95` 的定义不可复现。** canonical CSV 只有 `wilson` 数值，当前表题称 95% lower bound，但没有交代是每 seed Wilson lower bound、怎样跨 seed 汇总、其推断对象是什么。
   - 修复：删除主文列，或补齐公式、输入分母、seed 汇总方式与用途。它不应与 seed-level SD 混为同一 uncertainty statement。

3. **条件均值语言仍过强。** `lowest conditional recovery latency among all methods`虽是数值正确的描述，但不能引出“整体恢复更快”。
   - 修复：首次出现即限定为 recovered-only descriptive statistic，并在紧随句转到 KM/RMST。

4. **“reliability--recovery-speed trade-off improves”不受终局可靠性排序支持。** Full 的终局 recovery 低于 HAPPO、wider single-graph 与 w/o RPG。
   - 修复：使用“相对 MAPPO 的 early recovery timing advantage”；将终局 reliability 写为“near-saturated but not highest”。

5. **OOD 的 P3 boundary 在结果、讨论、结论三次详细复述。**
   - 修复：正文仅一次给 aggregate 与一行 family conclusion；其他位置各一短句交叉引用。所有 per-cell 例外、ceiling 细节、审计过程和“未重调参”规则放 Supplementary / methods。

### P2 — 清晰度与材料路由

1. robustness table 有 9 个条件、7 个方法，报告的是 n=3 means；没有区间、multiplicity family 或 prespecified inferential comparison。主文不应对其中 R02/R04/R09 作显著性或可靠机制断言。
2. efficiency table 的 canonical rows 标记 `n=1`，但叙事称 locked profiling。需要 `AUTHOR_INPUT_NEEDED`：硬件、计时 warm-up、重复 block 数、block 聚合方式、是否同一运行环境。否则只将其作为单次 profile 披露，移补充材料。
3. 当前表/正文多次重复 10,800、8,400、RNG、protocol lock 等审计信息。主文保留必要的 n、split 和 endpoint；其余置于方法/补充材料。

## 5. 供后续中文稿使用的统计报告契约

以下是**仅在所列事实已被本审计确认时**可用的中文模板，不替代完整统计方法。

> 除特别说明外，结果以 3 个独立训练 seed 的均值 ± 样本标准差表示；episode 为同一训练 seed 下的评估样本，而非独立训练重复。故障后恢复时间以故障开始为零点，在首个稳定任务链窗口起点计为事件；未在可观测随访内恢复的 episode 按其可用随访时间右删失。主生存分析限于 Early 和 Nominal 场景，每个 method×seed×scenario cell 含 100 个 failure-exposed episodes。以 Kaplan–Meier 估计恢复曲线，并按每个 seed 计算 RMST；τ=220 为共同完整随访上限，τ=80 为预设的故障持续窗口。Full 与 comparator 的不确定性由 hierarchical paired bootstrap 获得（10,000 次重采样；先重采样训练 seed，再在 seed×scenario 内对匹配 episode index 重采样；RNG 20260807）。

> 在 τ=80 的预设窗口，EA-RG 的 RMST 为 11.81 steps，MAPPO 为 15.51 steps；三个训练 seed 的 Full−MAPPO 差异分别为 −2.64、−7.27 和 −1.21 steps，hierarchical paired bootstrap 95% CI 为 [−7.16, −1.05]。在 τ=220，EA-RG 的 RMST 为 14.47 ± 3.10 steps；该全时域结果相对 MAPPO 较低，但与 HAPPO 和 wider single-graph 的比较不呈现统一 seed 方向。

## 6. AUTHOR_INPUT_NEEDED

- Gate Prior trajectory analysis：原始数据路径、每条曲线的独立单位、seed 数、相关系数/AUC 的计算定义、是否含 Full-with-prior curve、以及图形生成脚本。
- Efficiency profiling：硬件/软件版本、预热与计时协议、每方法的可重复 block 数、canonical 中 `n=1` 与“5 blocks”描述的关系。
- Held-out `Wilson95`：分母、Wilson 公式、每 seed 还是 pooled episode 计算、以及跨 seed 汇总规则。
- 若目标期刊要求 p-values/multiple-comparison correction：由作者指定该期刊政策；当前锁定分析的正式输出是 effect estimates、bootstrap intervals 和 seed consistency，不应追补未预设的检验。

## 7. Reviewer-facing residual risk

- n_seed=3 使效应方向可审计，但限制了细小差异的精度；应避免“显著优于所有基线”或强因果语言。
- RMST sensitivity 含多个预设 τ；主文应聚焦有任务解释的 τ=80，而不是挑选最有利的 horizon。
- 同时呈现 terminal recovery、recovered-only `t_rec` 与 RMST 时，必须注明不同 estimand，否则审稿人会质疑 selection/censoring handling。
- OOD aggregate 含 ceiling-saturated cells。它们可用于说明边界，但不应被解释为方法等价；同样不应从单一 aggregate 延伸到全部未知 shift。
