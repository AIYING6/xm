# Fig. 1 PCRF-R2 内容审计

## 图中采用的冻结术语及来源

| 图中术语 | 冻结含义 | 采用依据 |
|---|---|---|
| Scout / Relay / Attacker / Target | 当前 3DOF 异构协同任务的角色与目标实体 | `envs/uav_intercept_3d_env.py` 的角色常量与节点构造；v1.9 F1 协议。 |
| P: direct perception | 接收方自身对 target 的直接局部感知；图中以 receiver-to-target 蓝色 sensing ray 表达，并非 agent-to-agent 通信关系 | `V1_9_PCRF_R2_THEORY_AND_PROTOCOL_FREEZE.md` 第 2 节；`_get_pcrf_r2_sources`。 |
| C: delivered/cache-valid communication | sender-to-receiver 的已递送 packet，携带 target snapshot；仅实际递送、cache-valid、且 `age ≤ max_target_message_age_steps` 的证据可进入 C | PCRF-R2 理论冻结第 2 节；环境的 `cache_valid_target_packet`。 |
| C validity filter | expired、dropped、pending、invalid 或 undelivered packet 在 actor C 分支前剔除，产生 zero C node/edge/adjacency；不得只降 confidence 后保留 | 环境的 `cache_valid_target_packet` 与 R2 source construction。 |
| recipient-specific execution | actor 只使用当前接收方合法可得的 P/C/context；critic-only 状态不得进入 actor | PCRF-R2 理论冻结第 2 节；F1 协议的 CTDE 描述。 |
| P encoder / C encoder | 两个来源的独立图编码路径 \(F_P\)、\(F_C\)，图输入分别含对应 nodes/edges/adjacency 和 role | PCRF-R2 理论冻结第 3 节；`TwoSourcePCRFR2Encoder`。 |
| source-free \(z_{ctx}\) | 独立 context encoder 的输入仅含 receiver self/role/local task/local attack/fixed capability；不含 target estimate/cache、packet age/confidence 或 teammate payload | PCRF-R2 理论冻结第 2 节；环境 context masking 与 policy 的 `r2_context_encoder`。 |
| critic | 训练期 MLP critic 接收 centralized `share_obs` 与 current-agent role one-hot：\(V_\psi(share\_obs, role_i)\)；global reward 仅进入 return/advantage/PPO loss | `RIGMAPPOAgent.critic_value` 与 rollout/PPO implementation。 |
| source-preserving fusion | 将两条来源路径保持到可用性掩蔽融合阶段，而非先合并为统一残差表示 | PCRF-R2 理论冻结第 3--4 节。 |
| conflict-conditioned deviation | \(\delta(c)=g(c)-g(0)\)，故 \(\delta(0)=0\)；\(w=\operatorname{masked\_softmax}(\beta+\delta(c);m^P,m^C)\)。动态偏移只使用合法可用性差异、分歧、age、confidence | PCRF-R2 理论冻结第 3 节；实现中 neutral correction。 |
| comparator parity | PCRF-R2、single-R2、matched-nongraph-R2 使用同一合法 P/C raw fields；single 保留 source tag 但用 unified graph，non-graph 无 graph message passing，参数量近似匹配 | PCRF-R2 理论冻结第 4 节与 R2 capacity audit。 |

## 被明确排除的旧结构

本图不将历史三关系方法或其模块绘入架构：没有第三关系、旧 EA-RG 编码器、Gate Prior、union residual 或 Role-Pair gate。它们不属于 v1.9 PCRF-R2 的科学对象；图中的“两来源 R2 only”仅陈述当前结构的正向边界，不把旧模块名称放入最终图面。

## 图形证据边界

该图是实现/协议总览，不包含 F1 training-time validation 数值、checkpoint winner、F2 episode、性能排序、统计区间或机制结论。它只能支持“系统按何种信息合约和编码结构设计”，不能支持“PCRF-R2 已优于比较方法”。

## Reference-asset-preserving 视觉审计

- 用户提供的参考仅为 PNG；未提供可复制的 SVG/PDF/源矢量对象。因此最终图直接保留该 PNG 中的 Scout、Relay、Attacker、Target tower、山地、failure-X、面板边框与底部角色图例像素资产，而不重新绘制这些资产。
- 只遮盖旧科学标签及已否定的第三来源槽位，再在同一坐标母版内写入 PCRF-R2 术语与模块。
- `fig1_architecture_asset_preserving_metrics.json` 记录面板、图例、caption 的参考坐标与候选坐标；被保留角色资产的中心偏差为 0%，主面板 bounding-box 偏差为 0%，均低于本轮阈值。科学替换后的文字内容与模块内部不应被误读为对旧 EA-RG 标签的逐字对齐。
- 因输入资产为位图，SVG/PDF 是嵌入高保真 PNG 的论文容器；不把这些角色图标宣称为可编辑的原始矢量对象。
