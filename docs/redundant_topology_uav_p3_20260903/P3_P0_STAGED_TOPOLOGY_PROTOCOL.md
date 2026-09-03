# P3-P0：6 机冗余拓扑鲁棒性预注册设计审计

## 目标与边界

P2.13 已在五个全新训练 seed 上通过基础可学习性门：assigned Scout/Terminal role-SG-MAPPO 能稳定完成 nominal 与 Tier-R 条件。P3 不重开 P2，也不修改环境、奖励、动作 mask、角色 actor、critic 或 PPO。

P3 仅准备比较固定 UTR 与一个**预定义、非自适应**的 staged topology curriculum。它是一个数据分布调度候选，不宣称已有效，更不是在 P0 中实现的新算法。

## 拟冻结对象（尚未授权训练）

- `utr_assigned_role_sg_mappo`：现有 uniform topology collection；
- `staged_topology_assigned_role_sg_mappo`：固定三阶段 schedule：0--25% nominal；25--60% uniform Tier-R；60--100% uniform 全部 topology groups。阶段边界和组集必须在 P1 前冻结，训练中不得由 return、evaluation 或 seed outcome 改变。
- Cohort A 候选 seed：68011--68015；独立 Cohort B 预留：68021--68025；二者均未在维护的源码、配置和文档中出现。
- 每条未来轨迹使用 P2.13 的 3,907 updates / 1,000,192 environment steps；final checkpoint 固定为 1M。
- 未来 evaluation 仅能使用新生成、训练不可读取的 development-only tape；不得使用 P2.13 evaluation episodes 选 schedule 或 checkpoint。

## P0 输出与停止规则

P0 只能返回 `P3_P0_STAGED_TOPOLOGY_FEASIBLE` 或 `P3_P0_NO_GO`。即使 FEASIBLE，也不授权实现、训练、评估、云端包或自动续跑。只有另一个显式 P1 授权才能启动全新训练。
