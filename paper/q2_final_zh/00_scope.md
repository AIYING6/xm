# 00 Scope

## Manuscript type

Algorithmic MARL research paper with a topology-robustness task formulation and explicit training-seed reliability analysis.

## Primary reader

Researchers in multi-agent reinforcement learning, graph-based coordination, resilient multi-UAV systems, and communication-constrained autonomy.

## One-sentence argument

在异构多无人机协同中，中继节点故障可能在合法直连信息仍存在时重构通信路径和任务支持关系；DRTP-SG-MAPPO 通过在固定 nominal anchor 下自适应调整拓扑扰动组权重，并由一项前瞻性、参数匹配、五训练 seed 的 10M-step 实验检验其相对 UTR 的收益、风险与可重复性；历史证据提示其具有较高平均收益但存在训练 seed 敏感性，因此正式结论必须同时报告中心效应、逐 seed 方向和安全边界。

## Reader-question sequence

1. Relevance: relay-node failure changes coordination structure rather than merely adding observation noise.
2. Novelty: DRTP changes the topology-condition training distribution without changing the SG actor/critic.
3. Trust: UTR and DRTP are matched in a prospective five-seed 10M-step test; all formal seeds and historical failures are retained, and evaluation validity is audited.
4. Reuse: the topology groups, nominal anchor, bounded weighting, PPO contract, and evaluation estimands are reproducible.
5. Meaning: adaptive weighting has high average upside but is not seed-stable or deployment-validated.

## Scope boundary

- frozen 3-UAV heterogeneous simulation;
- relay-node-induced topology/path reconfiguration;
- nominal, F0, timing, duration, and compound conditions;
- training seed as the independent statistical unit;
- no scalability, HIL, real-flight, or universal-robustness claim.
