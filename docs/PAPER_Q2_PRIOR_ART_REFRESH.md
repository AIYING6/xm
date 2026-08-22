# PAPER-Q2 Prior-Art Refresh

**Generated:** 2026-08-22. Focused refresh only; no new algorithm search or training authorization.

## Positioning map

1. **Robust MARL under policy/environment variation.** Robust MARL work has addressed continuous-action multi-agent robustness and adversarial or opponent-policy changes. This establishes that robustness in MARL is broader than communication topology failure, so the paper must state its event semantics precisely. Primary source: [Robust Multi-Agent Reinforcement Learning](https://aima.eecs.berkeley.edu/~russell/papers/aaai19-marl.pdf).
2. **Topology-aware coordination.** TAPE explicitly uses agent topology in cooperative policy-gradient learning. The present distinction is not “graphs are new”; it is relay-node-induced path reorganization in a heterogeneous UAV mission plus reliability-aware evaluation. Primary source: [TAPE: Leveraging Agent Topology for Cooperative Multi-Agent Policy Gradient](https://ojs.aaai.org/index.php/AAAI/article/view/29699).
3. **Distributionally robust RL.** Distributionally robust Q-learning and later DRRL theory optimize against distributional/environmental shifts. DRTP should be positioned as an empirical, bounded topology-group weighting mechanism, not as a general DRMDP solution or theoretical worst-case guarantee. Primary sources: [Distributionally Robust Q-Learning](https://proceedings.mlr.press/v162/liu22a.html) and [On the Foundation of Distributionally Robust Reinforcement Learning](https://arxiv.org/abs/2311.09018).
4. **UAV relay and communication MARL.** Recent UAV relay work uses MARL for connectivity, trajectory, power, or covert communication objectives. These motivate the application context but do not by themselves establish the specific relay-failure/path-reconfiguration estimand used here. Primary sources: [Fast connectivity restoration of UAV communication networks](https://doi.org/10.1016/j.adhoc.2025.103785) and [Multi-hop UAV relay covert communication](https://doi.org/10.1016/j.cja.2025.103440).

## Novelty boundary

Do not claim the first topology-aware MARL, first robust MARL, first DRRL, or first UAV relay MARL. The defensible contribution is the integrated problem formulation, legal topology/path mechanism audit, bounded adaptive weighting across predefined perturbation groups, and an unusually explicit seed-level reliability/safety evaluation.
