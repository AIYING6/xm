# Selective-KLR Intervention Utility Audit: P0 contract

**Status:** `ZERO_TRAINING_ONLY`  
**Scope:** This contract audits whether the archived Full-Rollback KLR runs can support an exact, historical accept-versus-rollback counterfactual. It neither changes DRTP nor authorizes a new algorithm, rollout, evaluation, seed, or cloud run.

## Scientific question

The closed Full-Rollback KLR rule used an empirical post-step KL threshold of `0.02` as both an alarm and a mandatory action. P0 asks a narrower question:

> Does the archive retain enough state at every alarm to determine, from the same pre-trigger state, whether accepting or rolling back that particular actor update would have had greater short-horizon utility?

The question is not whether a seed was ultimately good or bad, and it must not use final return labels to choose historical triggers.

## Exact historical counterfactual requirements

For every post-step `KL > 0.02` trigger, an exact historical A/B branch would require all of the following at the instant immediately before the guarded actor update:

1. actor and critic parameters;
2. actor and critic optimizer states;
3. sampler, Python, NumPy, CPU/CUDA Torch and minibatch RNG states;
4. vector-environment runtime state and pending rollout state;
5. the exact rollout tensor and old log-probabilities used for the attempted update;
6. the current update/epoch position and the future minibatch order;
7. a trigger identifier linking the state to the corresponding telemetry row.

Milestone runtime checkpoints cannot substitute for these artifacts: a KL trigger can occur between milestones, and rewinding from a later milestone would no longer compare the same intervention.

## Frozen interpretation rules

- All `KL > 0.02` events in the inspected archive are the population; no seed, trigger, condition, or threshold may be selected after inspecting final outcomes.
- Training seed remains the independent replication unit. Trigger events within one seed are technical events, not independent scientific samples.
- A future utility branch, if separately authorized, must begin from a copied pre-trigger state. The rejected branch must never add data to the official PPO buffer.
- Future branch-selection utility must be calculated on a training-only paired probe or a fixed short continuation that is disjoint from the formal evaluation tape.
- A prospective audit must report the extra probe/branch interactions and compute cost. It cannot claim equal training budget merely because the official trajectory still has the original number of environment steps.

## P0 outcomes

| Outcome | Meaning | Authorized consequence |
|---|---|---|
| `HISTORICAL_EXACT_COUNTERFACTUAL_FEASIBLE` | every trigger has all seven pre-trigger artifacts | prepare a read-only historical branch protocol; no algorithm yet |
| `HISTORICAL_EXACT_COUNTERFACTUAL_NOT_FEASIBLE` | one or more required pre-trigger artifacts are absent | do not fabricate a historical A/B result; only a separately authorized prospective instrumentation study can answer the question |

## Prohibitions

- no KLR-v2, Selective-KLR, threshold sweep, branch-horizon sweep, or reward/PPO/sampler change;
- no rerun of seed3701--3710 to recreate a preferred trigger;
- no claim that a trigger-specific causal mechanism has been established from final seed outcomes;
- no use of this B-line work in the frozen A-line manuscript.
