# UTR technical definition

## Exact object audited

UTR is the collection rule used by the corrected six-UAV baseline in P2.13:

\[
g_t \sim \mathrm{Uniform}(\mathcal G),\qquad
\mathcal G=\{\text{nominal},R_{upstream},R_{downstream},C_{relay-node},C_{balanced},C_{cross},C_{same-relay}\}.
\]

Thus every reset/update draws one of the seven frozen topology conditions with probability
`1/7`; the nominal condition is included once, not over-sampled. The condition is injected
at the fixed fault time through the existing environment interface. UTR does **not** add a
network, a message channel, a reward, a PPO loss, a replay priority, an adaptive curriculum,
or an evaluation-time decision rule.

The implementation evidence is `scripts/run_redundant_topology_uav_p2.py:24-55` and
`scripts/run_redundant_topology_uav_p2_13.py:60-105`. The learner is the corrected
role-specific SG-MAPPO learner; it is held fixed between Plain and UTR.

## Information boundary

The sampler uses only training RNG and the frozen group set. It does not read the
development tape, held-out conditions, returns, TD errors, gradients, seed labels, or
checkpoints. Evaluation occurs after training with a frozen tape, and the training seed is
the independent unit.

## What it is and is not

- It is a **structured topology randomization training protocol**.
- It is not, by itself, a new policy-optimization algorithm.
- It is not an adaptive adversary, PLR, EPOpt, CVaR objective, group-DRO objective, or
  learned communication architecture.
- It may be a useful strong/simple baseline within a benchmark whose condition set has
  defensible physical, legal, and recoverability semantics.

