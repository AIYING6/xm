# Fig. 1 PCRF-R2 内容审计

## 图中采用的冻结术语及来源

| 图中术语 | 冻结含义 | 采用依据 |
|---|---|---|
| Scout / Relay / Attacker / Target | 当前 3DOF 异构协同任务的角色与目标实体 | `envs/uav_intercept_3d_env.py` 的角色常量与节点构造；v1.9 F1 协议。 |
| P: direct perception | 接收方对目标的直接局部感知主张，带可用性与质量字段 | `V1_9_PCRF_R2_THEORY_AND_PROTOCOL_FREEZE.md` 第 2 节；`_get_pcrf_r2_sources`。 |
| C: delivered/cache-valid communication | 仅实际递送且在最大消息年龄内的 packet/cache 证据，保留 age/confidence | PCRF-R2 理论冻结第 2 节；环境的 `cache_valid_target_packet`。 |
| recipient-specific execution | actor 只使用当前接收方合法可得的 P/C/context；critic-only 状态不得进入 actor | PCRF-R2 理论冻结第 2 节；F1 协议的 CTDE 描述。 |
| P encoder / C encoder | 两个来源的独立编码路径 \(F_P\)、\(F_C\) | PCRF-R2 理论冻结第 3 节；`PCRFR2Encoder`。 |
| source-preserving fusion | 将两条来源路径保持到可用性掩蔽融合阶段，而非先合并为统一残差表示 | PCRF-R2 理论冻结第 3--4 节。 |
| conflict-conditioned deviation; \(\Delta(0)=0\) | 动态偏移只使用合法可用性差异、分歧、age、confidence；中性状态精确回到基线 | PCRF-R2 理论冻结第 3 节；实现中 `fusion_gate` 的中性校正。 |

## 被明确排除的旧结构

本图不将历史三关系方法或其模块绘入架构：没有第三关系、旧 EA-RG 编码器、Gate Prior、union residual 或 Role-Pair gate。它们不属于 v1.9 PCRF-R2 的科学对象；图中的“两来源 R2 only”仅陈述当前结构的正向边界，不把旧模块名称放入最终图面。

## 图形证据边界

该图是实现/协议总览，不包含 F1 training-time validation 数值、checkpoint winner、F2 episode、性能排序、统计区间或机制结论。它只能支持“系统按何种信息合约和编码结构设计”，不能支持“PCRF-R2 已优于比较方法”。

## Reference-asset-preserving 视觉审计

- 用户提供的参考仅为 PNG；未提供可复制的 SVG/PDF/源矢量对象。因此最终图直接保留该 PNG 中的 Scout、Relay、Attacker、Target tower、山地、failure-X、面板边框与底部角色图例像素资产，而不重新绘制这些资产。
- 只遮盖旧科学标签及已否定的第三来源槽位，再在同一坐标母版内写入 PCRF-R2 术语与模块。
- `fig1_architecture_asset_preserving_metrics.json` 记录面板、图例、caption 的参考坐标与候选坐标；被保留角色资产的中心偏差为 0%，主面板 bounding-box 偏差为 0%，均低于本轮阈值。
- 因输入资产为位图，SVG/PDF 是嵌入高保真 PNG 的论文容器；不把这些角色图标宣称为可编辑的原始矢量对象。
