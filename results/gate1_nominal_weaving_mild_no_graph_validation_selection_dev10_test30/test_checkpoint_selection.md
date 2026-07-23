# Nominal 3DOF Checkpoint Selection

This report evaluates nominal 3DOF checkpoints on a fixed split. Validation rows are for checkpoint selection; test rows must use a frozen validation selection CSV.

## Protocol

```text
split = test
target_policy = weaving_mild
episodes = 30
base_seed = 409000
selection_csv = results/gate1_nominal_weaving_mild_no_graph_validation_selection_dev10/validation_selected_checkpoints.csv
max_selection_collision_rate = 0.0
selection_score = 1000 * success + 100 * attack_window_formed + 10 * tracking, invalid if collision exceeds threshold
```

## Selected Checkpoints

| Method | Graph | Seed | Update | Success | Attack window | Collision | Checkpoint |
|---|---|---:|---:|---:|---:|---:|---|
| `no_graph` | `no_graph` | 0 | 30 | 0 | 0 | 0 | `results/gate1_oracle_bc_ppo_weaving_mild_no_graph_seed0_cont30/actor_critic_update_0030.pt` |
| `no_graph` | `no_graph` | 1 | 20 | 0 | 0 | 0 | `results/gate1_oracle_bc_ppo_weaving_mild_no_graph_seed1_cont30/actor_critic_update_0020.pt` |
| `no_graph` | `no_graph` | 2 | 20 | 0 | 0 | 0 | `results/gate1_oracle_bc_ppo_weaving_mild_no_graph_seed2_cont30/actor_critic_update_0020.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not tune on test split results.