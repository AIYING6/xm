# Q0-S1：Structured / Agent-Scoped Robust MARL 直接近邻红队

状态：`Q0_S1_NO_GO__LATENT_UNCERTAINTY_SCOPE_NOT_DISTINCT`

日期：2026-08-11

## 1. 候选问题

候选设定为：部署期间存在隐藏变量

\[
z_t=(\text{uncertainty type},\text{affected-agent subset},\text{severity}),
\]

不同 agent 只能通过自己的合法历史部分推断当前 uncertainty scope，团队同时进行 scope inference 与 robust coordination。

## 2. 直接近邻红队

| 近邻 | 已覆盖内容 | 对候选的影响 |
|---|---|---|
| Shi et al., ICML 2024 | 分布鲁棒 Markov games；每个 agent 具有自己的 prescribed uncertainty set，并给出 robust equilibrium 与 sample-efficient 算法。 | “agent-specific uncertainty” 本身不能作为创新。<https://proceedings.mlr.press/v235/shi24d.html> |
| He et al., state-uncertainty MARL | 将状态扰动建模为每个 agent 关联的 perturbation adversary，并给出 robust Q-learning / actor-critic。 | 受影响 agent 子集和 agent-local uncertainty 已有直接建模先例。<https://arxiv.org/abs/2307.16212> |
| Zhou et al., stochastic adversary | 处理随机 adversary 下的 cooperative MARL 鲁棒性。 | “扰动对象随机变化”与 latent scope 的部分语义已有覆盖。 |
| NeurIPS 2025 robustness/resilience study | 大规模比较 13 类 uncertainty，并显式区分 single-agent 与 all-agent scope，报告 robustness 不跨 modality/scope 稳定泛化。 | 证明 scope/modality 现象真实，但主要是测量和经验发现，不形成候选算法缺口。<https://papers.neurips.cc/paper_files/paper/2025/hash/3e8d9bf1dd1eb9d3d9d500fb3543c87b-Abstract-Conference.html> |
| POMDP / Dec-POMDP belief methods | 隐藏 mode、局部历史和在线 belief inference 是标准部分可观测决策建模。 | 将 scope 设为隐藏变量后，候选机制容易退化为“belief reconstruction + robust policy”。 |

## 3. 关键判定

候选的最强表述是：

> centralized training 可见 uncertainty realization，但 decentralized execution 只能从局部历史推断受影响 agent subset，并据此协调。

这确实比统一 observation noise 更具体；但当前红队没有找到足够清楚的结构性算法缺口，原因有三：

1. agent-specific uncertainty sets 已被 robust Markov game 文献直接纳入；
2. state perturbation adversary 与随机 adversary 已覆盖受影响对象变化的主要建模形式；
3. 把 scope 变成隐藏变量后，剩余困难可自然归入 Dec-POMDP belief inference，再与 robust control 组合，尚未形成区别于已有 robust-POMDP / robust-MARL 的独立学习对象。

“现有工作通常不显式输出一个 scope posterior”不足以构成新颖性；输出形式变化不能替代机制差异。

## 4. 裁决

> `Q0_S1_NO_GO__LATENT_UNCERTAINTY_SCOPE_NOT_DISTINCT`

因此不进入 Q0-S2 数学形式化，不写代码、不训练，也不在当前 UAV 平台制造 latent scope 任务。当前 robust MARL 候选关闭。

## 5. 项目边界

本裁决不否定 robust MARL 的研究价值，只否定当前这个“latent agent-scoped uncertainty inference”作为新算法主线的资格。若继续寻找算法问题，应进入第三候选，并保持“文献缺口先于环境构造”的顺序。

