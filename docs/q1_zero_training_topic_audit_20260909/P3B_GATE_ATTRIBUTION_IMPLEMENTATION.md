# P3B：belief/gate 与 PPO 归因实现状态

**状态：** `P3B_GATE_AND_VALUE_COMPONENTS_PASS_RUNNER_PENDING`

## 1. 已实现部分

`algorithms/active_diagnosis/pilot_gate_adapter.py` 提供：

- 两模式 Bayesian belief 及 ACK/no-ACK 更新；
- entropy reduction gate；
- decision-relevant task-regret gate；
- belief 与 gate 运行态序列化；
- 外部 gate option 与低层 actor 动作的显式分离；
- per-agent `actor_control_mask`。

## 2. PPO 归因合同

外部 gate 强制中继机探测或攻击机 fallback 时：

1. `executed_action` 记录真实送入环境的 option；
2. `sampled_policy_action` 保留低层 actor 从 27 个飞行动作中产生的 shadow action；
3. 被 gate 接管的 agent-time 样本，其 `actor_control_mask=0`；
4. PPO actor loss 只使用 `sampled_policy_action` 且乘 control mask；
5. critic 仍使用真实 executed transition 的完整 reward 与 return；
6. option 执行期间，低层 actor 获得仅含 neutral flight action 的有限 shadow distribution，避免把被 mask 的 option 送入 `Categorical.log_prob`。

因此，强制动作不会被伪装成 actor 的随机样本，也不会产生 `-inf` log-probability。

## 3. 已通过性质

- 平衡先验下 DVOI gate 选择探测；
- 高置信先验下 entropy gate 仍因标签不确定性选择探测，而 DVOI gate 因任务遗憾不足选择 fallback；
- no-ACK 正确更新 hard-failure belief 并触发 fallback；
- 强制探测只把中继机 control mask 置零；
- 强制 fallback 只把攻击机 control mask 置零；
- belief/gate checkpoint 恢复精确；
- option-active 环境 mask 可转换成有限的低层 shadow-policy mask。

## 4. 尚未解决的关键项

DVOI 当前接受调用方提供的 `task_values[hypothesis, recovery_action]`。单元测试中的常数只用于验证数学和控制流，**禁止进入性能 pilot**。

正式 pilot 前必须实现 task-value estimator：

- 训练时可用模拟器故障标签监督候选模式价值，但不得把真实模式输入 actor；
- 部署时对每个候选模式分别查询价值，再按 belief 计算 DVOI；
- entropy 与 DVOI arm 必须携带同一估计器、接收同一训练信号，entropy arm 只是不使用其输出做 gate；
- 估计器、优化器、replay/normalization 状态必须完整序列化；
- 需要检查估计误差是否足以改变 gate 决策，而不能只报告 MSE。

`algorithms/active_diagnosis/task_value_estimator.py` 现已实现上述 estimator、归一化、监督 replay 和 checkpoint 合同；`algorithms/active_diagnosis/recurrent_sg_mappo.py` 现已实现共享 role-graph GRU actor、snapshot centralized critic、时间顺序重放、回合槽位清零、truncated BPTT 和 control-mask PPO actor loss。

独立技术审计在 32 步×2 环境的合成序列上通过，且 task-value estimator 的合成监督误差没有改变 0.50/0.90 两个冻结先验下的 gate 决策。这里的合成 target 只验证可训练性、序列化和决策敏感性，**不是环境任务价值证据，也禁止作为 pilot 输入**。

尚未完成的是统一 outer runner：它必须从真实完整 episode return 形成 estimator 监督，保存 sampled/executed action 双轨迹，计算真实 executed transition 的 critic/GAE，并把三 arm、环境运行态、gate/belief、estimator replay 和所有 RNG 纳入同一 checkpoint。故当前 `performance_pilot_authorized=false`。
