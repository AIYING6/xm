# 00 Scope

## Manuscript type

Algorithmic MARL research paper with a topology-robustness task formulation and explicit training-seed reliability analysis.

## Primary reader

Researchers in multi-agent reinforcement learning, graph-based coordination, resilient multi-UAV systems, and communication-constrained autonomy.

## One-sentence argument

在异构多无人机协同中，中继节点故障可能在合法直连信息仍存在时重构通信路径和任务支持关系；DRTP-SG-MAPPO 通过在固定 nominal anchor 下自适应调整拓扑扰动组权重，在历史配对证据中提高了平均和中位鲁棒性能，但该收益对训练随机初始化敏感，因此必须与 seed-level reliability 和安全边界共同报告。

## Reader-question sequence

1. Relevance: relay-node failure changes coordination structure rather than merely adding observation noise.
2. Novelty: DRTP changes the topology-condition training distribution without changing the SG actor/critic.
3. Trust: UTR and DRTP are matched, all seeds and historical failures are retained, and evaluation validity is audited.
4. Reuse: the topology groups, nominal anchor, bounded weighting, PPO contract, and evaluation estimands are reproducible.
5. Meaning: adaptive weighting has high average upside but is not seed-stable or deployment-validated.

## Scope boundary

- frozen 3-UAV heterogeneous simulation;
- relay-node-induced topology/path reconfiguration;
- nominal, F0, timing, duration, and compound conditions;
- training seed as the independent statistical unit;
- no scalability, HIL, real-flight, or universal-robustness claim.
