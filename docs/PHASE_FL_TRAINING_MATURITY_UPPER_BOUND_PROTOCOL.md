# Phase FL — Training-Maturity Upper-Bound Experiment Protocol

## Status

```text
Purpose: training-maturity ceiling only
New algorithm: prohibited
New diagnosis: prohibited
Training: authorized
TP-2: NO-GO
```

This experiment tests whether the current matched Single-Graph experts improve with a materially longer fixed budget. It does not select a checkpoint, change the method, or create a new robustness claim.

## Fixed arms and seeds

- `fl_nominal_expert`: 100% nominal training condition;
- `fl_f0_expert`: 100% frozen F0 training condition;
- seeds: `1801,1802`;
- four total runs, all from scratch.

Both arms retain the current matched Single-Graph architecture (`116,728` parameters), PPO implementation and hyperparameters, environment, reward, observation, actor information boundary, training pool, and F0 semantics. No curriculum, auxiliary loss, recurrent module, or architecture change is permitted.

## Budget and rollout contract

The current rollout contract is preserved:

```text
4 environments × 64 rollout steps × 3907 updates = 1,000,192 env steps
```

`1,000,192` is the nearest complete-update budget to the requested one-million-step ceiling; no partial rollout is introduced. The final update is the only final checkpoint used for evaluation.

## Milestone checkpoints

Milestones are saved only for learning-curve analysis and are never eligible for checkpoint selection:

| Label | Update | Actual env steps |
|---|---:|---:|
| `300k` | 1172 | 300,032 |
| `500k` | 1953 | 499,968 |
| `750k` | 2930 | 750,080 |
| `1m` | 3907 | 1,000,192 |

The `1m` final checkpoint is evaluated. The earlier milestones are used only to summarize training curves.

## Evaluation contract

All final evaluations use the existing FL diagnostic tape `370000–370049`, under nominal and F0 failure conditions. No new tape, seed, endpoint, environment, or evaluation protocol is introduced.

Report per seed and pooled:

- `J_nominal`, `J_failure`, `Delta_J`;
- training curves and finite PPO diagnostics at all four milestones;
- collision, timeout, constraint violation;
- episode length;
- communication path, topology, task-support, legal-information and cache-age telemetry.

The earlier milestones cannot be promoted based on their scores. If the final 1m checkpoint is weak, the experiment reports that result; it does not trigger automatic retraining or checkpoint replacement.
