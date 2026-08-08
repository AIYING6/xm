# 中文主稿预审（P7）

## Review setup

- **Input scope：** `paper_chinese/manuscript_zh.md`、两张重绘主图、P1/P3 锁定统计、方法图事实清单及已核验文献台账。
- **Assessment boundary：** 本预审不审计原始训练代码的数值重算，也不评价尚未指定的目标期刊政策。
- **Shared manuscript claim：** 在锁定 nominal held-out 的 matched failure exposure 下，EA-RG 相对 MAPPO 有可复现的早期故障后恢复优势；全时域与 OOD 结论均受限。
- **Visible evidence：** 三个独立训练 seed、KM/RMST、受控消融、family-level OOD 边界、三关系代码追溯与已验证背景文献。
- **Missing materials affecting confidence：** 最终补充材料、数据/代码可用性声明、作者元数据、目标期刊要求，以及可提交的 Gate Prior 双组轨迹资产。

## Reviewer 1 — 证据链与统计表述

- **Overall assessment：** 主结果已从终局成功率转为与问题匹配的恢复时序，统计单位和右删失边界也比旧稿清楚。
- **Who would be interested：** 多智能体控制、无人机协同和可靠性评估读者会关注把故障恢复作为事件时间终点的做法。
- **Major strengths：** RMST80 的任务解释明确；Full–MAPPO 的三 seed 同方向与 bootstrap 区间被完整报告；全时域不把 HAPPO 写成被全面超越。

### R1-M1：主要统计证据需要与补充材料形成可复算闭环（major）

- **Axis：** reproducibility / statistical-rigor
- **Claim pointer：** “EA-RG 相对 MAPPO 在故障活动窗口内更早恢复。”
- **Evidence pointer：** 主稿第 2.2、4.1 与 5.1 节；`docs/statistics/survival_results_v1_1/`。
- **Concern：** 主稿已给出 estimand、seed 数和区间，但投稿包尚未包含逐 seed RMST、KM 输入数据字典和完整 bootstrap 输出的 Supplementary 索引。
- **Resolution test：** 提供 Supplementary 表：每 seed 的 RMST50/80/100/220、每 method×seed 的暴露数、右删失定义及 `hierarchical_bootstrap.csv` 的可追溯链接；保持主结论不变。

### R1-m2：条件 \(t_{rec}\) 的选择条件需在最终排版中始终可见（minor）

- **Axis：** figures-and-tables / writing-clarity
- **Claim pointer：** 表 1、表 2 中的条件平均 \(t_{rec}\)。
- **Evidence pointer：** 主稿第 4.1 节、表 1 注、表 2 注。
- **Concern：** 当前文字已限定 recovered 且 exposed，但 Word/LaTeX 转排时容易被缩为 “recovery time”。
- **Resolution test：** 保留现有完整列名与表注；在最终模板中禁止把该列改为无条件的“恢复时间”。

## Reviewer 2 — 方法定位与机制证据

- **Overall assessment：** 方法描述与代码事实匹配，特别是明确了三关系、环境通信和静态 Role-Pair 的边界。
- **Who would be interested：** 图 MARL 及通信受限协同决策研究者会关注任务支撑关系与恢复端点的组合。
- **Major strengths：** 主稿不再把 attack window 画成第四关系，也不把 Gate Prior 写成在线故障响应；Role-Pair 的中性结果被一次性、如实披露。

### R2-M1：组件结果支持“设计贡献”，尚不足以支持更强机制因果（major）

- **Axis：** mechanism-evidence / causal-vs-correlative
- **Claim pointer：** Gate Prior 与 Task-Support 对整体设计的支撑。
- **Evidence pointer：** 主稿第 3.2 节、5.2 节与表 2；`docs/STATISTICAL_PROVENANCE_AUDIT.md`。
- **Concern：** 移除组件后的均值变化较大，但 seed 异质性也较大；当前没有可用的双组 Gate Prior 轨迹图来支撑优化过程层面的机制数字。
- **Resolution test：** 保持“受限的支持性/经验性证据”措辞；不要把轨迹相关、AUC 或故障自适应机制写入主文。若提交轨迹，先按图契约重绘和审计。

### R2-m2：最近工作差异应在最终格式中保留具体任务与终点的比较（minor）

- **Axis：** novelty-significance
- **Claim pointer：** 本文相对图式空战决策和通信 MARL 的定位。
- **Evidence pointer：** 主稿第 1 节；`docs/literature/CLOSEST_WORK_MATRIX.md`。
- **Concern：** 当前引言的弱表述是合格的，但目标期刊版需在 related work 中把 Ou、Huo 与本文在任务、故障条件和评价终点上的差异做成简短、可核验的对照。
- **Resolution test：** 使用已核验矩阵补一段具体比较，不使用“首次”或“所有既有工作只看成功率”等绝对表述。

## Reviewer 3 — 工程适用范围与呈现

- **Overall assessment：** 本稿在模拟范围内有清晰的工程问题和克制的结论，但其外部适用性仍是投稿层面的主要风险。
- **Who would be interested：** 面向失效恢复的无人机协同、鲁棒控制与仿真评估读者会对该受控证据链感兴趣。
- **Major strengths：** OOD 被作为边界而非亮点；方法图和主 KM 图各只回答一个问题，避免了旧稿的拥挤和矛盾。

### R3-M1：工程结论必须保持为受控 3DOF 模拟结论（major）

- **Axis：** experimental-design / claim-moderation
- **Claim pointer：** EA-RG 对故障后协同恢复的工程意义。
- **Evidence pointer：** 主稿第 2.1、6 与 7 节；`docs/EVIDENCE_STATUS_REGISTRY.csv` 的工程边界。
- **Concern：** 未提供 6DOF/JSBSim、真实传感器或物理通信验证；零样本 OOD 也显示通信拓扑和机动变化下的迁移不稳定。
- **Resolution test：** 保留现有“受控模拟证据”限定；选择匹配仿真与多智能体控制范围的期刊，不使用部署、实装、普适鲁棒或可扩展性主张。

### R3-m2：补充材料需承接 OOD 和成本细节（minor）

- **Axis：** figures-and-tables / reproducibility
- **Claim pointer：** OOD 的 family-level 边界和计算代价。
- **Evidence pointer：** 主稿第 5.3 节、表 3；`docs/FIGURE_EVIDENCE_AUDIT.md`。
- **Concern：** 主文已恰当地压缩 OOD，但读者仍需要逐单元、饱和解释及单次 profile 的硬件/重复协议来审计边界。
- **Resolution test：** 将七单元 OOD、saturation audit 和 profiling 协议放进 Supplementary；profile 未补齐前，不把 `n=1` 成本作比较性性能结论。

## Cross-review synthesis

- **Consensus strengths：** 三位审稿视角都认为主张—统计对象—图表的对齐显著优于旧稿；核心命题已被收窄到可由锁定证据支持的 Full–MAPPO 早期恢复比较。
- **Consensus technical risks：** （1）补充材料需要让 RMST/KM 与 bootstrap 完整可复算；（2）Gate Prior/Task-Support 只能保留受限机制解释；（3）工程外推应严格限于 3DOF 受控模拟。
- **Where emphasis differs：** Reviewer 1 注重统计对象和表格用语，Reviewer 2 注重方法与新颖性边界，Reviewer 3 注重工程验证与读者预期。
- **Broad-interest / significance readout：** 当前贡献对多智能体控制与无人机协同的专门读者具有明确价值；现有证据不支持将其包装为跨学科或通用自主系统层面的广泛突破。
- **Most important issues before submission：** 完成补充材料索引与可用性声明；保持所有机制和工程措辞的上限；在目标期刊模板内完成最近工作对照与统计表注。

## Risk / unsupported claims

- 不能声称图 MARL、学习通信或图空战决策的首次性。
- 不能声称 Gate Prior 是在线故障适应、通信剪枝或必要组件。
- 不能将 Role-Pair 调制表述为已验证的独立创新增益。
- 不能把 OOD bootstrap 结果写为 p 值、普适泛化成功或普适失败。
- 不能把条件 \(t_{rec}\) 当作完整恢复分布的主要时间结论。
- 不能从 3DOF 仿真推出实装、6DOF 或真实传感器/通信性能。
