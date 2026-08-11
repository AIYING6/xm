# v1.6R 应用型算法论文主线

状态：`APPLIED_ALGORITHM_TRACK_SELECTED__METHOD_PROTOCOL_PENDING_IMPLEMENTATION`

## 论文目标

目标不是提出一个通用 MARL 理论家族，而是形成一篇有明确算法机制、严格比较和物理任务证据的异构 UAV 应用型算法论文。

## 已确认问题

R2/R2R 已确认：合法 target evidence 能够到达 actor，BC policy 能在闭环中进入 attack geometry，但 vanilla PPO 更新会破坏已有 pursuit 行为。R3 的固定 retention loss 只能部分保持 geometry，未改善 neutralization，因此不能直接作为最终方法。

## 唯一候选方法方向

工作名：**Evidence-Gated Behavior-Retentive MAPPO (EG-BR-MAPPO)**。

核心不是增加图、memory、stage 或新 reward，而是在 PPO policy improvement 与已有 pursuit 行为之间建立状态选择性的约束：

1. 只在合法 target evidence 存在的状态启用 retention 门控；
2. 门控强度由当前 PPO 的 detached normalized advantage 决定：估计表现较差时加强 reference 保护，估计表现较好时自动减弱，避免把策略永久锁死在 BC 行为；
3. retention 只作用于 continuous turn/climb guidance，不改变 mission physics、reward 或 actor information；
4. critic 仍可使用训练期 share observation，但任何 privileged 字段不得流入 actor。

这与 R3 固定 evidence-mask retention 的区别是：R3 对所有 evidence 状态使用固定约束；EG-BR-MAPPO 使用 evidence mask × advantage-conditioned gate，使 policy improvement 与行为保护在同一更新中自适应平衡。

## 严格比较

- BC-Frozen：闭环 competent reference；
- vanilla MAPPO：同一 BC 初始化、同一 rollout、同一 PPO；
- fixed-retention PPO：R3 对照；
- EG-BR-MAPPO：唯一新增 adaptive evidence-gated retention；
- 所有方法共享 environment、reward、actor contract、action space、horizon、critic 与 evaluation seeds。

## 硬退出条件

只允许一次 development pilot。若 EG-BR-MAPPO 不能在两个 seed 上同时：

- 保持或改善 geometry acquisition；
- 不恶化 evidence-to-range latency；
- 至少改善一个 mission endpoint；

则关闭当前 v1.6R 算法线，不再做 EG-BR-MAPPO-v2、换系数或增加模块。

在方法接口和 deterministic regression 完成前，不进入正式 F1/F2，也不把 R3 partial 结果包装成方法性能证据。
