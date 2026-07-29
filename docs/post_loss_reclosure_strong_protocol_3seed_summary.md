# Strong Post-Loss Reclosure Protocol: EA-RG-MAPPO-S 3-Seed Development

Last updated: 2026-07-29

## Purpose

This note extends `docs/post_loss_reclosure_recovery_bc_seed0_summary.md`.

The previous seed-0 route showed that balanced offset recovery demonstrations plus conservative PPO can produce delayed/late post-loss recovery. This run tests whether the same idea can be made into a uniform three-seed development protocol.

## Uniform Protocol

Behavior cloning:

- Graph encoder: `multi_relation`
- Demonstration policy: `offset`
- Episodes: `120`
- Epochs: `20`
- Balanced action loss: enabled
- Attacker action weight: `2.0`
- Communication dropout: `0.30`
- Message delay: `2`
- Failed blue agent: `1`
- Failure start sampled in `[25,70]`
- Failure duration: `80`
- Strict target sensing: enabled
- Target-information bottleneck: enabled
- `min_success_step=80`

PPO:

- Updates: `40`
- Candidate checkpoints: `20,30,40`
- Actor LR: `5e-5`
- Critic LR: `1e-4`
- Clip coefficient: `0.1`
- PPO epochs: `2`
- Target KL: `0.01`
- Entropy coefficient: `0.003`
- Critic warm-up: `20` updates
- Post-loss reclosure reward: `0.5`
- Post-loss reclosure minimum step: `80`
- Safety proximity distance: `2500`
- Safety proximity penalty weight: `0.5`

Validation:

- Output: `results/paper_config_runs/stability_dev/checkpoint_sweeps/ea_rg_mappo_strong_offset_balanced_recovery_bc_safety05_seed0_2_dev40`
- Seeds: `0,1,2`
- Scenarios:
  - `dropout030_delay2_relay_failure_early`
  - `dropout030_delay2_relay_failure`
  - `dropout030_delay2_relay_failure_delayed`
  - `dropout030_delay2_relay_failure_late`
- Episodes: `10` per scenario/checkpoint/seed
- Selection: suite-level delayed recovery, `selection_success_weight=0`
- Evaluation uses `min_success_step=80`

## BC Quality

| Seed | Demo success | Final action accuracy |
|---:|---:|---:|
| 0 | 0.908 | 0.510 |
| 1 | 0.908 | 0.510 |
| 2 | 0.917 | 0.479 |

## Selected Checkpoints

| Seed | Selected update | Success | Recovery | After-loss recovery | Delayed recovery | Collision |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 30 | 0.575 | 0.725 | 0.725 | 0.275 | 0.000 |
| 1 | 30 | 0.825 | 0.850 | 0.850 | 0.375 | 0.000 |
| 2 | 20 | 0.475 | 0.575 | 0.575 | 0.375 | 0.000 |
| Mean | - | 0.625 | 0.717 | 0.717 | 0.342 | 0.000 |

## Scenario Averages

| Scenario | Success | Recovery | After-loss recovery | Delayed recovery | Collision | Timeout |
|---|---:|---:|---:|---:|---:|---:|
| early | 0.533 | 0.700 | 0.700 | 0.033 | 0.000 | 0.467 |
| standard | 0.667 | 0.867 | 0.867 | 0.033 | 0.000 | 0.333 |
| delayed | 0.633 | 0.633 | 0.633 | 0.633 | 0.000 | 0.367 |
| late | 0.667 | 0.667 | 0.667 | 0.667 | 0.000 | 0.333 |

## Interpretation

The uniform strong protocol clears the current development gate:

- Three-seed suite recovery is now nonzero and meaningful.
- Delayed/late scenarios are no longer failure cases.
- Collision is zero in the selected validation checkpoints.
- The protocol is now stable enough to expand to matched baselines.

The main weakness is seed-2 performance on early and standard failure timing. This does not block baseline expansion, but it should be tracked when moving to formal runs.

## Decision

Use this as the current EA-RG-MAPPO-S recovery-oriented development protocol.

Do not treat these results as final paper evidence yet because:

- Only EA-RG-MAPPO-S has been run under this exact strong protocol.
- The validation set has been used for checkpoint/protocol development.
- Formal test must wait until baselines use the same protocol and the final validation/test split is frozen.

## Next Step

Run Single-Graph MAPPO under the identical protocol:

1. strong balanced offset recovery BC, seeds `0,1,2`;
2. safety0.5 PPO, seeds `0,1,2`;
3. same four-scenario suite checkpoint sweep;
4. compare against EA before running MAPPO/no-graph and HAPPO.
