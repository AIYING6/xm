# P0D：最近邻与新颖性压力审查

## 审查结论

本轮检索没有发现一个既未被仓库历史覆盖、又能在当前固定接口内被唯一识别的机制缺口。相反，四个候选均受到成熟邻域挤压。

| 邻域 | 代表性原始来源 | 与候选的关系 | 风险 |
|---|---|---|---|
| 图结构通信学习 | [Learning Structured Communication for MARL](https://arxiv.org/abs/2002.04235) | 学习分组、路由和图消息传播 | “拓扑感知”本身不足以构成新颖性 |
| 跨规模图策略 | [Learning Transferable Cooperative Behavior in Multi-Agent Teams](https://arxiv.org/abs/1906.01202) | agent-entity graph、规模不变与迁移 | 单纯 GNN/规模泛化叙事拥挤 |
| 因果通信 | [Fully Decentralized Multiagent Communication via Causal Inference](https://ieeexplore.ieee.org/document/9761961/) | 用 counterfactual influence 选择通信 | 反事实通信归因已有直接邻居 |
| 动态通信 | [Dynamic Communication in MARL via Information Bottleneck](https://ieeexplore.ieee.org/document/10901017/) | 动态拓扑、部分不可达、通信效率 | 动态拓扑与 bottleneck 不是空白 |
| 有噪通信联合决策 | [Effective Communications](https://ieeexplore.ieee.org/document/9466501/) | 将消息作为动作并显式建模 noisy channel | 若扩展通信动作，需要与该类工作比较 |
| 不变 RL 表征 | [Invariant Causal Prediction for Block MDPs](https://proceedings.mlr.press/v119/zhang20t.html) | 多环境干预下学习回报相关不变表征 | 一致性正则需要可识别假设和环境干预条件 |
| 干预式因果表征 | [Interventional Causal Representation Learning](https://proceedings.mlr.press/v202/ahuja23a.html) | 依赖明确干预与可识别条件 | 不能仅凭 paired simulation 使用“causal”表述 |
| 图拓扑与领域知识 | [Knowledge-Driven MARL for Computation Offloading](https://arxiv.org/abs/2308.02603) | 将通信拓扑知识和置换不变性注入 GNN | 结构先验 + GNN 的方法包装风险高 |

## 对当前候选的表述上限

- paired topology intervention 最多能证明策略对指定模拟干预的敏感性差异。
- 除非给出可识别的结构因果模型、干预集合和独立标签，否则不能声称学到了因果拓扑表征。
- 除非通信/路由成为策略可控变量，否则不能声称解决了 topology repair 或 communication reconfiguration。
- 图掩码下的消息阻断属于架构性质，不是新训练机制的经验发现。

