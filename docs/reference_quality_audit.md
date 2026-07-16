# 参考文献质量审计

日期：2026-07-13

目的：把论文引用从“能支撑写作”推进到“可投稿审稿”的质量。当前策略是用正式会议/期刊文献支撑基础方法和 MARL 背景，用近期 arXiv 文献支撑趋势和问题动机，但不让未正式发表的近期文献承担核心理论依据。

## 1. 基础方法引用

| 文献 | 论文中作用 | 来源质量 | 当前处理 |
|---|---|---|---|
| Schulman et al., PPO, 2017 | PPO/MAPPO 优化基础 | arXiv，但为公认基础方法 | 保留，作为 PPO 原始方法引用 |
| Lowe et al., MADDPG, NeurIPS 2017 | CTDE actor-critic 背景 | 正式会议 | 保留，支撑多智能体 actor-critic 背景 |
| Foerster et al., COMA, AAAI 2018 | 多智能体信用分配背景 | 正式会议 | 保留，支撑 credit assignment 讨论 |
| Sunehag et al., VDN, AAMAS 2018 | 值函数分解背景 | 正式会议 | 保留，说明另一类 CTDE 路线 |
| Rashid et al., QMIX, ICML 2018 | 值函数分解强基线背景 | 正式会议 | 保留，说明 value-based MARL 代表方法 |
| Yu et al., MAPPO, 2021/2022 | 本文主要强基线 | arXiv，注明 NeurIPS 2022 Datasets and Benchmarks | 保留，作为 MAPPO 强基线依据 |

## 2. 图表示与通信引用

| 文献 | 论文中作用 | 来源质量 | 当前处理 |
|---|---|---|---|
| Velickovic et al., GAT, ICLR 2018 | 图注意力基础 | 正式会议 | 保留，支撑注意力聚合机制 |
| Singh et al., IC3Net, 2018 | 学习通信/通信门控背景 | arXiv/会议版本需后续再核 | 保留为背景，不承担主创新依据 |
| Malysheva et al., MAGNet, 2020 | 图网络用于 MARL 的相关工作 | arXiv | 保留为相关工作，后续可替换更强正式文献 |
| Liu et al., GNN meets MARL survey, 2024 | GNN+MARL 近期综述 | arXiv | 只用于趋势概述 |
| Cuzin-Rambaud et al., GNN communication survey, 2026 | GNN 通信近期综述 | arXiv | 只用于最新趋势概述，投稿前再次核对状态 |

## 3. UAV 近期文献引用

| 文献 | 论文中作用 | 来源质量 | 当前处理 |
|---|---|---|---|
| Feng et al., GAT-based RL for multi-UAV communication, 2024 | UAV+GAT+MARL 近例 | arXiv | 用于说明应用趋势 |
| Kim et al., UAV-aided MEC MADRL, 2024 | UAV+MARL 应用近例 | arXiv | 用于说明应用趋势 |
| Zhao et al., UAV cooperative pursuit-evasion, 2024 | UAV 追逃近例 | arXiv | 用于说明任务相关性 |

## 4. 投稿风险与补救

当前引用结构已经满足初稿写作，但投稿前仍建议做三件事：

1. 将 IC3Net、MAGNet 和 UAV 近期 arXiv 文献逐篇核对是否已有正式会议/期刊版本。
2. 如果目标期刊对 arXiv 引用敏感，保留 PPO/MAPPO 这类必要基础引用，但把 UAV 近期文献替换或补充为 IEEE/Elsevier/Springer 正式发表文献。
3. Related Work 中避免把 2024/2026 arXiv 综述作为“权威结论”，只写作趋势线索；核心依据仍放在 PPO、MADDPG、COMA、VDN、QMIX、GAT 和本文实验结果上。

## 5. 当前结论

文献基础已经比上一版更稳：MARL 背景不再只依赖 MAPPO 与若干近期 arXiv 文献，而是补上了 PPO、MADDPG、COMA、VDN、QMIX 这条基础链。下一步应继续补 UAV 有限通信、协同追逃、安全约束相关的正式期刊文献，并把引用压实到 Introduction 和 Related Work 的每个主张上。
