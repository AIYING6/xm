# EA-RG-MAPPO Training Stability Dev120 Summary

Generated: 2026-07-29

## Purpose

Run an EA-only development check for the new stability controls:

- fixed online monitor seed;
- critic-only warm-up;
- conservative PPO;
- actor/critic learning-rate split;
- PPO diagnostics.

This is development evidence only. It is not final validation or held-out test.

## Important Setup Note

The first seed-0 run accidentally used the default `hidden_dim=128` against a
no-balanced BC checkpoint trained with `hidden_dim=64`. The loader reported:

```text
loaded 6 matching tensors and 26 partial tensors; skipped 42
```

That run is invalid for BC-to-PPO conclusions.

The valid stability runs use:

```text
--hidden-dim 64
--role-dim 8
--intent-dim 8
```

and load all BC tensors exactly:

```text
loaded 74 matching tensors and 0 partial tensors; skipped 0
```

## Training Protocol

Common settings:

```text
method = EA-RG-MAPPO-S
seeds = 0, 1, 2
BC checkpoints = results/paper_config_runs/no_balanced_bc_dev/bc_seed*/ea_rg_mappo/actor_critic_latest.pt
env_name = 3d_intercept
target_policy = straight
strict_target_sensing = true
agent_target_info_bottleneck = true
communication_dropout_prob = 0.30
message_delay_steps = 2
failed_blue_agent = 1
node_failure_start_step = 40
node_failure_duration_steps = 80
num_envs = 4
rollout_steps = 64
updates = 120
eval_interval = 10
eval_episodes = 10
eval_base_seed = 150000
save_interval = 10
```

Stability settings:

```text
critic_warmup_updates = 30
actor_lr = 5e-5
critic_lr = 1e-4
clip_coef = 0.10
ppo_epochs = 2
target_kl = 0.01
entropy_coef = 0.003
max_grad_norm = 0.5
```

## Fixed Monitor Results

| Seed | Update 40 | Update 60 | Update 100 | Update 120 | Notes |
| ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 0.4 | 0.4 | 0.4 | 0.3 | Stable, no collapse. |
| 1 | 0.3 | 0.3 | 0.3 | 0.3 | Stable, no collapse. |
| 2 | 0.0 | 0.0 | 0.0 | 0.0 | Monitor split remains unsolved. |

Critic diagnostics improved after warm-up:

- seed 0 explained variance reached about `0.45` by update 120;
- seed 1 reached about `0.33` before ending at `0.17`;
- seed 2 reached about `0.41` before ending at `0.37`.

PPO update size stayed conservative:

- `approx_kl` remained far below `0.01`;
- `clip_fraction` was almost always `0`;
- no target-KL early stop was triggered in these short runs.

## Four-Scenario Suite Evaluation

Validation-like diagnostic settings:

```text
scenarios:
  dropout030_delay2_relay_failure_early
  dropout030_delay2_relay_failure
  dropout030_delay2_relay_failure_delayed
  dropout030_delay2_relay_failure_late
episodes = 5 per scenario/checkpoint
base_seed = 291000
selection_group = suite
candidate updates = 60, 80, 100, 120
```

Selected-checkpoint suite results:

| Seed | Selected update | Recovery | Delayed recovery | Success | Collision |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 100 | 0.4 | 0.0 | 0.8 | 0.0 |
| 1 | 100 | 0.3 | 0.0 | 0.6 | 0.0 |
| 2 | 120 | 0.3 | 0.0 | 0.6 | 0.0 |
| Mean | - | 0.333 | 0.000 | 0.667 | 0.000 |

Per-scenario pattern:

- early failure and standard failure are solved at useful rates;
- delayed and late failure show high success but zero post-failure recovery,
  because the successful behavior often completes before a strict recovery event
  is counted;
- strict delayed recovery remains absent in this short stability run.

## Interpretation

The stability controls are useful but incomplete.

Positive:

- Correctly matched BC checkpoints resume cleanly.
- Critic warm-up improves value diagnostics.
- PPO updates are conservative and do not show KL/clip instability.
- Broad suite success is much more seed-consistent than the earlier 1M snapshot
  analysis.
- Collision stays zero for selected checkpoints.

Not solved:

- Strict delayed recovery is still zero in the 120-update stability run.
- Seed 2 remains weak on the fixed monitor split.
- The suite success mostly comes from early/standard failure settings, not from
  delayed/late recovery.

## Decision

Do not run held-out test.

Do not claim final method superiority yet.

The next useful step is not another graph module. The next step should be one of:

1. continue this stable protocol to 300 updates for EA seeds 0/1/2 and run the
   same suite sweep;
2. add a delayed/late failure monitor split so online monitoring does not only
   reflect early/standard behavior;
3. if delayed recovery remains zero at 300 updates, adjust the training
   scenario/curriculum to include delayed/late failure during PPO rather than
   only evaluating it after training.

Only after delayed/late recovery appears under this stable protocol should the
same protocol be fairly applied to Single-Graph, MAPPO/no-graph, and HAPPO.
