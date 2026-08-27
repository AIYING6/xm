# 26 新颖性与既有方法定位图

**目的：** 将本文的可发表增量与已有工作清楚分开，避免把通用 MARL、图编码、PPO、鲁棒优化或 UAV 通信研究误写成本方法首创。

## 1. 本文不声称的创新

| 已有方向 | 本文的关系 | 不允许的写法 |
|---|---|---|
| PPO / MAPPO [1,10] | 共同优化器与合作 MARL 基础 | “首次将 PPO/MAPPO 用于无人机协同” |
| 图注意力 [2] | 固定 SG actor/critic 的表示组件 | “提出新的图注意力网络” |
| 拓扑感知策略梯度 [3] | 拓扑可进入协同优化的相关背景 | “首次考虑 agent topology” |
| robust MARL / DR RL [4,5] | 分布不确定性与鲁棒学习背景 | “DRTP 是一般 DRO 求解器” |
| group robustness、主动随机化和 curriculum [11--13] | 预定义组、训练分布与自适应采样的思想来源 | “首次提出困难组重加权” |
| UAV 图 MARL、抗干扰通信和中继决策 [6--9,15--16] | 应用与系统背景 | “首次研究 UAV 通信拓扑变化” |

## 2. 可辨识的任务化增量

本文的可辨识贡献只由以下组合构成：

1. **故障语义：** 在三角色异构协同任务中，将 relay failure 实现为冻结的节点/边失效窗口，同时保留物理规则允许的 Scout--Attacker 直连；研究对象是合法 communication-path composition 与 task-support source 的重构，而不是将所有信息错误地设为消失。
2. **受控因果比较：** UTR 与 DRTP 保持 SG 主干、116,728 参数、PPO、奖励、环境、七组训练 universe、50% nominal anchor、10M budget 和 paired evaluation tape 一致；实验隔离的只有六个故障组的均匀或有界自适应训练权重。
3. **有界训练分布控制：** DRTP 将故障质量限制在固定 0.50 内，对六组使用 EMA-relative difficulty、平滑和有界 simplex projection；它不向 actor 增加故障标签、最短路或仿真器真值。
4. **可靠性作为结果边界：** 以 training seed 而非 episode 为独立单位，预先固定终点并完整保留 collision--timeout 权衡、历史不利种子及独立反向 cohort，而不是只报告 pooled mean。

## 3. 证据对应与强度

| 增量 | 直接证据 | 可支持的说法 | 不能支持的说法 |
|---|---|---|---|
| 合法路径重构问题 | 环境合同、图1、路径/信息字段 | relay failure 改变合法路径与任务支持组成 | 故障后恢复了丢失的全局信息 |
| 相对 uniform 的经验增益 | 正式 2301--2305 UTR--DRTP、10M、12,000 records | 在该冻结正式 cohort 内观察到较高任务端点 | DRTP 对一切外部算法或场景优越 |
| 采样器真实工作 | q/EMA/difficulty telemetry、图6、S2--S3 | 采样器实际改变故障组暴露 | 权重改变已被证明造成特定策略行为 |
| 安全与技术有效性 | 逐 seed safety、risk-set trigger audit、S1 | timeout 减少伴随局部碰撞代价；触发器技术有效 | 所有安全端点都改善 |
| 训练可靠性边界 | 历史 strata、独立 2401--2405 三方法完整重复、S4 | 正式收益尚未跨 cohort 稳定复现 | DRTP 对随机初始化稳定优越 |

## 4. 静态非均匀对照的精确位置

独立三方法 cohort 包含固定非均匀 SNR，但它与正式主 cohort 使用不同训练种子和 evaluation tape，且 DRTP 相对 UTR 的方向在该 cohort 中反转。因此 SNR 不能被倒灌为正式主 cohort 内“online adaptation 必要性”的因果证明。该 cohort 的唯一投稿功能是完整地界定跨 cohort reliability 风险，并阻止将正式正向 cohort 夸大为一般结论。

## 5. 建议的投稿表述

允许：

> 在冻结的 relay-failure topology perturbation training contract 中，DRTP 相对于参数匹配的均匀拓扑随机化显示出经验性能提升；完整的独立重复同时表明该提升尚不具备跨训练 cohort 的稳定可复现性。

禁止：

> DRTP 首次、普适、稳定地解决了 UAV topology robustness，或 online adaptation 对任意 static nonuniform sampler 均为必要。
