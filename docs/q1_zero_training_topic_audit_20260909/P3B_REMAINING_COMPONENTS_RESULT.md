# P3B：价值估计器与循环 PPO 组件审计

**结论：** `P3B_REMAINING_COMPONENTS_PASS`

本轮实现了决策相关主动诊断 pilot 缺失的两个基础组件：部署合法的 task-value estimator，以及共享参数的 recurrent role-graph MAPPO 序列路径。

## 通过项

- estimator 的部署接口只接收公共/集中式合法状态，并自行枚举 2 个候选故障模式×2 个恢复选项；
- 模拟器真值仅可用于选择监督损失中的候选行，不能作为 actor 或 gate 输入；
- estimator、优化器、归一化统计、监督 replay 及 replay RNG 可精确恢复；
- 三个冻结 arm 使用相同 3,626 参数的小型审计网络；正式 runner 仍按合同使用统一冻结宽度；
- 32 步×2 环境序列可精确重放；第 13 步只清零已完成环境槽位；每 8 步截断 BPTT；
- 外部门控接管的 8 个 agent-time 样本不进入 actor policy/entropy loss；
- actor loss、GRU 梯度和模型/优化器/hidden checkpoint 均有限且可恢复。

## 证据边界

审计使用固定合成 task-value target，并进行了 180 次辅助梯度步，只为验证 estimator 可训练、序列化后行为一致、估计误差不会改变两种冻结先验下的测试 gate 决策。它没有创建环境、没有执行 PPO 性能更新，也没有比较任务 return。因此不能推出 estimator 能从 pilot 数据学准、DVOI 优于 entropy、循环策略有效或新算法具备性能收益。

## 当前决策

组件级实现门通过，但性能 pilot 尚未授权。剩余唯一阻塞项是集成三 arm 的真实环境 outer runner 与 frozen evaluation tape；该 runner 必须接受 32–128 步真实环境 rollout、双动作轨迹、真实 episode-return estimator 监督和 checkpoint replay 审计。

机器可读结果：`artifacts/active_diagnosis_p3b/P3B_REMAINING_COMPONENTS_RESULT.json`。
