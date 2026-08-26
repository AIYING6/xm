# DRTP / MAPPO-NoGraph 外部参考训练合同（V1）

## 目的与边界

本合同只补充一条标准 CTDE MAPPO 的无图通信外部参考线，以增强论文的外部基线覆盖。它不修改、替代或重新裁决既有 UTR–DRTP 正式五种子结果；UTR–DRTP 仍是唯一用于归因“均匀拓扑扰动加权 vs DRTP 自适应加权”的同构主消融。

该参考在实现中命名为 `MAPPO-NoGraph`（`mappo_ng`）：使用当前 3D S2 训练器中的 `graph_encoder=no_graph` 分支。actor 不进行图消息传递；critic 仍是 MAPPO 的集中式训练 critic。由于其 actor 表征与 SG 不同，本比较只能回答“DRTP/UTR 相对一个无图 MAPPO 外部参考的性能位置”，不能单独归因任何 DRTP 收益。

## 冻结方法与训练

- 方法：`MAPPO-NoGraph`；`graph_encoder=no_graph`，`hidden_dim=64`，`role_gate_mode=none`，训练前由预检实际计算并记录参数量。
- 训练 seed：`2301, 2302, 2303, 2304, 2305`；与现有 UTR/DRTP 正式比较逐 seed 配对。
- 每条轨迹从零开始、严格连续训练 `39,063` updates，即 `10,000,128` environment steps；最终比较只使用共同 `10m` checkpoint。
- 使用与 UTR 相同的 PPO、S2 3D 环境、动作空间、reward、failure semantics、actor 原始观测边界、七组 topology universe。
- 训练 exposure 固定为 UTR 规则：50% nominal anchor + 条件均匀的六个 failure groups；不使用任何 DRTP `q`/EMA/difficulty/return-adaptive sampling。
- 从 update 0 启用完整 runtime-state persistence；保存固定里程碑仅用于曲线，禁止 early stopping、best-checkpoint promotion、seed exclusion、warm restart 或 seed replacement。

## 冻结评价

评价必须复用既有正式 deterministic tape，hash 为
`84e31ed185ced0608a30c9cb9f9659c7423c952e4603aac53cf691c54fc64ac2`：episode IDs `490000–490099`、12 个 nominal/F0/timing/duration/compound conditions，每条件 100 episodes。

报告每个 training seed 和 pooled 的 `J_nominal`、`J_F0`、`J_OOD_mean`、`J_OOD_worst`、collision、timeout、constraint violation、risk-set trigger validity、pre-trigger collision。训练 seed 是唯一独立推断单位；全部五个 seed 和全部原始 episode 必须保留。

聚合时同时呈现 MAPPO-NoGraph − UTR 和 MAPPO-NoGraph − DRTP 的 paired effect（mean、median、wins、worst）。不对这一外部参考设立事后 PASS/FAIL 阈值，亦不改写 `FORMAL_CONFIRMATION_PASS_SEED_SENSITIVE` 的历史 DRTP/UTR 结论。

## 停止规则

完成五条 MAPPO-NoGraph、最终 checkpoint 评价、聚合和结果打包后立即停止。不得自动启动新的算法、更多 seed、canonical、held-out、规模扩展或超参数搜索。
