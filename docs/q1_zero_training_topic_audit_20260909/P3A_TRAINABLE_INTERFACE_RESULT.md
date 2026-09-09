# P3A：可训练接口门结果

**状态：** `P3A_TRAINABLE_INTERFACE_PASS`

## 1. 本阶段回答的问题

P3A 只检查主动诊断问题能否以合法、可训练且不泄漏故障真值的方式接入现有多智能体 PPO 管线。它不是性能实验，也不提供算法优越性证据。

## 2. 新增接口

`envs/active_diagnosis_trainable_uav_env.py` 以 opt-in wrapper 方式复用 `UAVIntercept3DEnv`，没有修改旧环境的转移、奖励或动作语义。

- 原有 27 个离散 3DOF 飞行动作保持不变；
- 新增第 28 个动作 `handshake probe`，仅中继机可选；
- 探测 option 固定执行 P1C 已验证的 12 步物理机动；
- option 执行期间，中继机动作掩码只允许继续探测；
- 每回合最多一次探测，完成后预算永久关闭；
- actor 只看到 `probe_available`、`probe_active` 和已经发生的 ACK 状态，不看到潜在故障标签；
- graph actor 使用三架蓝方 UAV 的合法局部观测、角色、当前通信邻接和动作掩码；中央 critic 沿用全局状态接口，但没有新增故障真值字段。

## 3. 可执行证据

审计入口：`scripts/audit_active_diagnosis_p3a_trainable_interface.py`。

结果文件：`artifacts/active_diagnosis_p3a/P3A_RESULT.json`。

通过项：

1. 标准 `reset/step` 张量形状有效；
2. recoverable range loss 与 hard relay failure 在探测前的全部 actor 输入逐元素相同；
3. actor/graph 字段不含故障真值；
4. 探测动作仅中继机可用且受一次性预算约束；
5. 12 步探测在回合终止前完成，并产生 `ACK=+1` 与 `no ACK=-1` 的可辨识结果；
6. masked SG-MAPPO rollout 未产生非法动作；
7. 单次 PPO 数值烟测的 loss 与梯度有限；
8. 模型与环境运行态恢复逐元素一致。

审计共执行 32 个 smoke environment steps 和 1 次 PPO smoke update；`performance_training_started=false`。

## 4. 证据边界

该结果证明“训练接口可行”，不证明：

- 1M steps 足够学习任务；
- DVOI gate 优于 entropy gate 或 recurrent baseline；
- 探测一定提高任务回报；
- 潜在故障模型覆盖真实通信故障；
- 方法具有跨任务、跨规模或实机泛化能力。

## 5. 决策

P3A 允许进入 P3B 的**零训练对照冻结与实现审计**。在三个 arm 的输入、容量、override 语义和统计合同全部实现并通过之前，不启动 9M-step pilot。

