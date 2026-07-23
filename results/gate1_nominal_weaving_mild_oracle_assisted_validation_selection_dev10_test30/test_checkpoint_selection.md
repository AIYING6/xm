# Nominal 3DOF Checkpoint Selection

This report evaluates nominal 3DOF checkpoints on a fixed split. Validation rows are for checkpoint selection; test rows must use a frozen validation selection CSV.

## Protocol

```text
split = test
target_policy = weaving_mild
episodes = 30
base_seed = 409000
selection_csv = results/gate1_nominal_weaving_mild_oracle_assisted_validation_selection_dev10/validation_selected_checkpoints.csv
max_selection_collision_rate = 0.0
selection_score = 1000 * success + 100 * attack_window_formed + 10 * tracking, invalid if collision exceeds threshold
```

## Selected Checkpoints

| Method | Graph | Seed | Update | Success | Attack window | Collision | Checkpoint |
|---|---|---:|---:|---:|---:|---:|---|
| `multi_relation` | `multi_relation` | 0 | 30 | 0.8 | 0.866667 | 0 | `results/gate1_oracle_bc_ppo_weaving_mild_seed0_cont30/actor_critic_update_0030.pt` |
| `multi_relation` | `multi_relation` | 1 | 30 | 0.4 | 0.4 | 0 | `results/gate1_oracle_bc_ppo_weaving_mild_seed1_cont30/actor_critic_update_0030.pt` |
| `multi_relation` | `multi_relation` | 2 | 25 | 0.7 | 0.733333 | 0 | `results/gate1_oracle_bc_ppo_weaving_mild_seed2_cont30/actor_critic_update_0025.pt` |
| `single` | `single` | 0 | 25 | 0.333333 | 0.466667 | 0 | `results/gate1_oracle_bc_ppo_weaving_mild_single_seed0_cont30/actor_critic_update_0025.pt` |
| `single` | `single` | 1 | 25 | 0 | 0 | 0 | `results/gate1_oracle_bc_ppo_weaving_mild_single_seed1_cont30/actor_critic_update_0025.pt` |
| `single` | `single` | 2 | 20 | 0 | 0 | 0 | `results/gate1_oracle_bc_ppo_weaving_mild_single_seed2_cont30/actor_critic_update_0020.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not tune on test split results.