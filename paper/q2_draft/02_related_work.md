# 2. Related Work

## Robust multi-agent reinforcement learning

Robust MARL has considered continuous-action coordination under changes in other agents' policies and adversarial variation. Such work motivates robustness as a multi-agent learning objective, but the perturbation studied here is a relay-node-induced change in a legal communication–task graph. The distinction is important: the present task does not replace the mission with an adversarial game or assume that robustness can be summarized by a worst-case opponent.

## Topology-aware and communication-aware MARL

Topology-aware policy-gradient methods explicitly model agent relationships, while communication-aware UAV methods often optimize connectivity, relay selection, power, or information exchange. These studies establish the relevance of graph structure to coordination. Our focus is narrower and more operational: a fixed heterogeneous UAV mission undergoes a physically defined Relay failure, and the evaluation follows the resulting path and task-support reorganization across canonical and OOD conditions.

## Distributionally robust and adaptive environment weighting

Distributionally robust RL formalizes performance under distributional or model shifts, including worst-case distributional optimization and robust Markov decision processes. DRTP is deliberately more modest. It is an empirical bounded weighting strategy over seven predeclared topology-perturbation groups, with unchanged PPO and no claim of a general DRMDP guarantee. The paper's contribution is therefore the combination of topology-specific problem semantics, adaptive exposure, and reliability-aware evaluation rather than a new general robust-RL theorem.

Representative primary sources include [Robust Multi-Agent Reinforcement Learning](https://aima.eecs.berkeley.edu/~russell/papers/aaai19-marl.pdf), [TAPE](https://ojs.aaai.org/index.php/AAAI/article/view/29699), [Distributionally Robust Q-Learning](https://proceedings.mlr.press/v162/liu22a.html), [On the Foundation of Distributionally Robust Reinforcement Learning](https://arxiv.org/abs/2311.09018), [Fast connectivity restoration of UAV communication networks](https://doi.org/10.1016/j.adhoc.2025.103785), and [Multi-hop UAV relay covert communication](https://doi.org/10.1016/j.cja.2025.103440). Their different environments and objectives are why none is used as a drop-in external comparator in the current contract.
