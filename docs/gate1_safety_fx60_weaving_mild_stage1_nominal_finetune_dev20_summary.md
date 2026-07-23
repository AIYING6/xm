# Weaving-Mild Stage 1 Nominal Fine-Tuning Diagnostic

Date: 2026-07-22

## Purpose

This diagnostic tested the first stage of a scenario-depth curriculum for `weaving_mild`.

The previous strict relay-failure weaving run failed at zero recovery, and from-scratch nominal weaving BC/PPO was unstable. This run therefore used the mature straight-target safety fixed-update-60 checkpoints as source policies and fine-tuned them under nominal `weaving_mild`.

The acceptance gate was intentionally simple:

- no strict sensing;
- no target-information bottleneck;
- no relay failure;
- `multi_relation` must become meaningfully learnable before any Stage 2 strict-sensing experiment.

## Protocol

- Methods: `single`, `multi_relation`
- Seeds: `0, 1, 2`
- Source checkpoints: `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/<method>/bc_ppo_seed<seed>/actor_critic_update_0060.pt`
- Target policy: `weaving_mild`
- Fine-tuning budget: 20 PPO updates
- Learning rate: `1e-5`
- Hidden dimension: `64`
- Save snapshots: updates `5, 10, 15, 20`
- Validation: 20 nominal weaving episodes per seed
- Test: 40 nominal weaving episodes per seed

Outputs:

- `results/gate1_safety_fx60_weaving_mild_nominal_finetune_from_straight_h64_lr1e5_dev20/`

Important implementation note:

An earlier attempted run used `hidden_dim=128`, which only partially loaded the fixed-update-60 source checkpoints. That run is invalid for interpretation. The current run uses `hidden_dim=64` and loads the source checkpoints correctly.

## Test Result

Validation-selected test performance:

| Method | Seed | Selected update | Success | Timeout | Collision | Mean steps |
|---|---:|---:|---:|---:|---:|---:|
| `multi_relation` | 0 | 20 | 52.5% | 47.5% | 0.0% | 191.3 |
| `multi_relation` | 1 | 20 | 0.0% | 100.0% | 0.0% | 260.0 |
| `multi_relation` | 2 | 5 | 27.5% | 72.5% | 0.0% | 241.0 |
| `single` | 0 | 20 | 0.0% | 100.0% | 0.0% | 260.0 |
| `single` | 1 | 20 | 0.0% | 97.5% | 2.5% | 255.3 |
| `single` | 2 | 20 | 0.0% | 100.0% | 0.0% | 260.0 |

Aggregate:

| Method | Success | Timeout | Collision |
|---|---:|---:|---:|
| `multi_relation` | 26.7% | 73.3% | 0.0% |
| `single` | 0.0% | 99.2% | 0.8% |

## Interpretation

The result is useful but not sufficient.

Useful:

- Correctly loaded straight-target source checkpoints transfer better than from-scratch weaving BC/PPO.
- `multi_relation` shows nonzero nominal weaving adaptation on two of three seeds.
- `single` remains at zero success under the same low-learning-rate adaptation, so the multi-relation structure remains promising in the scenario-depth direction.

Insufficient:

- Mean `multi_relation` success is only 26.7%, below the acceptance range for moving to strict sensing.
- Seed 1 fails completely, so the training route is not robust.
- This is nominal weaving only; it does not yet support any strict sensing, relay failure, or recovery claim.

## Decision

Do not start Stage 2 strict-sensing weaving yet.

The next scenario-depth task should improve Stage 1 nominal weaving until `multi_relation` reaches a useful range, preferably 60%-80% success with low collision rate. Recommended next changes are:

1. Increase fine-tuning budget to 60 updates while keeping `hidden_dim=64` and source checkpoint compatibility.
2. Use validation checkpoint selection over snapshots every 5 or 10 updates.
3. Keep learning rate small (`1e-5` first); only adjust one variable at a time.
4. If seed 1 remains stuck, run a seed-1 focused diagnostic with lower target maneuver amplitude or a two-phase target policy schedule.
