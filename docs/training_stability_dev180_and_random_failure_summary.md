# EA-RG-MAPPO-S Stability Dev: 180 Updates and Random Failure Pilot

Last updated: 2026-07-29

## Purpose

This note extends `docs/training_stability_dev120_summary.md`.

The goal was to check whether the conservative PPO stability recipe continues to improve EA-RG-MAPPO-S beyond 120 updates, and whether randomizing relay-failure start time during training improves recovery across the frozen four-scenario relay-failure suite.

## Protocol

Shared strict-sensing setting:

- Environment: `3d_intercept`
- Graph encoder: `multi_relation`
- Target policy: `straight`
- Strict target sensing: enabled
- Agent target-information bottleneck: enabled
- Communication dropout: `0.30`
- Message delay: `2`
- Failed blue agent: `1`
- Failure duration: `80` steps
- Fresh target-message gate: `max_target_message_age_steps=80`, `min_target_confidence=0.2`
- BC source: `results/paper_config_runs/no_balanced_bc_dev/bc_seed*/ea_rg_mappo/actor_critic_latest.pt`
- Architecture: `hidden_dim=64`, `role_dim=8`, `intent_dim=8`
- PPO controls: actor LR `5e-5`, critic LR `1e-4`, clip `0.1`, PPO epochs `2`, target KL `0.01`, entropy `0.003`, max grad norm `0.5`, critic warm-up `30` updates
- Online monitor: fixed `eval_base_seed=150000`

Frozen validation suite:

- `dropout030_delay2_relay_failure_early`
- `dropout030_delay2_relay_failure`
- `dropout030_delay2_relay_failure_delayed`
- `dropout030_delay2_relay_failure_late`

## Fixed Failure Training Through 180 Updates

Runs:

- `results/paper_config_runs/stability_dev/ea_rg_mappo_seed0_warmup60_h64`
- `results/paper_config_runs/stability_dev/ea_rg_mappo_seed1_warmup60_h64`
- `results/paper_config_runs/stability_dev/ea_rg_mappo_seed2_warmup60_h64`

Validation sweep:

- Output: `results/paper_config_runs/stability_dev/checkpoint_sweeps/ea_rg_mappo_warmup180_h64`
- Seeds: `0,1,2`
- Checkpoints: `120,140,160,180`
- Episodes: `5` per scenario/checkpoint/seed
- Selection group: suite

Suite-average checkpoint trend:

| Update | Success | Recovery | Delayed recovery | Timeout | Collision |
|---:|---:|---:|---:|---:|---:|
| 120 | 0.533 | 0.267 | 0.000 | 0.467 | 0.000 |
| 140 | 0.533 | 0.267 | 0.000 | 0.467 | 0.000 |
| 160 | 0.600 | 0.300 | 0.000 | 0.400 | 0.000 |
| 180 | 0.400 | 0.200 | 0.000 | 0.600 | 0.000 |

Selected checkpoints under suite legacy-recovery scoring:

| Seed | Selected update | Success | Recovery | Delayed recovery | Collision |
|---:|---:|---:|---:|---:|---:|
| 0 | 160 | 0.600 | 0.300 | 0.000 | 0.000 |
| 1 | 180 | 0.600 | 0.300 | 0.000 | 0.000 |
| 2 | 180 | 0.600 | 0.300 | 0.000 | 0.000 |

Interpretation:

- The best aggregate point in this run is around update `160`.
- Continuing to update `180` does not improve the suite and can degrade seed-0 behavior.
- Conservative PPO improves broad success and keeps collision at zero, but it still does not produce strict delayed/late recovery.
- Online 10-episode monitor drops to zero at update `180` for all three seeds, while suite validation still finds useful checkpoints. This confirms that checkpoint selection must use fixed validation sweeps, not online monitor alone.

## Random Failure Start Pilot

Run:

- `results/paper_config_runs/stability_dev/ea_rg_mappo_seed0_random_failure_h64`

Training changed only one factor:

- Failure start randomized during training: `[25,100]`

Validation sweep:

- Output: `results/paper_config_runs/stability_dev/checkpoint_sweeps/ea_rg_mappo_random_failure_seed0_dev60`
- Seed: `0`
- Checkpoints: `20,40,60`
- Episodes: `10` per scenario/checkpoint

Suite-average trend:

| Update | Success | Recovery | Delayed recovery | Timeout | Collision |
|---:|---:|---:|---:|---:|---:|
| 20 | 0.400 | 0.200 | 0.000 | 0.600 | 0.000 |
| 40 | 0.400 | 0.200 | 0.000 | 0.600 | 0.000 |
| 60 | 0.400 | 0.200 | 0.000 | 0.600 | 0.000 |

Interpretation:

- Random failure start alone does not solve delayed/late recovery.
- It also weakens the seed-0 broad recovery signal compared with fixed-failure training.
- The next step should not be merely adding updates under the same random-start setting. The training objective or curriculum must more directly reward post-loss re-closure of the kill chain.

## Decision

Do not promote the current fixed-failure or random-failure stability runs to formal paper evidence yet.

Use them as development evidence for the following conclusions:

- Conservative PPO controls are useful for preventing obvious instability and maintaining zero collision.
- Fixed step-40 relay failure can produce broad recovery and task success.
- Cross-failure-time delayed recovery remains unsolved.

## Next Recommended Step

Add a development training mode that explicitly samples and rewards post-loss chain re-closure:

1. Keep the frozen validation suite unchanged.
2. Train with failure starts sampled from the same suite-relevant window, but avoid overly broad `[25,100]` at first. Prefer a staged window such as `25-55` followed by `25-70`.
3. Add or enable a reward/auxiliary term tied to first post-loss chain re-closure after the failure event.
4. Run only EA seed 0 first for `60-100` updates.
5. If delayed recovery becomes nonzero without destroying broad success, expand to seeds `0,1,2`.

Acceptance gate for expanding beyond pilot:

- Suite success at least `0.50`;
- Suite recovery at least `0.25`;
- Delayed recovery greater than `0.00`;
- Collision remains `0.00`.
