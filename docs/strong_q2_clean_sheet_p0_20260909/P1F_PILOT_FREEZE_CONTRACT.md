# P1F：可微目标、公平性与 P2 小试验冻结合同

## 目标

P1F 只判断候选决策核能否形成公平、可微、无真值泄漏的 PPO 训练合同。通过 P1F 不等于算法有效，只表示可以准备受限 P2 pilot。

## 唯一方法差异

候选与直接 recurrent 对照共享：局部历史、GRU、物理动作 head、参数总量、PPO clipped objective、可靠度区间校准项、训练 seed、训练预算和固定评价 tape。

- 候选使用三种任务模式在概率区间两个端点上的平滑最小价值作为 mode logits；
- 对照使用相同容量的直接 recurrent mode logits；
- realized delivery 只用于环境转移和评价遥测，不进入 actor 或 actor loss；
- 校准目标是公开可靠度上下文，不是本回合是否送达。

模糊半径 0.05 是冻结的设计裕度，不解释为统计置信区间。

## P2 pilot 冻结规模

| 项目 | 冻结值 |
|---|---|
| 方法 | 信息集候选、容量与风险同时匹配的 recurrent 主对照 |
| training seeds | 98101、98102、98103 |
| 每条固定终点 | 1,000,000 个 3DOF 物理步，即 62,500 个完整 episode |
| 总上限 | 6,000,000 个 3DOF 物理步 |
| checkpoint 选择 | 禁止；只用固定终点 |
| 评价 tape | P1E 冻结的 300 episode tape |
| PPO clip | 0.20 |
| calibration weight | 0.10 |
| ambiguity radius | 0.05 |
| smooth-min temperature | 0.10 |

recurrent 主对照使用相同的单边承诺任务代价与校准目标，因此它同时完成容量匹配和风险匹配；另设一个重复的“risk-matched”训练 arm 不会增加可识别信息，故不纳入 pilot。

高层策略只选择 commit、defer 或 fallback；每次决策由同一个冻结低层控制器执行 16 个 3DOF 物理步。训练预算按物理步计数，公开线索阶段不推进物理仿真，也不计入 1M。

## 训练前最后检查

在生成云端包之前还必须完成：

1. 将 mode policy 与现有 PPO rollout/buffer 接口连接；
2. 证明三种训练方法读取同一 tape、同一环境和同一 reward；
3. 日志逐 seed 输出任务价值、双边承诺、单边承诺、defer、fallback、collision、constraint violation 和 timeout；
4. 用短至不构成性能证据的 smoke rollout 验证参数确实更新、断点可恢复、固定终点不会被覆盖；
5. 冻结软件版本和包哈希。

## P2 继续标准

只有容量匹配 recurrent 基线具备可学习性，且候选在至少 2/3 seed 同时满足下列条件，才允许进入正式实验：

- 单边/不兼容承诺率相对容量匹配 recurrent 至少降低 5 个百分点；
- 平均任务价值差不低于 -0.5；
- high-context commit rate 至少比 low-context 高 20 个百分点；
- fallback rate 相对基线增加不超过 20 个百分点；
- 无 NaN、非法动作、碰撞或约束违规异常增加。

基线可学习性要求：容量匹配 recurrent 的平均任务价值高于 always-defer 的冻结值 2.933。若不满足，P2 只能判为任务/训练不可识别，不能据此评价候选算法。

失败后不扫 ambiguity radius、calibration weight 或 soft-min temperature，不追加 seed，也不把 pilot 当论文结果。
