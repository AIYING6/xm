# P2：决策相关主动诊断算法设计冻结

**状态：** `P2_DESIGN_FROZEN_IMPLEMENTATION_PENDING`

## 1. 设计动机

主动诊断、诊断成本和容错控制联合设计都已有成熟工作。本文不能以“更准确地识别故障”为中心，因为两个物理上不同的故障如果对应同一个最优恢复动作，继续区分它们不会提高任务价值。

本候选只辨识**会改变团队恢复决策的差异**。

## 2. 决策等价类

给定潜在模式 \(h\in\mathcal H\)、任务状态 \(s\) 和恢复动作集合 \(\mathcal U\)，定义：

\[
h\sim_s h' \quad\Longleftrightarrow\quad
\arg\max_{u\in\mathcal U}Q_{\mathrm{task}}(s,h,u)
=\arg\max_{u\in\mathcal U}Q_{\mathrm{task}}(s,h',u).
\]

策略不必恢复完整故障标签，只需维护其在决策等价类 \(\mathcal C_s=\mathcal H/\sim_s\) 上的 belief。

## 3. 任务遗憾

若真实模式已知，最优任务价值为 \(V^*(s,h)=\max_u Q_{\mathrm{task}}(s,h,u)\)。belief \(b\) 下因信息不足造成的 Bayes 任务遗憾为：

\[
\mathcal R(s,b)=
\mathbb E_{h\sim b}[V^*(s,h)]
-\max_{u\in\mathcal U}\mathbb E_{h\sim b}[Q_{\mathrm{task}}(s,h,u)].
\]

它只惩罚会导致任务动作选错的不确定性；与恢复动作无关的标签差异不产生遗憾。

## 4. 探测价值

对合法探测 option \(p\)，观测 \(y\) 更新 belief 为 \(b^{p,y}\)。决策相关探测价值定义为：

\[
\mathrm{DVOI}(p\mid s,b)=
\mathcal R(s,b)-
\mathbb E_{y\sim P(\cdot\mid s,b,p)}[\mathcal R(s',b^{p,y})]
-c_{\mathrm{time}}(p)-c_{\mathrm{energy}}(p).
\]

只在以下条件同时满足时选择探测：

1. `DVOI > 0`；
2. probe budget 尚未耗尽；
3. probe option 在冻结安全可达集内；
4. 剩余任务时限足以执行探测与后续恢复。

## 5. 算法边界

### 固定部分

- 低层 3DOF 飞行控制与 MAPPO actor/critic；
- 环境奖励、安全约束和任务预算；
- 故障先验与训练/评估 seed；
- probe macro-controller；
- 故障支持集合。

### 新增部分

- 部署合法的故障模式 belief；
- 决策等价类；
- 基于任务遗憾下降的 probe gate；
- 一次性硬 probe budget。

### 明确不做

- 不最大化故障分类准确率；
- 不把 entropy reduction 直接加进 PPO reward；
- 不让 critic 的故障真值进入 actor；
- 不学习通信路由或任务重分配；
- 不联合修改 reward、网络容量和训练预算。

## 6. P2 实现前必须通过的解析性质

1. **决策无关不变性：** 拆分或合并具有相同最优恢复动作的故障标签，不改变 DVOI；
2. **非负信息价值：** 在零探测成本且后验由正确观测核更新时，期望后验任务遗憾不高于先验；
3. **成本阈值：** 当探测成本超过最大可减少遗憾时，gate 必须拒绝探测；
4. **oracle 上界：** 候选任务价值不得超过直接观察真实模式的 oracle；
5. **无信息探测拒绝：** 两个模式下观测核相同的 probe，其 DVOI 只能为负成本或零。

这些是单元测试目标，不声称为新的理论定理。

## 7. P3 pilot 合同（仅 P2 通过后）

### 方法

1. recurrent MAPPO：匹配历史容量，无显式 belief/probe gate；
2. entropy-probe：使用相同 belief 和 probe 动作，但按熵下降选择；
3. decision-relevant probe：完整方法。

always-probe、never-probe 和 oracle 只作为解释性边界，不占正式训练 arm。

### 预算

- 3 个 fresh seeds；
- 每条最多 1M environment steps；
- 总计 9M steps；
- 固定终点评估，不按回报选 checkpoint。

### 继续条件

完整方法必须同时满足：

- 相对 recurrent MAPPO 改善任务 success/timeout 或 return，而不是只提高诊断准确率；
- 相对 entropy-probe 使用更少或不更多的探测成本取得更高任务价值；
- 3 seeds 中不得出现 probe-induced catastrophic safety failure；
- probe rate 既非 0% 也非 100%；
- 至少在平衡先验和一个偏置先验下保持正确选择趋势。

否则停止，不做 v2/v3 修补。

