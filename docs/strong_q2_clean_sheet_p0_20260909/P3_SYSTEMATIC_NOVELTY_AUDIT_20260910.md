# P3 系统新颖性审计

## 决策

`NOVELTY_COLLISION_STOP`

当前 CEC-MAPPO 不进入实现和训练。停止原因不是任务不可学习，也不是代码失败，而是当前方法
创新核与公开最近邻工作发生实质重叠，无法在训练前证明其具有强二区所需的不可替代差异。

## 检索范围与失败记录

检索时间：2026-09-10。检索主题覆盖：不一致信念、共同知识、延迟通信与等待、信息价值、
conformal prediction、风险约束承诺、探测/回退和多机器人动作一致性。优先核验 arXiv、
NeurIPS、PMLR、OpenReview 与 IEEE 页面。

`nature-academic-search` 的 OpenAlex 回退检索因 HTTP 429 未完成。因此本审计不能声称穷尽
全部数据库；但停止决策不依赖“未发现相同工作”，而依赖已经找到的正面冲突，故该失败不
影响 STOP 结论。若未来提出新机制，仍须补 CrossRef/Scopus 去重与全文复核。

## 最近邻证据

| 工作 | 已公开能力 | 对当前候选的影响 |
|---|---|---|
| MACKRL, NeurIPS 2019 | 利用 common knowledge 组织去中心化协同 | 共同知识/一致性表示不是新颖点 |
| VoI macro-actions, NeurIPS 2020 | 根据信息价值决定闭环观察与开环执行 | defer 的信息价值不是新颖点 |
| DACOM, AAAI 2023 | 学习等待消息的时间，权衡等待成本和通信收益 | 等待消息不是新颖点 |
| Action-Consistent MR-BSP, 2024/2025 | 不一致信念下验证联合动作；失败时触发通信 | 动作一致性与选择性通信高度重叠 |
| Dec-POMDP action consistency, 2025 | 不一致信念下给出动作一致性与性能概率保证 | “概率保证的有限通信协同”已有直接先例 |
| SafeCommit, 2026 | 校准潜在世界集合；全支持承诺证书；否则探测或回退 | 击穿当前 CEC-MAPPO 的核心组合 |

## 为什么 UAV/MAPPO 实现不足以挽救新颖性

CEC-MAPPO 当前主张的关键链条是：从合法历史估计潜在一致状态，构造 conformal 集合，在
集合支持上审查 commit，并在不满足时 defer 或 fallback。SafeCommit 已公开相同层级的
决策抽象，并明确连接校准覆盖与不安全承诺概率。将对象从记忆型代理改为 UAV，把优化器接到
MAPPO，能够形成新的实证应用，但不能单独构成强方法创新。

四格消融可以回答“集合输入和门控在本实现中是否贡献性能”，但不能回答“该方法结构是否由
本文首次提出”。因此，先完成 100M 训练再依靠效果差异证明创新的路径被禁止。

## 可保留资产

- P3 Q0/Q0B 已核验的信息缺口与 `commit/defer/fallback` 任务构造；
- 合法局部信息边界、ACK 版本和消息年龄接口；
- 配对种子、固定评估带、可靠性端点和四格可识别性设计；
- 校准覆盖、错误承诺率、fallback/defer 使用率等指标合同。

这些资产可用于新问题，但不得把 CEC-MAPPO 名称和当前公式直接换皮重启。

## 重开条件

下一候选必须在零训练阶段同时满足：

1. 新机制的优化对象不是“对校准集合做安全承诺”；
2. 多智能体耦合不是仅把单体证书逐智能体应用；
3. 与 DACOM、MR-BSP action consistency、SafeCommit 可写出形式化差异；
4. 至少有一个无法由 recurrent MAPPO、point belief gate 或 SafeCommit-style filter解释的
   预测；
5. 在代码实现前冻结对应反事实消融和失败判据。

在这五项满足前，`training_authorized=false`。
