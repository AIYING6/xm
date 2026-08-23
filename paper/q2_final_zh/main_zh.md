# 中继节点故障下异构多无人机拓扑鲁棒协同：自适应扰动训练的平均收益与种子敏感性

> **状态：** 结构化中文主稿骨架。正文撰写必须遵守本目录的 research canon、evidence table、section contracts 和 terminology ledger。

## 摘要

`[最后撰写：问题 → 缺口 → DRTP → matched UTR 证据 → seed sensitivity → 有界意义]`

## 关键词

异构多无人机；多智能体强化学习；通信拓扑；中继节点故障；拓扑扰动训练；训练可靠性

## 1 引言

### 1.1 应用背景与结构性问题

`[说明异构角色、通信与任务支持关系为什么共同决定协同能力。]`

### 1.2 现有研究缺口

`[区分随机噪声、信息丢失与合法路径重构；引出 topology robustness。]`

### 1.3 本文方法与研究问题

`[说明 matched SG、UTR 与 DRTP；不写详细结果数字。]`

### 1.4 贡献

`[三项：问题、方法、验证/可靠性。禁止稳定性或首次性夸张。]`

## 2 相关工作

### 2.1 图结构多智能体强化学习

`[按拓扑表示与消息传播机制组织。]`

### 2.2 鲁棒与分布变化下的多智能体学习

`[按不确定性类型与优化目标组织。]`

### 2.3 通信受限与故障条件下的多无人机协同

`[按通信优化、拓扑变化和任务级鲁棒性组织。]`

### 2.4 本文定位

`[说明为什么 TAPE/M3DDPG 相关但不是公平 drop-in；回到 matched UTR ablation。]`

## 3 问题建模

### 3.1 异构角色与 3DOF 环境

### 3.2 通信–任务图与合法信息边界

### 3.3 Relay failure 与拓扑路径重构

### 3.4 Nominal、F0 与 OOD 条件

### 3.5 性能、安全与 exposure estimands

## 4 方法

### 4.1 Matched Single-Graph MAPPO

### 4.2 Uniform Topology Randomization

### 4.3 DRTP bounded adaptive weighting

### 4.4 Nominal competence anchor

### 4.5 训练流程、复杂度与信息边界

## 5 实验协议

### 5.1 方法与公平性合同

### 5.2 Development 与 held-out 分层

### 5.3 Evaluation tapes 与 failure conditions

### 5.4 指标与统计单位

### 5.5 Safety、pre-trigger termination 与 risk-set validity

## 6 结果

### 6.1 Relay failure 的拓扑/路径机制

### 6.2 Development 3M 绝对结果

### 6.3 Held-out 10M 绝对结果

### 6.4 Paired seed effects 与 reliability

### 6.5 Timing、duration 与 compound OOD

### 6.6 Timeout、collision、constraint 与 exposure validity

### 6.7 机制遥测及其解释边界

## 7 讨论

### 7.1 自适应扰动加权带来的平均收益

### 7.2 为什么平均收益不等于 seed-stable superiority

### 7.3 与现有 topology-aware / robust MARL 的关系

### 7.4 局限性

`[必须包含 seed sensitivity、mixed safety、无公平 external drop-in、3-UAV simulation、无 scalability/HIL。]`

## 8 结论

`[贡献 → 决定性证据 → 有界意义 → 明确边界。]`

## 数据与代码可用性

`[AUTHOR INPUT NEEDED：仓库、归档、匿名化及公开计划。]`

## 作者贡献、利益冲突与资助

`[AUTHOR INPUT NEEDED]`
