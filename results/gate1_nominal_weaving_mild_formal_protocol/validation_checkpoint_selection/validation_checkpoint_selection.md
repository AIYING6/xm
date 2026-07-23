# Nominal 3DOF Checkpoint Selection

This report evaluates nominal 3DOF checkpoints on a fixed split. Validation rows are for checkpoint selection; test rows must use a frozen validation selection CSV.

## Protocol

```text
split = validation
target_policy = weaving_mild
episodes = 30
base_seed = 509000
eval_batch_size = 10
selection_csv = none
max_selection_collision_rate = 0.0
selection_score = 1000 * success + 100 * attack_window_formed + 10 * tracking, invalid if collision exceeds threshold
```

## Selected Checkpoints

| Method | Graph | Seed | Update | Success | Attack window | Collision | Checkpoint |
|---|---|---:|---:|---:|---:|---:|---|
| `multi_relation` | `multi_relation` | 0 | 20 | 0.933333 | 0.933333 | 0 | `results/gate1_nominal_weaving_mild_formal_protocol/stage2_weaving_mild_ppo/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0020.pt` |
| `multi_relation` | `multi_relation` | 1 | 15 | 0.0666667 | 0.0666667 | 0 | `results/gate1_nominal_weaving_mild_formal_protocol/stage2_weaving_mild_ppo/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0015.pt` |
| `multi_relation` | `multi_relation` | 2 | 25 | 0.7 | 0.733333 | 0 | `results/gate1_nominal_weaving_mild_formal_protocol/stage2_weaving_mild_ppo/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0025.pt` |
| `no_graph` | `no_graph` | 0 | 10 | 0 | 0 | 0 | `results/gate1_nominal_weaving_mild_formal_protocol/stage2_weaving_mild_ppo/runs/no_graph/bc_ppo_seed0/actor_critic_update_0010.pt` |
| `no_graph` | `no_graph` | 1 | 5 | 0 | 0 | 0 | `results/gate1_nominal_weaving_mild_formal_protocol/stage2_weaving_mild_ppo/runs/no_graph/bc_ppo_seed1/actor_critic_update_0005.pt` |
| `no_graph` | `no_graph` | 2 | 25 | 0 | 0 | 0 | `results/gate1_nominal_weaving_mild_formal_protocol/stage2_weaving_mild_ppo/runs/no_graph/bc_ppo_seed2/actor_critic_update_0025.pt` |
| `single` | `single` | 0 | 5 | 0.566667 | 0.7 | 0 | `results/gate1_nominal_weaving_mild_formal_protocol/stage2_weaving_mild_ppo/runs/single/bc_ppo_seed0/actor_critic_update_0005.pt` |
| `single` | `single` | 1 | 10 | 0 | 0 | 0 | `results/gate1_nominal_weaving_mild_formal_protocol/stage2_weaving_mild_ppo/runs/single/bc_ppo_seed1/actor_critic_update_0010.pt` |
| `single` | `single` | 2 | 25 | 0 | 0 | 0 | `results/gate1_nominal_weaving_mild_formal_protocol/stage2_weaving_mild_ppo/runs/single/bc_ppo_seed2/actor_critic_update_0025.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not tune on test split results.