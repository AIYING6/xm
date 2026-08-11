# New Algorithm Project Q0

状态：`Q0_STANDARD_BENCHMARK_FIRST__LITERATURE_SCREENING_RUNNING`

## 目标

在不继续改造当前 UAV 平台的前提下，筛选一个能够形成应用型算法论文的 MARL 问题。当前 UAV 平台只作为后续验证环境，不作为新问题的来源。

## 筛选门

候选问题必须同时满足：

1. 有明确、可引用的近期文献缺口；
2. 能在标准 benchmark 上先验证问题真实存在；
3. 能提出一个结构清楚的算法机制，而非模块堆叠；
4. 有强 comparator 与可预注册的机制指标；
5. 通过后才能迁移到 UAV。

## 初始候选池

| 候选 | 初始问题 | 当前风险 |
|---|---|---|
| P1 | policy improvement 破坏已有 competent behavior 的多智能体稳定优化 | demonstration regularization / KL policy constraint 近邻较多，必须证明机制差异 |
| P2 | latent agent-scoped uncertainty 下的 cooperative robust control | robust MARL 与 adversarial MARL 近邻密集，需证明 scope inference 不等价于普通 POMDP belief |
| P3 | unseen partners / heterogeneous-team zero-shot coordination | 2024–2025 已有多个直接方法与 benchmark，创新门槛高 |

## Q0 出口

- `Q0_PASS__CANDIDATE_READY_FOR_STANDARD_BENCHMARK_AUDIT`
- `Q0_PARTIAL__NOVELTY_OR_BENCHMARK_FIT_UNCLEAR`
- `Q0_NO_GO__NO_ALGORITHM_PROJECT_IDENTIFIED`

最多保留一个候选进入 benchmark phenomenon audit；不为了凑数保留三个。

## 当前边界

- 不复活 v1.6R 的 TEAR、EG-BR、R3 retention 或旧 EA-RG headline；
- 不在当前 UAV 环境上继续调算法；
- 不租正式训练资源；
- 不把 literature proximity 误写成 novelty；
- 若 Q0 失败，直接停止算法搜索并保留平台资产。
