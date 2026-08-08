# 方法—代码可追溯审计

**范围**：3DOF EA-RG 主线（生存分析锁定版本）。本文件只记录已由代码、配置和锁定证据支持的事实；不改变实现、原始结果或论文正文。

## 审计结论

当前正式实现支持的核心方法表述是：在 3DOF 异构 UAV 拦截环境中，策略演员使用三个显式关系通道（感知、通信、任务支撑）的边特征图注意力编码器，并融合一个联合邻接图的残差信息路径。通信可达性由环境决定；静态角色对调制及其 Gate Prior 是辅助结构，其中 Gate Prior 是初始化偏置而不是运行时故障自适应机制。

## 可追溯事实表

| 方法/环境事实 | 代码或配置锚点 | 审计状态 | 允许的论文表述 | 禁止或需收缩的表述 |
|---|---|---|---|---|
| 图有 3 个显式关系通道：perception、communication、task-support | `envs/uav_intercept_3d_env.py:53-58, 1038, 1110-1112`; `algorithms/ri_gmappo/simple_ri_gmappo.py:244-255` | 已确认 | “三关系图编码器” | “四关系图编码器”；“攻击窗口关系通道” |
| 节点为 scout、relay、attacker 与 target；target 不是动作主体 | `envs/uav_intercept_3d_env.py:133-167`; `paper_latex_3d_en/sections/04_method.tex:7-14` | 已确认 | “3 个蓝方决策 UAV 加 1 个目标节点” | “目标参与联合动作” |
| 邻接采用 receiver–sender 方向 | `envs/uav_intercept_3d_env.py:1094-1112`; `paper_latex_3d_en/sections/04_method.tex:14` | 已确认 | “`A[i,j]` 表示 j 向 i 聚合” | 未说明方向却将图示箭头解释为相反方向 |
| 感知边代表蓝方对目标的直接探测 | `envs/uav_intercept_3d_env.py:1090, 1110`; `_radar_visible` at `envs/uav_intercept_3d_env.py:579-607` | 已确认 | “由有效探测激活的感知关系” | “所有 UAV 恒有目标观测” |
| 通信边由距离、dropout、delay 与节点失效共同约束 | `envs/uav_intercept_3d_env.py:477-566`; `_is_comm_failed` at `:574-579` | 已确认 | “环境驱动的可递送通信邻接” | “策略网络学习决定实际物理链路是否发送” |
| Task-Support 是对已递送通信的、角色兼容且信息状态相关的关系掩码 | `envs/uav_intercept_3d_env.py:1092-1112, 1149-1175` | 已确认 | “任务相关的已递送信息关系掩码” | “独立通信信道”；“额外字节传输通道” |
| 攻击窗口是节点特征/Task-Support 激活条件之一，不是 relation channel | `envs/uav_intercept_3d_env.py:1068, 1103-1113, 1172-1175` | 已确认 | “攻击窗口作为局部状态特征参与表征” | “Attack-window relation” |
| 边特征维度为 17，包括相对几何、速度、感知/通信/支撑标记、消息年龄与置信度 | `envs/uav_intercept_3d_env.py:44-58, 1113-1133`; `paper_latex_3d_en/sections/04_method.tex:49-59` | 已确认 | “17 维图计算边特征” | “17 维通信报文” |
| 注意力先经关系邻接 + self-loop 硬掩码，再 softmax；边特征进入 score | `algorithms/ri_gmappo/simple_ri_gmappo.py:127-156, 163-201` | 已确认 | “状态相关、边特征调制的掩码注意力” | “注意力门控实际传输字节” |
| 每一层按关系独立处理，并另有联合图 GAT 残差输入后融合；编码器有两层 | `algorithms/ri_gmappo/simple_ri_gmappo.py:244-347` | 已确认 | “关系专属分支与联合图残差路径融合的两层编码器” | “只有三条关系消息、无联合图残差”；“四条互斥关系分支” |
| 角色对门是 relation × receiver-role × sender-role 的静态向量调制 | `algorithms/ri_gmappo/simple_ri_gmappo.py:159-207` | 已确认 | “静态角色对消息调制” | “按故障状态动态启闭链路”；“消息剪枝/带宽压缩” |
| Gate Prior 只对部分角色对 embedding 写入初始 logit 0.4；消融初始为 0 | `algorithms/ri_gmappo/simple_ri_gmappo.py:258-303`; `configs/paper/ea_rg_mappo_gate_prior.yaml:3-15` | 已确认 | “结构化初始化偏置（sigmoid 约 0.599）” | “在线 Gate Prior”或“故障后自适应 prior” |
| Actor 用局部观测和图；critic 接收 shared observation 与角色 one-hot，不使用图门 | `algorithms/ri_gmappo/simple_ri_gmappo.py:452-540, 552-625` | 已确认 | “CTDE，去中心化 actor/集中式 critic” | “critic 通过 Gate 直接推理” |
| 训练入口可控制 graph encoder、Task-Support 消融、角色门消融、prior 强度 | `scripts/train_ri_gmappo.py:12-169`; `scripts/run_3d_role_pair_gate_ablation_protocol.py:56-70`; `scripts/run_3d_task_support_ablation_protocol.py:57-70` | 已确认 | “消融保持其余图结构条件不变” | 未核验的“所有基线参数完全等量” |

## 论文方程的实现边界

1. `paper_latex_3d_en/sections/04_method.tex:27-38` 中以抽象的关系消息函数描述多关系编码，方向上与实现一致；实际实现的角色对门直接调制发送方嵌入，关系分支随后与联合图 GAT 输出拼接并融合。
2. `:49-59` 的硬掩码和边特征调制与实现一致。应把“物理通信”和“图消息聚合”严格分开：后者不产生真实发送动作。
3. `:61-64` 中 Task-Support 的“通信可用 + 角色兼容 + 信息相关”条件与 `_active_support_edge` 一致。建议最终中文稿避免把“local attack window”写成第四个关系。
4. `:66-78` 对静态角色对调制和 Gate Prior 的功能边界与代码一致；结论只能写为锁定实验中所观察到的优化稳定性关联，不可从结构本身推出因果性或运行时重构。

## 与锁定结果的对应关系

| 证据层 | 可保留的结论 | 约束来源 |
|---|---|---|
| P1_CORE | 在 matched exposure 下，相对 MAPPO 的早期 RMST 优势 | `docs/statistics/P1B_DECISION_MEMO_V1_1.md` |
| P2_SUPPORTING | Gate Prior 与跨 seed 优化一致性相关；Task-Support 有经验性贡献 | `docs/P0_PROVENANCE_LOCK_V1_6_PROPOSED.md`; 锁定消融 |
| P3_BOUNDARY | OOD 迁移依赖分布，通信拓扑变化会逆转比较 | `docs/statistics/p3a_ood_results_v1_1/` |
| P4_DIAGNOSTIC | 静态 Role-Pair 调制没有独立效益；任务支撑时序案例不构成故障后重组机制证据 | `docs/EVIDENCE_STATUS_REGISTRY.csv` |

## 发现的实施—稿件风险

- **高优先级**：主方法图含“Attack-window relation”图例和粉色关系线，但代码只定义 3 个 relation channel。必须修图，不能用文字说明掩盖。
- **高优先级**：Gate Prior 现有图只显示 `w/o Gate Prior` 曲线；但正文及 caption 声称显示 “with and without”。该图不能作为 P2 证据，直至从锁定数据重新渲染并目视核验。
- **中优先级**：`scripts/plot_method_overview.py` 是旧 EA-RG-MAPPO-S/随机半径路线，且使用“physical edge relation”等旧语言；不得用作当前 3DOF 主稿方法图。
- **中优先级**：Task-Support 是动态关系掩码，但其独立消融不等于证明“故障后关系重组”。正文必须维持“经验性贡献”的边界。

## 审计完成条件

本文件完成代码与配置事实追溯。需要主笔在重绘方法图、重新生成 Gate Prior 双曲线或将其路由至补充材料后，再解除相应图件的发布阻塞。
