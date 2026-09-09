# P0H：强二区新课题清洁式搜索协议

**日期：** 2026-09-09  
**阶段：** 零训练选题、新颖性与可识别性审查  
**边界：** 本阶段不实现算法、不启动训练、不把 DRTP 历史收益作为新课题证据。

## 1. 为什么需要 P0H

P0D--P0G 已经系统审查并关闭了当前固定接口内的 sampler 修补、反事实 critic、group-robust PPO、拓扑记忆、通用通信请求/路由、在线角色重分配、离线适应、风险校准和主动故障辨识等方向。P3B 又在预设校准门处停止：冻结任务内没有出现 balanced prior 下的 decision-relevant probe case，因此主动诊断方法没有进入性能训练的资格。

P0H 明确放弃“几乎完全复用、低成本、容易出结果、强创新”必须同时满足的要求。新课题允许改变任务、信息结构和决策变量，只复用通用软件基础设施。

## 2. 搜索问题

检索不再围绕“怎样修 DRTP”，而围绕以下问题：

1. 动态失效下，现有 MARL 忽略了哪个可执行决策对象？
2. 该缺口能否在训练前由解析反例或环境单元测试证明？
3. 最近邻是否已经完整覆盖问题、算法对象和证据形式？
4. 若进入训练，能否构造单变量机制消融和两个评价环境？

## 3. 排除集

以下方向不再作为新候选：

- DRTP/PLR/课程式训练分布重加权；
- topology-conditioned critic、group-weighted PPO 或稳定化 gate；
- GNN、GRU、belief encoder 或 world model 的直接拼接；
- 单纯链路重建、消息补全、通信请求、路由或 AoI 优化；
- 单纯故障分类、信息增益奖励或主动诊断；
- 通用角色重分配、任务分配或 agent dropout 训练；
- Byzantine 消息过滤或普通 adversarial training；
- 仅做风险评估、benchmark 或统计校准而无新控制决策。

## 4. 来源与检索方法

采用 `nature-academic-search` 的 `multi-source-search` 工作流。优先使用公开的会议/期刊原始页面、PMLR、NeurIPS/ICLR/AAAI/IJCAI proceedings、IEEE 页面和 arXiv 原文；按 DOI 去重，缺 DOI 时按标题与首作者去重。OpenAlex fallback 因 HTTP 429 未提供结果，未使用抓取式来源填补数量。

检索簇：

- common knowledge / inconsistent belief / unreliable communication / Dec-POMDP；
- open teams / teammate change / malfunction recovery；
- decentralized world model / counterfactual planning / structural shift；
- graceful degradation / mission contract / safe fallback；
- Byzantine-resilient MARL（作为排除性近邻）；
- asynchronous macro-action coordination（作为排除性近邻）。

## 5. 放行条件

候选只有同时满足下列条件，才可进入 P1；P1 仍然不训练。

1. **新决策对象：** 一句话说明 agent 新决定什么，而不是网络新增什么模块；
2. **严格反例：** 普通 recurrent MAPPO 即使容量充足也因信息结构而不能同时实现两个最优联合动作；
3. **可控干预：** 方法和主基线之间存在可冻结的唯一主要差异；
4. **最近邻余量：** 至少有一个非措辞性的数学或执行语义差异；
5. **双环境闭环：** 一个 UAV 环境加一个社区可识别环境；
6. **非饱和任务：** 基线可学习，但存在稳定、可解释的性能缺口；
7. **成本止损：** P2 pilot 不超过 15M environment steps，正式验证原则上不超过 250M；
8. **失败即停：** 不允许通过连续改奖励、改 gate 或扫参数挽救假设。

## 6. 可复用与不可复用资产

可复用：

- `algorithms/mappo/` 与通用 PPO/并发训练骨干；
- `envs/uav_intercept_3d_env.py` 的 3DOF 动力学和安全指标；
- checkpoint、seed registry、fixed evaluation tape、provenance 和云端打包框架；
- 图数据结构及合法邻接掩码的工程实现。

不可复用为新结论：

- DRTP、EGTR、GA-EGTR、TATG、active diagnosis 的收益数字；
- 历史开发 seed 或技术无效 6-UAV 结果；
- 历史 NO-GO 机制改名后的实现；
- 旧任务上的“结果为正”作为新问题成立的先验证据。

