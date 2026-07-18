# 3DOF Fair Source Checkpoint Inventory

This inventory documents which staged source checkpoints are available before strict-sensing fair baseline experiments.

| Method | Seed | Best | Latest | Run directory |
|---|---:|---:|---:|---|
| no_graph | 0 | True | True | `results/intercept_3d_no_graph_source_curriculum/runs/no_graph/bc_ppo_seed0` |
| no_graph | 1 | True | True | `results/intercept_3d_no_graph_source_curriculum/runs/no_graph/bc_ppo_seed1` |
| no_graph | 2 | True | True | `results/intercept_3d_no_graph_source_curriculum/runs/no_graph/bc_ppo_seed2` |
| single | 0 | True | True | `results/intercept_3d_node_failure_curriculum_pilot_seed0/runs/single/bc_ppo_seed0` |
| single | 1 | True | True | `results/intercept_3d_node_failure_curriculum_pilot_seed0/runs/single/bc_ppo_seed1` |
| single | 2 | True | True | `results/intercept_3d_node_failure_curriculum_pilot_seed0/runs/single/bc_ppo_seed2` |
| multi_relation | 0 | True | True | `results/intercept_3d_node_failure_curriculum_pilot_seed0/runs/multi_relation/bc_ppo_seed0` |
| multi_relation | 1 | True | True | `results/intercept_3d_node_failure_curriculum_pilot_seed0/runs/multi_relation/bc_ppo_seed1` |
| multi_relation | 2 | True | True | `results/intercept_3d_node_failure_curriculum_pilot_seed0/runs/multi_relation/bc_ppo_seed2` |

## Decision

All requested best checkpoints exist.

Use this file to justify whether existing `single` / `multi_relation` sources are reused and which `no_graph` sources still need training.
