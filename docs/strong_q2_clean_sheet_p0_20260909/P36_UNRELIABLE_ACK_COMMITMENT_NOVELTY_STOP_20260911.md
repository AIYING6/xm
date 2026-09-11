# P36 不可靠确认下的协同任务承诺：新颖性与可识别性 STOP

## 审查对象

P36 由 P0H 候选一演化而来：在不可靠确认条件下，让异构团队在
`commit / defer / fallback` 之间作一致任务承诺。它没有进入环境设计或训练。

## 已核对的直接近邻

1. Schroeder de Witt et al., *Multi-Agent Common Knowledge Reinforcement
   Learning*, NeurIPS 2019：以共同知识及其层级策略树处理去中心化协调。
2. *Asking for Information by Evaluating the Communication and Coordination
   Trade-Off in Multi-Agent POMDPs*, IEEE RA-L：直接研究通信受限时，信息请求
   的决策价值与协同一致性。
3. 项目内部 P3/P3B 与 P35 零训练审计：在现有可复用资产中，主动信息取得并
   未形成持续的、会改变最优任务行动的决策价值；P35 的证据年龄门槛亦未通过。

## 判断

P36 的问题表述可以成立，但其方法对象与共同知识、概率共同知识、通信—协调
权衡和不一致信念下的行动一致性高度重叠。若仅将其投射到 UAV 任务，实质贡献会
退化为现有信息结构方法的场景应用。

同时，当前资产没有证据说明“不可靠确认”会产生一个不同于 P3/P35 的、持续且
不可由固定安全降级规则消除的任务决策缺口。因此，继续实现环境只会把新颖性风险
与可识别性风险后移到昂贵训练阶段。

## 决策

`P36_STOP_BEFORE_ENVIRONMENT`。

不得以改名为 common-belief、commitment-aware、ack-aware 或 risk-sensitive
coordination 的方式重新启动。只有在未来发现一个**非通信中心的**任务对象，且其
最优行动依赖于不可由共同知识/固定规则涵盖的资源或时序约束时，才可作为新的候选
重新进入零训练审查。
