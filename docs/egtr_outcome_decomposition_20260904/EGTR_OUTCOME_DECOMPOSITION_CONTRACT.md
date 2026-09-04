# EGTR outcome decomposition contract

## Scope

This post-hoc audit reads only the completed simultaneous EGTR double-cohort 10M training
artifacts and fixed final evaluation summaries. It asks whether EGTR's existing training-only
sampler telemetry contains a **cross-cohort repeated association** with final EGTR-minus-UTR
perturbed return.

## Prohibitions

The audit must not alter EGTR, UTR, Original DRTP, checkpoints, sampler logs, evaluation tape,
seed registry, reward, PPO, environment, numerical threshold, or final double-cohort verdict.
It cannot authorize EGTR-v2, a parameter sweep, training, evaluation, checkpoint selection, or
automatic continuation.

## Decision boundary

The audit reports a feature only if it has the same within-cohort Spearman direction and
absolute correlation at least `0.8` in both separate five-seed cohorts. This is deliberately
hypothesis-generating rather than confirmatory: `n=5` per cohort cannot establish a causal
mechanism. Absence of such a feature is a reason not to propose a telemetry-directed successor.

