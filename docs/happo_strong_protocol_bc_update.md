# HAPPO Strong-Protocol BC Update

Last updated: 2026-07-29

## Purpose

HAPPO is used as an external MARL baseline. To keep the comparison fair under
the current strong post-loss recovery protocol, HAPPO must use the same scenario
knobs and the same behavior-cloning initialization style as EA-RG-MAPPO,
Single-Graph MAPPO, and MAPPO/no-graph.

## Implemented

- `scripts/train_happo_baseline.py`
  - Added CLI support for:
    - `--clip-coef`
    - `--max-grad-norm`
    - `--ppo-epochs`
    - `--eval-base-seed`
    - random node-failure start/duration windows
    - `--min-success-step`
    - post-loss chain reclosure reward
    - `--init-checkpoint`
  - HAPPO now returns a dummy chain-auxiliary tensor so it remains compatible
    with the shared rollout collector.

- `scripts/evaluate_happo_3d.py`
  - Added `--min-success-step` and pass-through to the 3DOF environment.

- `scripts/evaluate_happo_checkpoint_sweep.py`
  - Added `--min-success-step` and pass-through to validation/test checkpoint
    sweeps.

- `scripts/pretrain_happo_3d_bc.py`
  - Added a HAPPO-specific BC pretraining entrypoint.
  - Reuses the existing 3DOF geometric teacher and demonstration collection.
  - Trains each HAPPO agent's independent actor on the same demonstrated action
    labels.
  - Supports balanced loss, attacker action weighting, strict sensing,
    dropout/delay, random relay failure windows, and `min_success_step`.

## Validation

Passed:

- Python compile check for the modified HAPPO scripts.
- 1-update HAPPO strong-protocol training smoke.
- 1-checkpoint HAPPO sweep smoke.
- HAPPO BC smoke.
- HAPPO PPO smoke initialized from the HAPPO BC checkpoint.

The BC smoke used only 2 demonstration episodes and 1 epoch, so its accuracy is
not evidence of performance. It only verifies that the code path is valid.

## Next Experiment

Run HAPPO with the same strong recovery protocol already used for EA,
Single-Graph, and MAPPO/no-graph:

- Seeds: 0, 1, 2.
- BC: balanced offset demonstrations.
- PPO: 40-update development run.
- Checkpoint candidates: 20, 30, 40.
- Validation scenarios:
  - `dropout030_delay2_relay_failure_early`
  - `dropout030_delay2_relay_failure`
  - `dropout030_delay2_relay_failure_delayed`
  - `dropout030_delay2_relay_failure_late`
- Selection: suite-level delayed recovery with `min_success_step=80` and
  success weight 0.

This is still a development comparison, not a final held-out test.
