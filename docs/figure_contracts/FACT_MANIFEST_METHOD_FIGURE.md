# 方法与图表事实清单（P5）

## 使用规则

- 仅用“状态”为 **CONFIRMED** 的条目撰写方法、图注或科学图。
- **CONFLICT** 条目必须先修复或从主文移除；不得用措辞绕过。
- **BOUNDARY** 条目只能按指定层级呈现，不能升级为方法创新或性能主张。

| ID | 类型 | 事实 | 状态 | 事实锚点 | 可用层级 | 图文操作 |
|---|---|---|---|---|---|---|
| MF01 | 图结构 | 4 个节点：3 个蓝方 actor + 1 个目标节点 | CONFIRMED | `envs/uav_intercept_3d_env.py:1033-1040` | P1/P2 | 方法图可显示 4 节点；目标不画成 actor 输出 |
| MF02 | 图结构 | relation adjacency 形状为 `[3,N,N]` | CONFIRMED | `envs/uav_intercept_3d_env.py:1038`; `simple_ri_gmappo.py:356-360` | P2 | 只画 perception/communication/task-support |
| MF03 | 关系 | 感知：蓝方对目标的有效探测 | CONFIRMED | `uav_intercept_3d_env.py:1090,1110` | P2 | 画为 target—蓝方感知边；明确由观测决定 |
| MF04 | 关系 | 通信：环境递送邻接，受距离/dropout/delay/failure 约束 | CONFIRMED | `uav_intercept_3d_env.py:477-566` | P1/P2 | 不画成策略学习的物理开关 |
| MF05 | 关系 | Task-Support：角色兼容、已递送通信、信息状态相关的掩码 | CONFIRMED | `uav_intercept_3d_env.py:1149-1175` | P2 | 不画成独立消息通道 |
| MF06 | 状态 | 攻击窗口为 local node state/Task-Support 条件，不是 relation | CONFIRMED | `uav_intercept_3d_env.py:1068,1103-1113` | P2 | 用节点徽标或条件注释表示 |
| MF07 | 编码器 | 两层关系专属 RoleConditionedGAT + 联合图 GAT 残差融合 | CONFIRMED | `simple_ri_gmappo.py:244-347` | P2 | 方法图需显式或文字注明 union residual；不添加第四 relation |
| MF08 | 注意力 | 边特征进入 attention score，关系邻接为 hard mask，self-loop 始终可用 | CONFIRMED | `simple_ri_gmappo.py:127-156,163-201` | P2 | 图注写“图聚合掩码”，不等同通信载荷 |
| MF09 | 静态调制 | role-pair gate 仅依赖 relation 和角色对，非输入/故障状态 | CONFIRMED | `simple_ri_gmappo.py:188-207` | P4/方法说明 | 作为辅助模块，禁止画成动态故障响应 |
| MF10 | 初始化 | Gate Prior 为选定 role-pair logit 的 0.4 初值 | CONFIRMED | `simple_ri_gmappo.py:258-303`; config | P2 | 可写 structured initialization；不写 runtime prior |
| MF11 | P1结果 | Full 相对 MAPPO 的早期 RMST80 优势，三 seed 同方向 | CONFIRMED | `docs/statistics/P1B_DECISION_MEMO_V1_1.md` | P1 | 主 KM/RMST 图表的唯一 headline |
| MF12 | P1结果 | RMST220 下 Full 对 HAPPO/wider SG 仅有竞争性 | CONFIRMED | `P1B_DECISION_MEMO_V1_1.md` | P1 | 表与 Discussion 要披露，不写全面领先 |
| MF13 | P2结果 | Gate Prior 关联优化一致性；Task-Support 有经验性贡献 | CONFIRMED | `docs/EVIDENCE_STATUS_REGISTRY.csv:E03-E04` | P2 | 小表/修复图；避免机制过推断 |
| MF14 | P3边界 | OOD 对通信拓扑/机动改变不具普遍优势 | CONFIRMED | `docs/EVIDENCE_STATUS_REGISTRY.csv:E05` | P3 | 主文紧凑 boundary table，细节至 Supplementary |
| MF15 | P4诊断 | Role-Pair 调制无稳定独立增益 | CONFIRMED | `docs/EVIDENCE_STATUS_REGISTRY.csv:E06` | P4 | 消融中一次性披露，非主图 |
| MF16 | 现有图 | 方法图图例存在 attack-window 第四关系 | CONFLICT | `paper_latex_3d_en/figures/intercept_3d_multi_relation_graph.png` | 禁用 | 重绘后才可入主文 |
| MF17 | 现有图 | Gate Prior 图缺 Full 曲线，不能支持双组 caption | CONFLICT | `paper_latex_3d_en/figures/fig_gate_evolution.png` | 禁用 | 从锁定数据重渲染，或撤至补充材料 |
| MF18 | 旧资产 | `method_overview_ea_rg_mappo_s.png` 属于旧叙事 | BOUNDARY | `scripts/plot_method_overview.py` | 禁用 | 不得复用 |
| MF19 | 工程边界 | 未完成 JSBSim/6DOF/真实雷达导弹验证 | BOUNDARY | `docs/EVIDENCE_STATUS_REGISTRY.csv:E09` | 局限性 | 不画成实装验证示意 |
