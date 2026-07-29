# Training Stability Implementation Update

Generated: 2026-07-29

## Purpose

This update implements the first engineering step from
`EA_RG_MAPPO_training_stability_solution.md`: make PPO instability observable and
add conservative controls for the BC-to-PPO transition.

The immediate target is EA-RG-MAPPO-S seed instability and late-policy
degradation under the frozen four-scenario relay-failure suite.

## Implemented

### Fixed Online Monitor Seeds

`RIGMAPPOConfig` now supports:

```text
eval_base_seed: int | None = None
```

When unset, the old behavior is preserved:

```text
base_seed = 10000 + update * 100
```

When set, every online evaluation uses the same monitor episodes. This makes
learning curves more interpretable. These monitor episodes remain separate from
validation and held-out test.

### PPO Stability Metrics

`train_log.csv` now records:

```text
approx_kl
clip_fraction
grad_norm
explained_variance
ppo_epochs_ran
critic_warmup_active
```

These metrics are needed to diagnose whether policy degradation comes from
oversized PPO updates, unstable critic estimates, entropy collapse, or reward
scale/gradient issues.

### Critic-Only Warm-Up

`RIGMAPPOConfig` now supports:

```text
critic_warmup_updates: int = 0
```

During warm-up, the rollout is still collected by the current actor, but the
optimization loss is only:

```text
value_coef * value_loss
```

This lets the critic learn returns before actor updates begin.

### Conservative PPO Controls

The RI-GMAPPO training CLI now exposes:

```text
--actor-lr
--critic-lr
--clip-coef
--ppo-epochs
--target-kl
--max-grad-norm
```

The optimizer supports separate actor and critic learning rates while preserving
the original single-learning-rate behavior when these fields are not provided.

`target_kl` enables PPO epoch early stopping. It is disabled by default.

## Validation

Static validation passed:

```text
python -m py_compile algorithms/ri_gmappo/simple_ri_gmappo.py scripts/train_ri_gmappo.py
```

A one-update 3D EA-RG-MAPPO-S smoke run passed with:

```text
--critic-warmup-updates 1
--actor-lr 5e-5
--critic-lr 1e-4
--clip-coef 0.1
--ppo-epochs 2
--target-kl 0.01
--eval-base-seed 150000
```

The smoke log contained the new stability fields:

```text
approx_kl = 0.0
clip_fraction = 0.0
grad_norm = 0.8849
explained_variance = 0.0876
ppo_epochs_ran = 2
critic_warmup_active = 1.0
```

## Recommended Next Experiment

Run EA-RG-MAPPO-S only first, because this is a stability diagnosis rather than
formal method comparison.

Suggested protocol:

```text
method: EA-RG-MAPPO-S
seeds: 0, 1, 2
updates: 300
num_envs: 4
rollout_steps: 64
eval_interval: 20
eval_episodes: 30
eval_base_seed: 150000
save_interval: 20
save_snapshots: true
```

Suggested conservative PPO settings:

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

Gate for promotion:

- fixed-monitor success/recovery should not show late collapse;
- delayed-recovery signal should appear in at least 2/3 seeds after validation
  sweep;
- collision should remain zero for selected checkpoints;
- `approx_kl` and `clip_fraction` should not stay abnormally high;
- `explained_variance` should improve over random-critic behavior;
- PPO should improve over BC-only rather than erase it.

Only after this EA-only stability run is useful should the same stable protocol
be applied fairly to Single-Graph, MAPPO/no-graph, and HAPPO.
