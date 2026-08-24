# 论文初稿 v1.14 借鉴与迁移审计

参考材料：`D:\File\Downloads\论文初稿_v1.14_最终实验与投稿审计_20260820.pdf`。

本审计只借鉴参考稿的结构、证据组织和表述方式，不借用其数据、结论、任务定义或方法结果。你的稿件仍以 `PAPER_Q2_RESULT_PROVENANCE.md`、`PAPER_Q2_COMPLETE_ASSET_LEDGER.md` 和冻结的 DRTP claim boundary 为唯一证据来源。

## 参考稿中最值得保留的做法

| 借鉴点 | 参考稿的做法 | 在本稿中的落点 |
|---|---|---|
| 摘要结果化 | 任务、方法、主要数值、代价和边界在摘要内同时出现 | `paper/q2_draft/abstract.md`：增加绝对指标、seed sensitivity 和 scope boundary |
| 问题边界 | 明确“任务层规划”而非“飞控”，避免读者误解输出能力 | `03_problem_formulation.md`：增加 scope/term table |
| 证据链矩阵 | 数据集/任务/用途、方法/输入/公平性分开列 | `05_experimental_setup.md`：增加 contract matrix 和 baseline capability matrix |
| 指标可解释 | 主指标、辅助指标、指标方向和统计单位明确分层 | `05_experimental_setup.md`：增加 metric definition table |
| 结果梯度 | 先验证问题，再给主结果，再给消融、机制、效率和局限 | `06_results.md`、`07_discussion.md`：调整阅读顺序和结果边界 |
| 消融定位 | 明确哪些模块改善哪些指标，不宣称所有指标都提升 | `05_experimental_setup.md`、`06_results.md`：将 UTR vs DRTP 放在主文并保留反向 seed |
| 数据可用性 | 说明数据、代码、配置、许可和复现材料 | 新增 `09_data_code_availability.md` |

## 不直接照搬的部分

1. 参考稿的任务图规划指标和数据集不能作为 DRTP 的结果。
2. 参考稿的 holdout、样本数和显著性数值不能填入本稿。
3. 本稿不能把 DRTP 的历史 development 与 held-out 10M 证据合并为一个同质样本。
4. 本稿不把 UTR/DRTP 之外的历史非兼容方法表格包装成公平 comparator。
5. 本稿不把有利的 pooled mean 写成 seed-stable superiority；seed1902 和 held-out seed2002 必须保留。

## 本轮完善后的投稿级证据链

`冻结任务与信息边界 → 合同矩阵 → matched UTR ablation → 绝对性能 → paired seed effects → OOD 分解 → 安全与 exposure validity → 机制遥测 → 限制与数据可用性`

这条链条用于组织论文，不改变任何训练、checkpoint、评估 tape 或历史裁决。
