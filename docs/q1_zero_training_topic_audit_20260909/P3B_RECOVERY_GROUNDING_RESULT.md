# P3B：恢复决策语义落地审计

**状态：** `P3B_RECOVERY_GROUNDING_PASS`

## 1. 为什么需要这一步

P3A 只证明探测动作可以接入 PPO。如果没有至少两个会因潜在故障模式而改变优先级的合法恢复选择，DVOI 中的“决策相关”只能依赖人为标签，不能支持新算法主张。因此在实现三个训练 arm 前，先把恢复选择落到真实 3DOF 转移中。

## 2. 冻结的潜在模式与恢复选择

两种模式在初始 actor 输入上逐元素一致：

1. `recoverable_range_loss`：中继--攻击机链路因距离暂时不可用，合法握手机动可恢复 ACK；
2. `hard_terminal_comm_failure`：攻击机通信接口硬失效，相同机动不能恢复 ACK，但攻击机仍可依靠任务先验接近目标并在物理可见范围内自主感知。

两个恢复计划：

- `immediate_fallback`：攻击机立即执行 24 步先验引导搜索 option；
- `probe_then_condition`：中继机先执行 12 步握手；收到 ACK 后继续信息支撑任务，未收到 ACK 时切换到同一个 fallback option。

探测在环境回报中承担固定 `0.12` 任务效用成本；它不是免费信息动作。

## 3. 零训练结果

审计入口：`scripts/audit_active_diagnosis_p3b_recovery_grounding.py`。

结果文件：`artifacts/active_diagnosis_p3b/P3B_RECOVERY_GROUNDING_RESULT.json`。

- 四个“模式 × 计划”轨迹均完成任务；
- 无 timeout、collision 或 constraint violation；
- 探测结果严格区分两种模式；
- 条件化计划只在硬通信故障下调用 fallback；
- 平衡先验下，条件化计划相对立即 fallback 的平均回报差为 `+0.053384`。

共执行 88 个环境步；没有训练或 PPO 更新。

## 4. 解释上限

该审计证明真实转移中存在一个**带成本但具有正期望任务价值的决策相关探测问题**。它不证明学习策略能够发现该行为，也不证明当前脚本控制器应成为最终算法组件。脚本只用于冻结语义和排除“探测无对应恢复动作”的伪问题。

## 5. 下一门槛

下一步实现 P3B policy/gate adapter，必须解决：

1. 外部 gate 强制 option 时不把强制动作伪装成 actor 采样动作；
2. PPO actor loss 对强制 option 使用明确的 control mask，critic 仍学习全部时间步回报；
3. entropy 与 DVOI arm 共享 belief、观测核和低层策略，仅 gate 目标不同；
4. DVOI 所需任务价值不能长期依赖本审计的脚本常数，pilot 前必须给出可训练、可序列化且不读取部署真值的估计器合同。

完成这些实现门之前，性能 pilot 仍未授权。

