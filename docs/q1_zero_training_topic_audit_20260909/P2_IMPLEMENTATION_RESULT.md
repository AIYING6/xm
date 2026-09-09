# P2 数学核心实现结果

**裁决：** `P2_MATH_CORE_PASS_TRAINABLE_INTERFACE_PENDING`

## 已实现

`algorithms/active_diagnosis/decision_relevant_probe.py` 实现了：

- Bayes 任务遗憾；
- 基于最优恢复动作的故障决策等价类；
- 探测后的期望后验任务遗憾；
- 扣除物理成本后的决策相关探测价值；
- 受硬预算约束的正价值 probe 选择。

该模块不依赖 PyTorch、PPO 或环境 rollout，因而可以独立审计算法定义。

## 已验证性质

1. 将一个故障标签拆成两个任务决策完全相同的标签，不改变探测价值；
2. 正确观测核下，零成本信息不会增加期望 Bayes 任务遗憾；
3. 成本超过可减少遗憾时拒绝探测；
4. 直接观察真实模式的 oracle 始终上界 belief 决策价值；
5. 对各故障模式具有相同观测分布的 probe 在成本为正时被拒绝；
6. probe budget 耗尽时，即使净价值为正也不能执行。

累计测试结果：`15 passed`，包括 P1A、P1B、P1C 和 P2。

## 当前证据边界

这证明了算法数学对象内部一致，尚未证明：

- learned belief 校准正确；
- 任务价值估计足以计算有效 DVOI；
- mode policy 能在 on-policy 训练中稳定学习；
- 相对 recurrent MAPPO 或 entropy-probe 有性能优势。

因此仍禁止训练。下一步是建立 trainable interface smoke test，且不得在 smoke test 中根据性能调整 reward。
