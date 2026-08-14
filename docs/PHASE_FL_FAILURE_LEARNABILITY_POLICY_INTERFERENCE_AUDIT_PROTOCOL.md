# Phase FL — Failure Learnability & Policy-Interference Audit Protocol

## 0. Frozen status

```text
CTP = CLOSED
TP-2 = NO-GO
Phase FL protocol = FROZEN FOR REVIEW
Training = NOT AUTHORIZED
```

This document defines a diagnostic audit. It is not a new method-selection phase and it does not authorize training by itself. No Schedule D, robust loss, recurrent module, architecture change, reward change, environment change, or failure-semantic change is permitted under this protocol.

## 1. Single diagnostic question

The audit answers only:

> Can the existing matched Single-Graph policy learn the frozen F0 failure condition when nominal episodes are removed from its training distribution?

The purpose is to distinguish failure learnability from interference between nominal and failure competence. It must not be used to manufacture a positive robustness claim.

## 2. Fixed arms and seeds

The diagnostic uses the same matched Single-Graph architecture for both arms:

| Arm | Training distribution | Role |
|---|---|---|
| `fl_nominal_expert` | 100% nominal episodes | Same-seed nominal reference |
| `fl_f0_expert` | 100% frozen F0 failure episodes | Failure-only learnability expert |

Seeds are fixed to new diagnostic seeds `1801` and `1802`. These seeds were not used for prior method or curriculum selection. Each arm therefore has exactly two runs, for four total runs.

The two arms must share the same:

- Single-Graph architecture and parameter count (`116,728`);
- PPO implementation and hyperparameters;
- environment, reward, observation, actor information boundary, and training pool;
- rollout geometry (`4` environments × `64` steps);
- training budget (`1,172` updates = `300,032` environment steps);
- from-scratch initialization rule;
- final-checkpoint-only evaluation rule.

The only training-distribution difference is nominal versus F0 exposure.

## 3. Frozen F0 condition

The failure-only expert uses the existing S2 F0 semantics exactly:

```text
failed relay agent = 1
failure onset      = t=44
failure duration   = 80 steps
failure timing     = deterministic
failure sampling   = 100% F0
```

No timing randomization, duration randomization, curriculum schedule, failure-probability change, or alternative failure condition is allowed.

The nominal expert uses the same environment with the frozen nominal condition and no relay failure. It is a reference arm, not a proposed method.

## 4. Training and checkpoint contract

Both arms must satisfy:

- train from scratch;
- exactly `300,032` environment steps;
- exactly `1,172` updates;
- no resume;
- no early stopping;
- no best-checkpoint selection;
- no checkpoint promotion;
- evaluate only the fixed final checkpoint;
- no canonical seeds, canonical results, or paper headline evaluation.

Any violation invalidates that run as FL evidence; the run must not be silently repaired or substituted.

## 5. Independent diagnostic evaluation tape

FL uses a new paired diagnostic tape, separate from all previously used tapes. The reserved FL namespace is:

```text
paired episode IDs: 360000–360049
conditions: nominal and relay_failure
episodes per condition: 50
```

The tape must be generated, hashed, and frozen before any FL evaluation. It must bind the same exogenous episode realization for the nominal/failure pair, including initial state, target realization, action/noise realization where applicable, failure node/time, and environment randomness. The tape must not reuse IDs or realizations from `340000–340099` or `350000–350049`.

Both FL arms must be evaluated on exactly the same tape. The tape is diagnostic-only and must not be reused as canonical evidence.

## 6. Primary estimands

For every arm and seed, report seed-level means for:

```text
J_nominal
J_failure
Delta_J = J_nominal - J_failure
```

Also report paired episode-level values and:

- collision rate;
- timeout rate;
- constraint-violation rate;
- failure exposure;
- episode length;
- failure onset and terminal reason;
- communication path/topology telemetry;
- task-support source and path-switch telemetry where available;
- final finite PPO diagnostics and learning-curve summaries.

The primary comparison is between the two experts on the same seed and the same FL tape. `J_failure` is the main learnability diagnostic; `J_nominal` is the specialization/competence diagnostic.

## 7. Pre-registered interpretation rule

FL does not require a pre-specified victory margin, statistical significance, or paper-level superiority. Results are classified by the frozen qualitative pattern below, using pooled means plus seed-wise direction. With two seeds, all conclusions remain diagnostic and uncertainty must be reported.

### A — Failure learnable; shared-policy interference indicated

Assign A when the F0-only expert has a higher failure score than the nominal reference in the pooled result and the direction is consistent across both diagnostic seeds, while nominal competence is not materially reduced.

Interpretation: the failure condition is learnable by the existing SG backbone, and the earlier mixed-condition degradation is consistent with nominal–failure policy interference or optimization interference.

### B — Failure not shown to be learnable under the current formulation

Assign B when the F0-only expert does not improve the failure score over the nominal reference in the pooled result, or the seed-wise directions do not provide consistent evidence of improvement.

Interpretation: under the current observation, reward, policy class, and budget, failure competence has not been demonstrated. The next investigation must target partial observability, temporal dependence, message age/staleness, and post-failure action bottlenecks—not another curriculum or robust-loss proposal.

### C — Failure learnable with nominal–failure specialization trade-off

Assign C when the F0-only expert improves failure score with consistent seed-wise direction, but its nominal score is materially lower than the nominal reference.

Interpretation: the SG backbone can specialize to failure, but nominal and failure competence occupy a visible Pareto trade-off. A later constrained-robust-optimization proposal may be considered only after a separate protocol is written and authorized.

If the result lies near a tie or has contradictory safety/telemetry evidence, report the closest pre-registered category together with `diagnostic uncertainty`; do not create a new method or alter the category after seeing the result.

## 8. Prohibited actions

The following are prohibited during FL:

- changing the S2 environment, reward, failure semantics, actor boundary, or observation;
- adding curriculum, robust loss, auxiliary loss, recurrent memory, or architecture modules;
- changing seed `1801/1802`, budget, tape, or checkpoint rule;
- selecting checkpoints from the learning curve;
- excluding a seed or episode;
- using success as a substitute for `J_nominal`, `J_failure`, or `Delta_J`;
- using canonical seeds or canonical evaluation;
- launching TP-2 or any CTP continuation;
- making a paper headline claim from FL.

## 9. Required artifacts

Before any later authorization, the FL executor must produce:

```text
docs/PHASE_FL_FAILURE_LEARNABILITY_POLICY_INTERFERENCE_AUDIT_REPORT.md
results/development/phase_fl_failure_learnability/
  manifest.json
  tape_manifest.json
  runs/fl_nominal_expert/seed1801/
  runs/fl_nominal_expert/seed1802/
  runs/fl_f0_expert/seed1801/
  runs/fl_f0_expert/seed1802/
  per_seed_summary.csv
  paired_episode_metrics.csv
  learning_curve_diagnostics.csv
```

The final report must state exactly one of A, B, or C, preserve all raw episode rows and checkpoint hashes, and explicitly confirm whether training and evaluation contracts were respected.

## 10. Authorization boundary

This protocol freezes the diagnostic design only. It does not authorize the four FL training runs. A separate explicit authorization is required before generating the FL tape, launching training, or evaluating checkpoints.
