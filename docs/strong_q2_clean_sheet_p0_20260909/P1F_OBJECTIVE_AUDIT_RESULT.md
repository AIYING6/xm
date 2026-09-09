# P1F：可微目标与训练公平性审计结果

## 结论

`P1F_OBJECTIVE_AND_FAIRNESS_AUDIT_PASS`

候选和 recurrent 主对照已形成相同容量、相同 PPO 目标和相同校准目标的可微训练合同。P1F 通过后仍需完成现有 rollout/buffer 的短程接线 smoke，才能生成 P2 pilot 包。

## 核心审计结果

- 两个 actor 的参数量完全一致；在 39 维合法局部观测、32 维 GRU 下均为 8,163 个参数。
- 两种方法均产生有限且归一化的三模式概率分布。
- 两者使用同一个 `commitment_actor_loss`：PPO clipped surrogate 加公开可靠度区间校准项。
- 候选的 GRU、interval head 和 endpoint-value head 均获得有限梯度。
- recurrent 对照的 GRU 和全部 8 维直接模式 head 均获得有限梯度。
- actor loss 只接收公开 `reliability_prior`，不接收 realized delivery、ack、global state 或 teammate belief。
- 模糊半径 0.05 只是冻结设计裕度，不是统计置信区间。

## Pilot 成本修正

原计划中的 capacity-matched recurrent 和 risk-matched recurrent 在奖励与校准目标相同时是同一对照。重复训练不会隔离新的变量，因此合并为一个“容量与风险同时匹配的 recurrent”主对照。

最终 pilot 为：2 个方法 × 3 seeds × 1M steps = 6M environment steps。

## 证据边界

P1F 只证明损失可微、梯度路径有效、接口无投递真值泄漏且主对照公平。它不证明概率区间已经校准，不证明 PPO 能学会上下文条件策略，也不证明候选优于 recurrent 对照。

## 可追溯文件

- actor：`algorithms/epistemic_commitment.py`
- 目标函数：`algorithms/epistemic_commitment_objective.py`
- 审计：`scripts/audit_epistemic_commitment_p1f_objective.py`
- 测试：`tests/test_epistemic_commitment_p1f_objective.py`
- 机器结果：`docs/strong_q2_clean_sheet_p0_20260909/P1F_RESULT.json`
