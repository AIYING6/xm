# P8C ACFID 多划分、多上下文压力复核

## 结论

`ACFID_P0C_STRESS_PASS`

共享结构交互机制通过压力复核，可以进入学习型 pilot 的实现与代码审计阶段。当前仅授权实现，不授权直接训练；训练前仍需通过组合泄漏、方法差异、预算和评价端点预检。

## 固定设计

- 5 个独立上下文随机种子；
- 每个种子 120 个上下文；
- 8 个预先固定的平衡训练 pair 划分；
- 共 40 个 `context seed × pair split` 审计单元；
- 每个划分保持三类跨类型故障交互及同/跨任务分支覆盖；
- 环境、故障强度、恢复动作、评价组合和模型阈值均未因 P8B 结果修改。

## 结果

| 检查 | 结果 |
|---|---:|
| structured 相对 additive 的 pair regret 增益达标比例 | 40/40（100%） |
| structured 优于 type-only 比例 | 40/40（100%） |
| triple/quadruple 相对 additive 非劣比例 | 40/40（100%） |
| 全部单元 pair regret 中位相对增益 | 55.19% |

各上下文种子的中位 pair regret 增益：

| seed | 中位增益 |
|---:|---:|
| 98101 | 57.24% |
| 98102 | 53.05% |
| 98103 | 59.56% |
| 98104 | 53.88% |
| 98105 | 49.04% |

## 证据边界

P0C 证明的是：在冻结宏观任务生成机制中，故障类型、任务分支和任务上下文构成的共享参数化具有稳定的未见组合预测价值。它尚未证明：

- MAPPO 能从轨迹中学得这些交互；
- 表示在连续 3DOF 控制或更真实传感噪声下仍然成立；
- ACFID 的最终任务表现优于强神经基线；
- 真实 UAV 复合故障主要由二阶交互解释。

## 下一步冻结要求

实现 `3 methods × 3 seeds × 1M` pilot：

1. Fault-aware MAPPO：直接条件化 primitive degradation signatures；
2. Additive fault-value model：仅学习单故障主效应；
3. ACFID：学习共享、动作条件且任务结构正则化的 pair interaction。

三者必须共享环境、actor/critic 主干、PPO 目标、参数预算、训练组合、训练步数和模型选择规则。主要端点固定为 held-out compound-fault recovery-action regret，任务成功率为共同主要表现端点；训练期间不得出现 held-out pair/triple/quadruple。
