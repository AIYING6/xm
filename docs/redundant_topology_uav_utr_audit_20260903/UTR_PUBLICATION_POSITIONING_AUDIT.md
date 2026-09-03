# 6-UAV UTR novelty and external-comparator audit

## Scope

This is a zero-training paper-positioning audit. It modifies no environment, learner, training
rule, evaluation tape, seed register, or experiment result.

## Evidence consulted

- Implementation: `scripts/run_redundant_topology_uav_p2.py` and
  `scripts/run_redundant_topology_uav_p2_13.py`.
- Learnability: P2.13 final result, where corrected Plain and UTR reached nominal success
  `1.0` for each of five fresh training seeds, and UTR reached Tier-R success `1.0` for each.
- Negative ablation: P3-P2 static schedule, which yielded `P3_P2_NO_SIGNAL` with a mean
  all-group success delta of `-0.4` against UTR.
- Literature: domain randomization, EPOpt, PLR, group-DRO, structured communication MARL,
  and fault-tolerant UAV MARL. Exact sources appear in
  `UTR_NEAREST_NEIGHBOR_COMPARISON.csv`.

## Finding

Uniform topology randomization is a sound transparent baseline, but it is technically a finite,
structured form of domain randomization. The current evidence supports task learnability and
the practical usefulness of UTR on its frozen main-scale conditions. It does not yet support a
generic method-novelty, external superiority, held-out robustness, or cross-scale claim.

## Publication recommendation

Position the work as a **redundant-topology UAV benchmark and reproducible strong simple
baseline**, with a clearly described topology-failure taxonomy. Do not title or market the work
as “UTR: a new robust MARL algorithm.” A later framework claim should be conditional on the
minimum external-comparator plan and held-out/scale evidence.

