# 图表契约（P5）

本契约定义下一轮中文稿图表的科学目的、证据来源和发布条件。它不授权改变锁定数据或生成新的实验结果。

## Fig. 1 | 任务与三关系图编码

- **核心结论**：该问题将间歇感知、环境驱动受限通信与节点失效下的任务链恢复，表示为可观测的三关系图输入。
- **原型**：schematic-led composite。
- **面板**：a，3DOF scout–relay–attacker–target 任务与 failure window；b，perception / communication / task-support 三关系、17 维边特征、union residual、静态 role-pair modulation。
- **证据来源**：环境和编码器代码（MF01–MF10）。
- **发布阻塞**：现有 b 面板含错误第四关系，必须重绘；攻击窗口只能标为节点状态/支持边条件。
- **不可声称**：策略学习实际物理发送、动态角色门剪枝、6DOF 航空器实现。

## Fig. 2 | 匹配暴露下的早期任务链恢复

- **核心结论**：在锁定 held-out 分布与 matched failure exposure 下，Full 相对 MAPPO 更早恢复；完整随访中与 HAPPO/wider single-graph 竞争。
- **原型**：quantitative grid（一个主 KM 面板 + 紧凑 RMST80/220 数字面板或相邻表）。
- **主曲线**：Full、MAPPO、HAPPO、wider single-graph；其余方法完整曲线入补充材料。
- **证据来源**：`docs/statistics/survival_results_v1_1/`、P1B memo。
- **统计要求**：注明 3 个独立训练 seed、Early+Nominal、每 method 600 exposure、右删失、RMST 时间窗与“lower is earlier”。
- **发布阻塞**：无数据阻塞；需要重排图例、线型和图注以避免九方法拥挤。

## Table 1 | Held-out 性能与恢复时间

- **核心结论**：Full 终局可靠性在第一梯队，但不是 recovery 最高；条件恢复时间只能作描述性指标。
- **原型**：紧凑主结果表。
- **证据来源**：锁定 table1 + survival lock。
- **最小字段**：方法、recovery、success、条件 `t_rec`、RMST80、RMST220；必要时仅保留 Full/MAPPO/HAPPO/wider SG 及消融连接说明。
- **发布阻塞**：避免把 conditionally recovered-only 的 `t_rec` 写成完整恢复分布结论。

## Table 2 | 受控组件消融

- **核心结论**：Gate Prior 与 Task-Support 具有限定的支持；Role-Pair 调制未获得独立有效性支持。
- **原型**：quantitative grid。
- **证据来源**：锁定 ablation 与 P1B memo。
- **主文措辞**：Gate Prior = structured optimization initialization；Task-Support = empirical relational contribution；Role-Pair = auxiliary component。
- **发布阻塞**：无数据阻塞；避免 caption 以“每个模块均有效”概括。

## Fig. S1 / Table S1 | 全部 KM 与 seedwise RMST

- **核心结论**：提供完整比较和时间窗敏感性，而不占用主叙事。
- **证据来源**：survival results v1.1。
- **发布条件**：与主文方法命名、颜色、时间窗定义一致。

## Fig. S2 | Gate Prior 优化一致性

- **核心结论**：若使用锁定双组轨迹，prior 对初始结构和跨 seed 一致性有支持；不说明运行时自适应。
- **原型**：two-panel quantitative grid（gate mean/dispersion + success trajectory）。
- **证据来源**：锁定 `gate_prior_v1_5_assets`。
- **发布阻塞**：当前 `fig_gate_evolution` 缺 Full 曲线，必须重渲染并目视核验。若不能完成，删去图，仅保留受限文字/表述。

## Fig. S3 / Table S2 | In-distribution robustness

- **核心结论**：邻近通信和失效扰动下的竞争性表现，不构成 OOD 泛化证明。
- **证据来源**：锁定 canonical v1.5 robustness。
- **路由**：Supplementary；主文最多一句简述。
- **发布条件**：R00–R09 的定义、暴露不足单元和 `n=3` 清楚列出。

## Table 3 | Zero-shot OOD 的必要边界

- **核心结论**：优势不随所有未见分布变化普遍迁移；几何可部分保留，拓扑变化可反转，机动族 early RMST80 可饱和。
- **原型**：主文 compact boundary table（family 级，而非 seed × 7 cell 全表）。
- **证据来源**：P3-A lock。
- **路由**：主文仅 family-level + aggregate；完整 seed/cell、oracle 和 saturation audit 入 Supplementary。
- **发布条件**：不使用“Gate C”；不把饱和当成方法等价或失败的额外叙事中心。

## Table S3 | 计算成本

- **核心结论**：Full 的计算代价更高，任务层面的早期恢复不等同每步推理效率。
- **证据来源**：locked profiling。
- **路由**：Supplementary 或 Methods 一句；不得作为贡献图。

## 最终图表 QA 闸门

1. 每个图只服务一个明确结论，并有可回溯来源。
2. 方法图与 `RELATION3D_COUNT = 3` 一致；不得出现隐藏第四关系。
3. 图注自足：方法颜色/线型、`n`、误差/删失、统计单位与 metric direction 均明确。
4. P1 先于 P2，P2 先于 P3，P4 只在必要时出现；负结果比例不超过其科学必要性。
5. 所有重渲染必须读取锁定数据，保存生成脚本、输入文件哈希和最终 PDF/PNG 目视检查记录。
