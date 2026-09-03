# P3-P1 静态拓扑课程技术审计授权

授权范围仅为实现与审计 `StaticTopologySchedule`：0--25% nominal、25--60% Tier-R uniform、60--100% 全 group uniform。调度器只能根据 update index 和训练 RNG 选择已有 fault group。

禁止 PPO rollout/update、RL training、正式 evaluation、云端训练、调 schedule 边界、改环境/奖励/mask/learner，及自动进入 P3-P2。
