# DRTP 最终证据 P0：Held-out/OOD 合同

**状态：** `P0_ZERO_TRAINING_PREFLIGHT_ONLY`。本合同冻结最终论文证据的下一步，不重新开启机制根因审计，也不修改 DRTP、EGTR 或 GA-EGTR。

## 已冻结的依据

- A、B 两个独立 10M cohort 的下载结果包是唯一输入；两包的 SHA256 已登记在 `configs/drtp_final_evidence_p0_heldout_ood_freeze_20260906.json`。
- 主方法为 Original DRTP (`drtp_sg`)，UTR (`utr_sg`) 是唯一的本阶段匹配参照。EGTR 与 GA-EGTR 的 A/B 不一致性保留在方法选择记录中，但不在本阶段继续开发或调参。
- 每个 cohort 的五个最终 checkpoint 原位使用；禁止按 return、最坏 seed、OOD 表现或任何其他结果更换 checkpoint。

## 新的未见测试

训练和 A/B 固定终点评估均只暴露了 Relay-1 的失效时间/时长变化。本 P0 新冻结一个不被训练读取的 `782000–782099` episode namespace：

| 类别 | 条件 | 未见变化 |
|---|---|---|
| 参考 | nominal | 无失效 |
| 参数 OOD | early / long Relay-1 | 只改变已知 Relay-1 失效的时间或时长 |
| 结构 OOD | Scout-0 node | 改变失效节点位置 |
| 结构 OOD | symmetric longest edge | 删除最长通信边的双向通信 |
| 结构 OOD | directed longest edge | 删除最长通信边的一个方向 |
| 结构 OOD | Scout-0 + symmetric edge | 组合节点与边拓扑变化 |

这些条件只调用已有环境的节点失效和通信拓扑接口；不改变奖励、动力学、动作空间、actor 输入维度或网络参数。P0 会先验证其观测/图接口固定、静态删边实际生效且没有把 condition descriptor 直接提供给策略。

## 解释规则

后续终点评估按 A、B 分开报告，以训练 seed 为统计单位。报告必须同时给出均值、中位数、lower tail、逐 seed 的配对方向、timeout、collision 与结构 OOD 相对参数 OOD 的表现。

这不是新的“单项硬门”。一个条件、raw range 或 SD 本身不触发算法关闭；它只约束论文主张的范围。禁止训练、重训、超参数调整、checkpoint promotion、自动启动 6-UAV 或自动算法修订。

通过 P0 只授权下一步的**冻结 checkpoint held-out/OOD 评估设计**；任何外部方法重新训练或 6-UAV 实验仍需单独执行合同。
