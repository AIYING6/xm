# P0E 证据边界与下一轮搜索合同

## 已核验事实

- `envs/uav_intercept_3d_env.py`：角色与能力、奖励及合法信息路径耦合；通信由环境转移实现，不是 agent action。
- `configs/b_line_p1_formal_problem_novelty_freeze.json`：原生 relay/routing control 缺失。
- `docs/q1_zero_training_topic_audit_20260908/c0r/C0R_RESULT.json`：主动感知—路由—服务重构已完成严格近邻与理论靶点审查并关闭。
- `docs/tatg_mappo_p0_20260904/TATG_P0_RESEARCH_CONTRACT.md` 与 `configs/tatg_mappo_p1_information_gap_freeze.json`：合法历史信息缺口已经被定义并推进为 TATG 路线。

## 外部新颖性压力

- [Attention-Based Recurrence for MARL under Stochastic Partial Observability](https://proceedings.mlr.press/v202/phan23a.html)：直接覆盖 stochastic partial observability 下的 recurrent MARL。
- [Enhancing Cooperative MARL with State Modelling and Adversarial Exploration](https://proceedings.mlr.press/v267/kontogiannis25a.html)：覆盖 belief/state modelling 与信息性探索。
- [Learning to Explore in POMDPs with Informational Rewards](https://proceedings.mlr.press/v235/xie24a.html)：覆盖信息获取奖励与部分可观测探索。
- [Multi-agent Bayesian DRL under Communication Failures](https://arxiv.org/abs/2111.11868)：覆盖通信失败下的 belief-based multi-agent decision making。
- [Graph-Attention-Based RL for Multi-UAV Trajectory and Resource Assignment](https://ieeexplore.ieee.org/document/10522499/)：覆盖 multi-UAV 轨迹与资源分配联合学习。

## P0F 搜索范围

下一轮不得再以“通信故障 + 某个通用 MARL 模块”为模板。应跨出当前问题族，优先搜索以下三类高价值对象：

1. **可验证的部署风险边界**：对拓扑退化策略给出有限样本风险校准或失效检测，而不是再训练一个更复杂策略；
2. **跨任务/跨平台拓扑鲁棒性基准**：将现有单环境结论扩展为可迁移的评价问题，但必须至少有第二个标准环境，不能只换 UAV 数量；
3. **离线故障数据下的受约束策略适应**：以不能重新采集大量故障轨迹为核心限制，研究少样本/离线适应，而不是 sampler 重加权。

P0F 只做文献与可行性审查。每类必须找到：一句可检验命题、最近邻、最小资产复用路径、P1 无训练反例或数据审计，以及预计总训练量。未通过不得编码。

