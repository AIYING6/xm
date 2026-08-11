# V2-R1：多任务异构 UAV 直接近邻矩阵与创新边界

状态：`R1_PARTIAL__PROBLEM_COMBINATION_DISTINCT_BUT_METHOD_GAP_UNCLEAR`

日期：2026-08-11

## 1. 审查维度

矩阵同时检查：异构能力、并发多任务、multi-agent coalition、动态 assignment、high/low-level 联合、连续动力学、decentralized execution、recipient-specific 信息、range/loss/delay/staleness、物理可行性变化、task-agent 图、feasibility mask、assignment-conditioned credit，以及真实 physical completion。

## 2. Direct-neighbor matrix

| 近邻 | 异构/能力 | 动态 coalition/任务 | 高低层联合与运动 | 局部/去中心化 | 不确定/通信时效 | 与 V2 的主要差异 |
|---|---|---|---|---|---|---|
| Bezerra et al., 2024/25 | 多机器人任务分配，异构性在 coalition 中有作用 | **动态 coalition、task revision** | MAPPO + spatial action maps + motion control | **local information、intention sharing** | 未形成严格 recipient-specific delivered/cache-valid range/loss/delay 合约 | 最强直接近邻；已覆盖“局部动态 coalition + motion + MAPPO”，但其信息时效/物理 feasibility 语义需逐项核对。<https://arxiv.org/abs/2412.20397> |
| TIHDP, 2024 | 可变数量对象/机器人，任务分配 | 动态 task priority | **三层：allocation → priority → robot control** | allocation/control 受 local observation/action 限制；priority 可用 global object info | 非 V2 的 packet/cache/staleness 合约 | 层次接口已被明确研究；V2 不能把 hierarchy 本身作为创新。<https://arxiv.org/abs/2404.02362> |
| ATA-HRL, ICRA 2025 | team heterogeneity | initial allocation + condition-triggered reallocation | HRL | 面向动态 operational state 与 information uncertainty | 不等同于 recipient-specific packet provenance/age | 已覆盖“异构 + 动态重分配 + 信息不确定”；V2 必须有更窄的结构差异。<https://arxiv.org/abs/2409.13824> |
| CASH, CoRL 2025 | **capability-aware heterogeneous coordination** | 可适应未见机器人/团队组成 | policy architecture，不是 V2 的 physical multi-task loop | 重点是共享权重与泛化 | 非 V2 communication contract | capability encoding / shared policy 不能作为核心创新。<https://proceedings.mlr.press/v305/fu25a.html> |
| MOHITO, UAI 2025 | agent/task 关系 | task-open、任务集合动态变化 | actor-critic + task/action hypergraph | 不以 V2 的连续 3DOF 执行链为核心 | 非 V2 的 packet/cache 语义 | task-open / dynamic task graph / hypergraph 不能单独宣称创新。<https://proceedings.mlr.press/v286/anil25a.html> |
| HYGMA, 2025 | agent group coordination | dynamic grouping | hypergraph coordination | 重点是 agent state-history grouping | 非 V2 的 task feasibility + physical completion | dynamic grouping/hypergraph 已有直接先例。<https://arxiv.org/abs/2505.07207> |
| Huang et al., 2026 | speed-heterogeneous quadrotor swarm | multi-task assignment | **hierarchical allocation + trajectory optimization** | 以 topology/clustering/MILP 为主，不是 decentralized MAPPO | chance constraints；非 recipient-specific packet/cache | 已覆盖异构 UAV 多任务分配与连续轨迹耦合；其 centralized optimization 与 V2 decentralized learning 有差异。<https://link.springer.com/article/10.1007/s44443-026-00797-1> |
| heterogeneous UAV CDTA, 2023 | heterogeneous UAV | dynamic task reallocation | MARL allocation | proposer-responder distributed mechanism | uncertainty，但非 V2 strict packet semantics | UAV 动态任务分配本身不是新问题。<https://doi.org/10.1109/TVT.2022.3228198> |

## 3. 当前可保留的组合边界

文献矩阵尚未显示一篇工作同时明确覆盖以下完整组合：

> capability-feasible multi-agent coalition + physical-state-dependent feasibility + strict recipient-specific delayed/stale task evidence + decentralized joint allocation and continuous 3DOF execution + physical task endpoint。

这说明 V2 的**问题组合**仍可能与近邻不同。但这不是方法创新结论：Bezerra 已经覆盖 local dynamic coalition + motion control，TIHDP 已覆盖层次 allocation/control，ATA-HRL 已覆盖 heterogeneity + dynamic reallocation + uncertainty，2026 UAV 工作已覆盖 heterogeneous multi-task allocation + trajectory optimization。

## 4. R1 裁决

> `R1_PARTIAL__PROBLEM_COMBINATION_DISTINCT_BUT_METHOD_GAP_UNCLEAR`

不能进入 R2，也不能实现 R0 环境。下一步最多进行一次**方法边界重构**：必须把 V2 的核心机制从“任务分配 + 层次控制 + capability graph”进一步收窄为一个与上述最强近邻可区分的机制。若做不到，直接 `R1_NO_GO`；不得继续增加模块或扩充文献审计轮次。

## 5. 明确禁止的创新表述

* 首次异构多 UAV 任务分配；
* 首次 dynamic coalition / task reallocation；
* 首次 hierarchical allocation + motion control；
* 首次 capability-aware graph/hypergraph；
* 首次将 MAPPO 用于多机器人任务分配。

