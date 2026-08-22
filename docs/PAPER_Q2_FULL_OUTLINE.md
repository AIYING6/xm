# PAPER-Q2 Full Outline

**Working paper type:** algorithmic MARL research paper with a topology-robustness task and explicit reliability analysis. **Generated:** 2026-08-22

## One-sentence argument

Relay-node failure need not remove all legal information; it can reorganize communication paths and task support, and DRTP can improve average and median performance across the resulting perturbation groups, but the evidence also exposes non-negligible seed sensitivity that must remain part of the conclusion.

## Sections

1. **Introduction:** topology perturbation is a structural coordination problem; distinguish it from blackout/recovery; state the reliability question.
2. **Related work:** robust MARL, topology-aware MARL, communication-aware UAV MARL, distributionally robust RL; position DRTP as an empirical topology-group weighting mechanism, not a new universal robust-RL theorem.
3. **Problem formulation:** heterogeneous roles, communication/task graph, receiver-row adjacency, legal relay failure, nominal/F0/OOD conditions, estimands and risk-set validity.
4. **Method:** seven topology groups, 50% nominal anchor, bounded adaptive weighting, update equations, implementation mapping, no extra encoder/reward/critic information.
5. **Experimental protocol:** T1 reference; DRTP development and held-out strata; seeds, budgets, tapes, checkpoint policy, safety and exposure accounting.
6. **Results:** absolute returns first; paired deltas and seed-level dispersion; OOD decomposition; safety; mechanism telemetry.
7. **Reliability and limitations:** development NO-GO, held-out FAIL, seed1902 and seed2002, why mean/median gains cannot be called stability.
8. **Discussion:** what topology-robust MARL evidence supports, what it does not; deployment implications and reproducibility.
9. **Conclusion:** bounded claim only.

## Required result order

Absolute `J_nominal/J_F0/J_OOD` and safety first; relative deltas second; mechanism interpretation third; reliability limitation immediately adjacent, not hidden in an appendix.
