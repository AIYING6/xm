# P1：主动故障辨识的可辨识性与接口门

**日期：** 2026-09-09

**当前裁决：** `P1A_ANALYTIC_PASS_P1B_INTERFACE_PENDING`

## 1. 已通过的解析反例

`scripts/audit_active_diagnosis_identifiability_p1.py` 对冻结配置
`configs/active_diagnosis_p1_counterexample.json` 执行了零训练计算。结果写入
`docs/q1_zero_training_topic_audit_20260909/P1_IDENTIFIABILITY_RESULT.json`。

平衡先验下：

- 不探测的最优期望效用为 1.20；
- 付出 0.20 成本后探测，再按回执选择动作的期望效用为 1.46；
- 主动辨识价值为 +0.26；
- 探测观测在两个假设下的总变差距离为 0.80；
- 在先验 0.05 和 0.95 时，探测均损失 0.20，说明“始终探测”并非支配策略。

因此，最小问题同时满足：被动观测等价、最优动作冲突、探测提高可分性、探测成本非零以及探测应按 belief 选择。

这只证明问题在数学上非平凡，不证明现有 UAV 环境已经具备相同结构，也不证明任何学习算法有效。

## 2. P1B 冻结接口草案

### 2.1 潜在失效原因

只保留两类足以形成反例的原因，避免建立故障百科：

1. `recoverable_range_loss`：中继因几何位置/有效通信范围失去链路，进入握手区可恢复；
2. `hard_relay_failure`：中继通信节点失效，即使进入握手区仍无法恢复。

故障发生后的前置窗口中，两类原因必须产生相同的 actor 可见字段：当前消息缺失、消息年龄、当前 delivered adjacency 和缓存状态。故障原因、故障 mask、随机数状态和评估标签只允许进入 evaluator，不进入 actor/critic 的部署侧输入。

### 2.2 动作

采用双层动作而不是把 27 个飞行动作任意扩成几十个组合：

- `task_control`：现有转向、爬升和加速离散动作；
- `mode`：`continue_task`、`handshake_probe(peer)`、`degrade_task`。

`handshake_probe` 是持续固定短时长的 macro-action：低层控制器把中继引导至冻结握手区并发起确认。它只能通过普通通信回执产生信息，不返回故障标签；同时累计真实时间和能量成本。`degrade_task` 切换到不依赖中继的低收益任务合同，但不能凭空恢复原协同链。

### 2.3 观测与 belief

部署侧仅允许：

- 当前自身动力学状态；
- 当前合法局部感知；
- 已实际接收的消息、回执和消息年龄；
- 自身历史动作与 macro-action 状态。

训练时 centralized critic 可使用全局物理状态，但不得向 actor 蒸馏故障真值。belief 更新器可在训练时用故障标签监督校准，但主实验必须另含不使用标签监督的版本或清楚限定适用条件。

### 2.4 安全与预算

- probe 必须经过原有碰撞、边界、最小高度和载荷约束；
- 每回合 probe 次数设硬上限，而非只靠 reward 惩罚；
- task、diagnosis、energy/time 与 safety 指标分开报告；
- 不能用更长 episode horizon 补偿探测成本。

## 3. 外部基准选择

冻结两级验证：

1. **Multi-Agent Tiger / POSGGym 兼容实现**：验证 belief、主动观测和停止/执行权衡；它是算法 sanity benchmark，不承担 UAV 工程外推。
2. **异构 UAV 主环境**：验证物理探测动作、协同恢复、时间/能量代价和安全边界。

不再把自定义 MPE wrapper 称为独立标准环境；只有在 Multi-Agent Tiger 无法接入现有训练骨干时，才将 MPE 作为工程适配测试，而不是第二条主证据。

## 4. P1B 必须通过的环境级单元测试

在任何 PPO 训练之前必须有以下确定性测试：

1. 同一初始状态和随机带下，两类故障在 probe 前产生逐字段相同的 actor observation；
2. handshake probe 后的回执分布在两类故障间可区分；
3. probe 不读取 evaluator-only fault label；
4. probe 消耗冻结步数和能量；
5. probe 轨迹满足动作与安全约束；
6. oracle、always-probe、never-probe 和 belief-rule policy 的解析排序与反例一致；
7. 保存/恢复环境状态后，probe 结果与 RNG 轨迹完全一致。

## 5. 当前禁止事项

- 不实现神经网络算法；
- 不启动训练；
- 不把解析 +0.26 写成实验收益；
- 不把 Multi-Agent Tiger 的 listen 动作包装成本文创新；
- 不使用“首次”“保证恢复”或“解决通信故障”；
- 不允许在环境实现后连续修 reward 直到方法获胜。

## 6. 下一步

下一步只实现最小环境语义和上述七项单元测试，阶段名：

`P1B_ACTIVE_DIAGNOSIS_ENVIRONMENT_SEMANTIC_GATE`。

只有全部通过，才设计算法；失败则关闭该方向，不消耗 GPU。
