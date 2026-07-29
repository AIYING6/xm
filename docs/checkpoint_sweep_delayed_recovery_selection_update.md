# Checkpoint Sweep Delayed-Recovery Selection Update

Last updated: 2026-07-29

## Purpose

Move the strict recovery metric from offline post-processing into the reusable
checkpoint-sweep protocol.

This lets future validation sweeps select checkpoints using delayed post-failure
recovery instead of raw success or legacy recovery.

## Implementation

Updated:

- `scripts/evaluate_3d_checkpoint_sweep.py`
- `configs/paper/checkpoint_selection_schema.yaml`

New sweep arguments:

```text
--selection-metric legacy_recovery|delayed_recovery
--delayed-recovery-min-step 80
--selection-success-weight 100.0
```

Default behavior is unchanged:

```text
--selection-metric legacy_recovery
```

Delayed mode uses:

```text
delayed_recovery = (
    post_failure_chain_recovered_after_loss == 1
    and post_failure_first_chain_step >= delayed_recovery_min_step
)
```

Selection score in delayed mode:

```text
1000 * delayed_recovery_mean + selection_success_weight * success_mean - delayed_recovery_steps_mean
```

## Added CSV Fields

Summary CSV now includes:

- `post_failure_chain_recovered_after_loss_mean`
- `delayed_recovery_min_step`
- `delayed_recovery_mean`
- `delayed_recovery_steps_mean`
- `selection_metric`
- `selection_success_weight`

Selected-checkpoint CSV now includes the same delayed-recovery fields.

## Smoke Verification

Command smoke:

```text
scripts/evaluate_3d_checkpoint_sweep.py
--graph-encoders no_graph
--seeds 1
--checkpoint-glob actor_critic_update_2400.pt
--no-graph-root results/paper_config_runs/dev_1m/runs/mappo
--episodes 2
--max-target-message-age-steps 20
--selection-metric delayed_recovery
--delayed-recovery-min-step 80
```

Smoke result:

| Method | Seed | Update | Legacy recovery | Delayed recovery >= 80 | Success | Selection score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| MAPPO/no-graph | 1 | 2400 | 1.0000 | 0.0000 | 1.0000 | -900 |

This confirms that a checkpoint can still achieve early success while being
penalized by delayed-recovery selection.

Validation:

```text
python -m py_compile scripts/evaluate_3d_checkpoint_sweep.py scripts/analyze_strict_recovery_hardening.py
python scripts/audit_checkpoint_selection_schema.py
```

Both passed.

## Follow-Up Selection-Weight Check

A focused MAPPO/no-graph seed-1 sweep over update `2000` through `2300` under
`dropout030_delay2_relay_failure`, `max_target_message_age_steps=20`, and
`delayed_recovery_min_step=80` found:

| Update | Legacy recovery | Delayed recovery >= 80 | Success | Score with success weight 100 | Score with success weight 0 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2000 | 0.0000 | 0.0000 | 0.0000 | -1000 | -1000 |
| 2060 | 0.0000 | 0.0000 | 0.0000 | -1000 | -1000 |
| 2100 | 0.0000 | 0.0000 | 0.0000 | -1000 | -1000 |
| 2200 | 0.0000 | 0.0000 | 0.0000 | -1000 | -1000 |
| 2300 | 0.8000 | 0.0000 | 0.8000 | -920 | -1000 |

Interpretation:

- `selection_success_weight=100` still lets early success influence selection
  when delayed recovery is zero.
- `selection_success_weight=0` removes that influence. If all candidates have
  zero delayed recovery, the selected checkpoint is just the latest tie-breaker
  and should not be interpreted as a good delayed-recovery checkpoint.

## Decision

Future strict relay-failure validation sweeps should use:

```text
--selection-metric delayed_recovery
--delayed-recovery-min-step 80
--selection-success-weight 0
```

This should be treated as evaluation hardening, not as an algorithmic
contribution.
