# Strict-Sensing Formal Protocol

Last updated: 2026-07-16

## Purpose

This protocol upgrades the current 10-update strict-sensing pilot into a formal experiment line.

Main claim:

```text
Under strict intermittent sensing and relay communication-node failure, the multi-relation role graph improves kill-chain recovery probability and recovery speed compared with a matched single-graph variant.
```

This protocol intentionally does not add 4v2, missiles, JSBSim, self-play, or ELO. The goal is to make the existing strict-sensing relay-failure line statistically and procedurally credible.

## Data Splits

Use three disjoint episode sets:

| Split | Purpose | Default base seed | Default episodes |
| --- | --- | ---: | ---: |
| Online monitor | NaN/crash/reward sanity only | training script internal | 5 |
| Validation | checkpoint selection and training-budget diagnosis | 120000 | 50 |
| Test | final reporting after selection is frozen | 130000 | 100 |

Do not use test rows to choose checkpoints or adjust hyperparameters.

## Checkpoint Rule

Training saves snapshots every 10 updates:

```text
actor_critic_update_0010.pt
actor_critic_update_0020.pt
...
actor_critic_update_0120.pt
```

Validation selects checkpoints using:

```text
score = 1000 * post_failure_recovery_rate
      + 100 * success_rate
      - mean_recovery_steps
```

The score prioritizes recovery probability first, success rate second, and recovery speed third.

## Development Run

Use the currently available seed-0/1/2 source checkpoints first:

```bash
python scripts/run_3d_strict_sensing_formal_protocol.py \
  --seeds 0 1 2 \
  --graph-encoders single multi_relation \
  --updates 120 \
  --validation-episodes 50 \
  --test-episodes 100 \
  --scenarios relay_failure
```

This produces:

```text
results/intercept_3d_strict_sensing_formal/protocol.md
results/intercept_3d_strict_sensing_formal/checkpoint_sweep/validation_checkpoint_summary.csv
results/intercept_3d_strict_sensing_formal/checkpoint_sweep/validation_selected_checkpoints.csv
results/intercept_3d_strict_sensing_formal/checkpoint_sweep/test_checkpoint_summary.csv
results/intercept_3d_strict_sensing_formal/checkpoint_sweep/test_episode_metrics.csv
```

## Final Main Run

After seed-3/4 source checkpoints are prepared, rerun with:

```bash
python scripts/run_3d_strict_sensing_formal_protocol.py \
  --seeds 0 1 2 3 4 \
  --graph-encoders single multi_relation \
  --updates 120 \
  --validation-episodes 50 \
  --test-episodes 100 \
  --scenarios relay_failure
```

Final reporting should use only the test split selected by the validation split.

## Required Analysis

For the paper, report:

- validation learning curve across checkpoint updates;
- final test recovery rate and recovery steps;
- seed-level scatter and paired difference;
- layered/bootstrap confidence intervals over training seeds and episodes;
- recovery-process curves after failure: tracking, connectivity, chain closure, and attack-window status.

## Claim Boundary

Promote:

- relay failure;
- strict sensing;
- task-support relation;
- role-pair message gate;
- topology curriculum.

Do not promote as core claims:

- `no_edge_features`;
- `no_role_identity`;
- weak dropout/delay trends;
- low-success maneuvering-target pilots;
- extreme communication-radius stress cases.
