# DRTP Warm-Restart Maturity Extension Amendment

## 0. Scope, supersession, and status

**FROZEN WARM-RESTART AMENDMENT / NO 3M->5M TRAINING AUTHORIZED BY THIS DOCUMENT ALONE.**

This amendment replaces only the 3M-to-later-budget execution rule in
`DRTP_SG_MAPPO_TRAINING_MATURITY_ADDENDUM.md`. It is bound to verified 3M archive
SHA256 `2025d3d1b49718e727eb97c87982501eb15b1a7d3c94a33a586082f6da4be1c1`
and to the four source checkpoints in
`DRTP_SG_MAPPO_DEVELOPMENT_PERFORMANCE_REPORT.md`.

It changes neither DRTP/UTR, the 7 topology groups, the 50% nominal anchor, the
116,728-parameter matched SG, PPO, S2 task, reward, failure semantics, actor
information boundary, evaluation tape, seed set, or development retention
threshold. It changes only post-3M continuation provenance and persistence.

## 1. Checkpoint warm restart, not strict resume

The four source checkpoints are:

| arm | seed 1901 SHA256 | seed 1902 SHA256 |
|---|---|---|
| UTR-SG | `d1f97ed242176b145a0ebadebfc62e4c852c08d703b1f24f8913d1c89e5709ae` | `dd2b105f0163d1ff33ecc7d28a498f50211b63e74ca08d567bebfe165aa5c657` |
| DRTP-SG | `d09b9243a5d78818603f3b32b31e62da0c4f58a01459694a1bd2e3b9c5812e3a` | `d0b3131e94b88703ec3e9cadc3c46d7eb152133cce55164c8e33321a88f71109` |

Every source training-state file must declare update `11,719`. A warm restart
may restore only model parameters, PPO optimizer state, update counter, and
DRTP's uniquely recoverable final logged `q`, EMA, difficulty, and adaptation
count. It cannot recover environment runtime state, current observations, exact
Python/NumPy/PyTorch/CUDA RNG states, per-environment episode counters, or
per-group completed returns in the active DRTP adaptation window.

Consequently, 3M->later training is formally a **checkpoint warm restart**.
All four arms recreate environments symmetrically and clear the sampler
adaptation window. The frozen restart RNG seeds, shared by UTR and DRTP, are:

| training seed | restart RNG seed |
|---:|---:|
| 1901 | 9301901 |
| 1902 | 9301902 |

No score, arm identity, or historical result may alter this mapping. The warm
restart is not an algorithmic improvement and performance changes across it may
not be attributed to DRTP.

## 2. Restarted maturity clock

The pre-restart 2.5M->3M change is excluded from all later plateau calculations.
The post-restart maturity clock begins at 3M and uses these common milestones:

| label | global update | environment steps |
|---|---:|---:|
| source boundary | 11,719 | 3,000,064 |
| 3.5M | 13,672 | 3,500,032 |
| 4M | 15,625 | 4,000,000 |
| 4.5M | 17,578 | 4,499,968 |
| 5M | 19,531 | 4,999,936 |

At 5M, apply the existing frozen plateau threshold only to `4M->4.5M` and
`4.5M->5M`: pooled `J_OOD_worst` relative change below 5% in both intervals, no
two-seed substantial positive growth, no two-seed latest increase above about
10%, and no material structural change in nominal, F0, OOD mean, safety, or
exposure.

If immature, all four arms may strictly continue together at common 6M, 7M, 8M,
9M, and at most 10M budgets. No later warm restart is permitted. At 10M,
unresolved maturity is reported and work stops.

## 3. Runtime-state persistence after warm restart

Every post-restart milestone/final checkpoint must save:

- model, PPO optimizer, global/update step;
- Python, NumPy, PyTorch CPU, and CUDA RNG states;
- every environment's mutable state and RNG state;
- current observation, shared observation, graph observation, and any
  normalization state if present;
- per-environment episode counters and active episode returns;
- active DRTP selections, `q`, EMA, difficulty, adaptation count, and complete
  adaptation-window per-group return values/counts;
- all state required to reproduce the following rollout/update.

Before any 3M->5M launch, a save->reload->next-update deterministic continuation
test must pass. It compares uninterrupted and reloaded trajectories at the next
update, including model, optimizer, sampler, selected conditions, and logs.

## 4. Fairness and stop condition

UTR/DRTP x seed1901/1902 always use the same restart mapping, milestones, common
final budget, evaluation tape, and unmodified retention matrix. Maturity PASS
and development retention PASS are both required before held-out work can be
proposed; held-out remains separately authorized. Canonical seeds `0–4` remain
prohibited.

This phase stops after the amendment, runtime-state persistence implementation,
and deterministic continuation test report pass. It does not authorize the
3M->5M long-training launch.
