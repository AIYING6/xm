# Chinese Manuscript Blueprint (Initial)

## One-sentence argument

在严格间歇感知、受限通信和中继节点短时失效的三自由度异构无人机协同拦截任务中，基于任务图的多关系协同能够相较无图 MAPPO 更早恢复任务链；该优势在全时域仅具竞争性，并受分布变化限制。

## Narrative hierarchy

| Priority | Thread | Main-paper treatment |
|---|---|---|
| P1_CORE | Failure-aware task formulation plus early recovery advantage versus MAPPO | Abstract, Introduction, primary figure/table, Results core, Conclusion |
| P2_SUPPORTING | Multi-relation representation; Gate Prior stability; Task-Support empirical contribution | Method, concise ablation/mechanism evidence |
| P3_BOUNDARY | Full-horizon competitiveness and distribution-dependent OOD transfer | Discussion plus one compact OOD boundary element |
| P4_DIAGNOSTIC | Role-Pair non-benefit, detailed OOD cells/saturation, profiling, temporal cases, development history | Supplementary or one neutral disclosure only |

## Proposed Chinese article logic

1. 问题：失效后任务链恢复为何不同于终局成功率。
2. 方法：以感知、通信与任务支撑三类关系表达受限信息条件下的协同依赖。
3. 主证据：锁定 held-out 的 KM/RMST 结果，突出故障持续窗口内相对 MAPPO 的早期恢复。
4. 支撑证据：可靠性、受控图基线、关键消融与 Gate Prior 稳定性。
5. 必要边界：全时域竞争性及零样本 OOD 的分布依赖性。
6. 解释：方法改善的对象是 nominal 分布中的早期恢复时序，而非无条件泛化或全面性能最优。

## Terminology seed ledger

| Canonical Chinese term | First-use form | Do not use as interchangeable synonym |
|---|---|---|
| 边感知角色图 MAPPO | Edge-Aware Role-Graph MAPPO（EA-RG-MAPPO-S；short form EA-RG） | RI-GMAPPO as a paper method name |
| 任务链 | cooperative kill chain | 仅称“成功链” without definition |
| 故障后恢复 | post-failure recovery | completion time when recovery metric is intended |
| 受限平均生存时间 | restricted mean survival time（RMST） | recovered-only mean as a primary endpoint |
| 任务支撑关系 | Task-Support relation | independent communication channel |
| Gate Prior | 结构化门控初始化先验 | online failure gate |
