# 图表—证据审计（P5）

**审计目标**：将当前英文稿图表按 P1_CORE / P2_SUPPORTING / P3_BOUNDARY / P4_DIAGNOSTIC 分流，核验图示事实与代码/锁定结果的一致性。本审计不重绘、删除或修改现有资产。

## 一页结论

主文应由一个问题图、一个修复后的三关系方法图、一个精简的早期恢复主证据，以及受控的核心表格组成。当前 KM 图信息密度过高但数据有效；Gate Prior 图当前失效；鲁棒性图和细粒度 OOD 表格不应让边界/诊断内容压过 P1 主证据。

## 资产清单与裁决

| 当前资产 | 证据层 | 结论职能 | 审计裁决 | 主文/补充材料 | 主要风险与操作 |
|---|---|---|---|---|---|
| `intercept_3d_task_scene.png` | P1_CORE | 定义异构 3DOF 任务、角色和信息链 | 可用，需最终图注明确是示意 | 主文 Fig. 1a | 图例“sensing/task support”混合两种概念，最终版本宜拆开或弱化为任务链说明 |
| `intercept_3d_multi_relation_graph.png` | P2_SUPPORTING | 解释图编码结构 | **不可用** | 修复后主文 Fig. 1b | 标题称三关系，图例却画了第 4 个“attack-window relation”；与代码硬冲突 |
| `km_recovery_curve_primary.png/.pdf` | P1_CORE | 展示 matched exposure 下的恢复时间分布 | 数据可用，需精简 | 主文 Fig. 2 | 九方法曲线/图例拥挤；保留 Full、MAPPO、HAPPO、wider single-graph，完整九方法曲线移补充材料 |
| `table1_held_out.tex` | P1_CORE | 总体 held-out 可靠性与条件性时间描述 | 可用，需压缩数位并标清 seed 单位 | 主文 | 不得把条件性 `t_rec` 当成完整分布恢复时间 |
| `table2_rmst.tex` | P1_CORE | 报告预设 RMST 时间窗 | 可用 | 主文 | 用 RMST80 作为早期主锚，RMST220 作为竞争性完整随访上下文 |
| `table2_ablation.tex` | P2_SUPPORTING | Gate Prior / Task-Support / Role-Pair 的组件证据 | 可用但叙事需收束 | 主文紧凑表 | Role-Pair 为有限独立收益，不能与 Full 并列包装为核心创新 |
| `fig_gate_evolution.png/.pdf` | P2_SUPPORTING | Gate Prior 的初始化和跨 seed 稳定性 | **当前不可用** | 修复后主文小图或补充材料 | 目视检查显示仅有 w/o Gate Prior 的 0.5 曲线；Full 曲线缺失，caption 不成立 |
| `fig_cross_seed_dispersion.png` / `fig_success_curves.png` | P2_SUPPORTING | 支撑 Gate Prior 稳定性 | 候选支持证据 | 补充材料；如重构双曲线可配合主文 | 需使用锁定机制轨迹，明确是优化一致性而非运行时机制 |
| `fig_robustness_degradation.png` + `table3_robustness.tex` | P2_SUPPORTING | 训练分布邻近扰动下的表现 | 有效但非主结论 | 补充材料默认；主文一段中性概述 | 9 条曲线、R01–R09 代码命名、空缺 exposure 容易造成实验报告感；不能替代 OOD |
| `table4_efficiency.tex` | P4_DIAGNOSTIC | 披露推理/训练成本 | 可用 | 补充材料或 Methods 一句 | profile 为 n=1，不应列为论文贡献 |
| `table5_ood.tex` | P3_BOUNDARY | 简洁限定零样本迁移范围 | 事实可用，呈现需压缩 | 主文一张紧凑边界表；完整 cell 移补充材料 | 现表及正文细节过多，M/J 饱和不能压过 P1；移除内部 “Gate C” 命名 |
| Task-Support windows/cases | P4_DIAGNOSTIC | 解释为何不主张故障后重组机制 | 可用 | 补充材料 | 一次性中性披露，不作为主要机制图 |
| Pareto 成功率/恢复率图 | P4_DIAGNOSTIC | 展示终局 trade-off | 事实可用但非必要 | 补充材料 | Full 不全面领先；若没有独特论点则不进入主文 |
| 旧 `method_overview_ea_rg_mappo_s.png` | 历史 | 旧 2D/随机半径叙事 | 禁用 | 不纳入 | 代码脚本/标题不属于当前锁定 3DOF v1.6 主线 |

## 硬阻塞

### 1. 三关系—四关系图示冲突

代码常量固定 `RELATION3D_COUNT = 3`，编号为感知、通信和任务支撑。现有图在正确标题下额外标出粉色“Attack-window relation”。攻击窗口在环境中是 node feature，并可触发 Task-Support，但不构成第四邻接切片。这一错误会误导读者对模型容量和创新点的理解。

**解除条件**：重绘为只有三种关系；把攻击窗口表示为 attacker 节点内部状态/Task-Support 激活条件，而非边型；图中注明联合图残差路径和静态角色对调制均不是额外 relation channel。

### 2. Gate Prior 图缺少 Full 曲线

当前图只有橙色 `w/o Gate Prior`，在约 0.5 处平直；没有图例所需的 Full 蓝色轨迹。故无法证明“with and without”、初始结构差异或跨 seed 保持性。

**解除条件**：从锁定 `gate_prior_v1_5_assets` 数据重渲染 Full 与 w/o 的均值及 SD，或将该图暂时撤出主文，仅用经过锁定表格支持的谨慎文字表述；不得手动补线。

## 图表逻辑建议

### 主文最小证据链

1. **Fig. 1（P1+P2）**：任务/信息边界示意 + 修复的三关系图。它回答“问题是什么、方法如何编码已观测信息”。
2. **Fig. 2（P1）**：精简 KM（Full、MAPPO、HAPPO、wider SG）并在图注或相邻表内提供 RMST80、RMST220 与 `n=3`。它回答“核心早期恢复结论是否成立”。
3. **Table 1（P1）**：held-out 与 RMST 的紧凑合并表，避免重复堆表。
4. **Table 2（P2）**：Gate Prior、Task-Support 与 Role-Pair 的紧凑消融，最后一项明确为辅助组件的限制。
5. **Table 3（P3）**：一张简洁 OOD family 级边界表；细粒度 seed × cell 置补充材料。

### 补充材料

- 完整 KM（九方法）、RMST seedwise、bootstrap 和 survival audit。
- 全部 R00–R09 鲁棒性曲线/表、全部 OOD cell 和 feasibility/audit。
- Gate Prior 的完整可重现轨迹、cross-seed dispersion、Task-Support 时序 case。
- 效率、Pareto、模型参数、训练曲线与旧/发展期资产清单。

## 图注与视觉要求

- 图注必须写清统计单位（独立训练 seed）和 episode 使用方式；对 KM/RMST 还需说明 matched exposure、右删失和时间窗。
- 主图不以“正/负结果清单”展开。边界图用中性句一次说明，不把 P3/P4 诊断列入摘要或主叙事标题。
- 同一方法必须跨图保持颜色、marker 和名称一致；`Full`、`MAPPO`、`HAPPO`、`wider single-graph` 的主图身份应固定。
- 最终交付前应在最终版宽度目视检查中文字体、线型在灰阶下的可辨性、表格可读性和图注自足性。

## 来源与审计依据

- 代码事实：`envs/uav_intercept_3d_env.py`、`algorithms/ri_gmappo/simple_ri_gmappo.py`。
- 锁定统计：`docs/statistics/P1B_DECISION_MEMO_V1_1.md` 与 `docs/statistics/survival_results_v1_1/`。
- 锁定层级：`docs/EVIDENCE_STATUS_REGISTRY.csv`、`docs/PAPER_ASSET_SPEC.md`。
- 当前渲染脚本：`_operator_scripts/render_paper_figures_v1_5.py`、`_operator_scripts/analyze_gate_prior_v1_5.py`。
