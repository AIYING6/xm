# P0D：强二区候选机制卡

## 评价维度

每个候选按五项判断：问题是否非平凡、是否有唯一可控干预、仓库是否已有反证、最近邻是否拥挤、是否能以现有资产低成本验证。

## A. 拓扑条件信用分配

- 科学对象：通信拓扑变化下 centralized critic 的归因偏差。
- 优点：理论叙事强，与 CTDE 的信息不对称直接相关。
- 致命问题：仓库已完成 counterfactual critic、group-gradient 与 trust-region 类尝试，并得到重复 NO-GO；外部研究也已有 relation-aware credit、graph-conditioned value decomposition 与 asymmetric critic 分析。
- 决策：`NO_GO_ARCHIVE_AND_OVERLAP`。

## B. 合法拓扑转变记忆

- 科学对象：当前图快照不足时，对历史拓扑转变进行合法记忆。
- 优点：动态故障叙事自然。
- 致命问题：本仓库已有 TATG/snapshot-GRU 路线；继续推进会成为已有路线改名。动态通信、信息瓶颈和 recurrent partial-observability 文献也较拥挤。
- 决策：`NO_GO_ALREADY_ATTEMPTED`。

## C. 在线故障信念或主动诊断

- 科学对象：隐故障条件下的 belief inference 与策略适应。
- 优点：问题高度高于采样器。
- 致命问题：当前故障拓扑直接进入图关系张量，故障并非充分隐藏；若改为隐故障并增加诊断动作，将同时改变 observation、transition 与 action interface，无法最大复用现有正式对照。已有 Bayesian MARL、fault estimator 与 active communication defence 研究形成直接邻域。
- 决策：`NO_GO_CURRENT_CONTRACT`。

## D. 同物理状态下的拓扑干预一致性

- 科学对象：在固定物理状态下改变通信边，约束策略只对任务相关的信息路径变化作出反应。
- 可用资产：`algorithms/ri_gmappo/simple_ri_gmappo.py` 已支持同 base-id 的 paired intervention probe；`envs/uav_intercept_3d_env.py::_get_graph_obs` 显式生成当前通信、感知和 task-support 关系。
- 非平凡性审查：
  1. 若两次干预产生完全相同的合法 actor 输入，则策略输出一致是确定性网络的恒等事实，不构成算法。
  2. 若 actor 输入不同，则必须先定义哪些变化是“任务无关”以及期望动作应保持何种关系；当前合同没有独立于回报的 oracle 标注。
  3. 若用未来回报或成功标签定义相关性，会把事后结果泄漏到训练目标，并退化为一般 invariant/causal representation learning。
  4. 当前图编码器已通过 `adj` / `relation_adj` 门控消息传播，最朴素的断连无关性已有结构保证。
- 决策：`NO_GO_UNIDENTIFIED_OR_TRIVIAL`。

## P0D 综合结果

四个候选均不能在“保持当前环境与动作接口、最大复用资产、低试错”约束下形成新的强二区主线。继续从现有 DRTP 周围寻找正则项、critic 或记忆模块，边际收益低于选题风险。

