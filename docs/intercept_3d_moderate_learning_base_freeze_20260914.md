# 3DOF 中等难度学习底座冻结（开发阶段）

日期：2026-09-14  
状态：`development_learning_base_frozen`，不属于论文结果。

## 冻结的事实

在 `weaving_mild` 目标、通信丢包 0.25、雷达丢包 0.15、消息延迟 4 步的 3DOF 条件下，采用“本地观测合法控制器的行为克隆 + 五轮 DAgger 初始化 + 低学习率 PPO + 行为保持项”的开发训练链，在独立的三个开发 seed 上得到如下 60-episode 终点结果：

| seed | 成功率 | 超时率 | 碰撞率 | 结果文件 |
| --- | ---: | ---: | ---: | --- |
| 5104 | 1.00 | 0.00 | 0.00 | `results/development/intercept_3d_moderate_bc_regularized_ppo_replication/seed5104/endpoint_evaluation.csv` |
| 5105 | 0.70 | 0.30 | 0.00 | `results/development/intercept_3d_moderate_bc_regularized_ppo_calibration/seed5105/read_only_best_endpoint_evaluation.csv` |
| 5106 | 0.85 | 0.15 | 0.00 | `results/development/intercept_3d_moderate_bc_regularized_ppo_preformal/seed5106/ppo/endpoint_evaluation.csv` |

每个终点评估使用与训练内 checkpoint 选择带分离的固定 60-episode 带。5105 通过只读工具重新评估其训练内选出的 `actor_critic_best.pt`，避免把最后更新的 checkpoint 与选择规则混淆。

## 这允许什么

这证明当前任务条件和训练骨干足以支撑下一阶段的**受控方法比较**。后续方法只能在保持环境转移、奖励、观测、动作、PPO 预算和评估带不变的前提下，改变预先声明的单一机制。

## 这不允许什么

这些均为开发证据，不能作为论文性能表、泛化结论或新方法有效性的证据。它们也不能证明所有随机种子、故障条件或更高难度任务都可学习。
