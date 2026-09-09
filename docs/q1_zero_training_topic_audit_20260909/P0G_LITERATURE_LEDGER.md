# P0G 文献台账（最近邻用途）

本表只用于选题排重，不构成论文最终参考文献表。日期与书目信息在正式写作前仍需逐条 DOI 核验。

| 主题 | 文献 | 对本轮判断的作用 |
|---|---|---|
| 韧性异构任务分配 | Mayya et al., *Resilient Task Allocation in Heterogeneous Multi-Robot Systems*, arXiv:2009.04593 | 排除“能力损失后重分配+优雅降级”作为干净创新 |
| 能量与故障韧性任务分配 | Notomista et al., *A Resilient and Energy-Aware Task Allocation Framework for Heterogeneous Multirobot Systems*, IEEE T-RO 38(1), 2022, DOI: 10.1109/TRO.2021.3102379 | 表明能力、组件失效、在线分配和实机验证已有强近邻 |
| 任务分配与形式化规划 | Faruq et al., *Simultaneous Task Allocation and Planning Under Uncertainty*, arXiv:1803.02906 | 排除仅用 failure-aware planning/guarantee 建立创新 |
| 任务分配与路径 | *Reinforcement learning–based task allocation and path-finding in multi-robot systems under environment uncertainty*, CA-CIE 40(22), 2025, DOI: 10.1111/mice.13535 | 表明间歇通信下 RL 任务分配/路径已被直接研究 |
| Ask-type 通信 | *Asking for Information by Evaluating the Communication and Coordination Trade-Off in Multi-Agent POMDPs*, IEEE RA-L 11(8), 2026, DOI: 10.1109/LRA.2026.3703246 | 区分“主动请求信息”与候选的“物理探测故障” |
| 主动信息获取 | Lauri et al., *Multi-Robot Active Information Gathering with Periodic Communication*, ICRA 2017, arXiv:1703.02610 | 主动探测不是新概念，候选必须聚焦协同故障辨识 |
| 主动故障诊断 | Zaccaria et al., *Fault Identification Enhancement with Reinforcement Learning (FIERL)*, arXiv:2405.04938 | 最近的主动诊断 RL 近邻；要求本项目证明多智能体任务耦合差异 |
| 分散主动假设检验 | *Deep Multi-Agent Reinforcement Learning for Decentralized Active Hypothesis Testing*, arXiv:2309.08477 | 排除把“多 agent + 主动诊断”本身当创新 |
| 鲁棒通信 MARL | Yu et al., *Robust Communicative Multi-Agent Reinforcement Learning with Active Defense*, AAAI 2024, DOI: 10.1609/aaai.v38i16.29708 | 区分被动消息可靠性加权与主动制造诊断信息 |
| MAS 模型诊断综述 | Kalech and Natan, *Model-Based Diagnosis of Multi-Agent Systems: A Survey*, AAAI 2022, DOI: 10.1609/aaai.v36i11.21498 | 显示 MAS 诊断成熟，同时指出 troubleshooting、恢复和间歇故障仍有空间 |
| 间歇通信 MARL | *Multi-agent reinforcement learning for cooperative search under aperiodically intermittent communication*, ESWA, DOI: 10.1016/j.eswa.2025.127526 | 区分丢失信息重建与故障原因主动辨识 |
| 主动诊断与最优控制联合设计 | Guo and He, *Integrated design for active fault diagnosis and fault-tolerant optimal control for stochastic systems with non-convex input constraints*, Automatica 188, 2026, DOI: 10.1016/j.automatica.2026.112960 | 说明“诊断+控制”组合本身不新；候选必须聚焦分散协同与决策相关辨识 |
| RL 主动诊断与跟踪控制 | *Reinforcement learning-based integrated active fault diagnosis and tracking control*, ISA Transactions, DOI 页面 PII: S0019057822003299 | 排除仅用 CRL 同时优化诊断和跟踪的泛化表述 |
| 带成本/收益的主动诊断 | *Active Diagnosis with Costs and Rewards*, CONCUR 2026, DOI: 10.4230/LIPIcs.CONCUR.2026.37 | 表明诊断成本和任务收益已有形式化；不能把非零 probe cost 当作独立创新 |

## 当前结论边界

现有检索只支持“尚未发现完整覆盖精确交叉点”，不支持“首次提出”。P1 必须继续围绕以下组合做定向排重：

`active fault diagnosis` + `Dec-POMDP` + `communication failure` + `embodied probing` + `cooperative control`。
