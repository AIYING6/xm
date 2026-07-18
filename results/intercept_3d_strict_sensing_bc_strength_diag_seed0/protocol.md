# Fair Strict-Sensing 3DOF Baseline Protocol

Generated: 2026-07-17T02:00:48

This protocol is smoke-scale by default. It exists to validate that `no_graph`, `single`, and `multi_relation` baselines can use the same BC initialization, topology curriculum, validation checkpoint selection, and disjoint test split.

## Configuration

```text
seeds = [0]
graph_encoders = ['single', 'multi_relation']
bc_episodes = 40
bc_epochs = 10
updates = 3
save_interval = 1
validation_episodes = 5
test_episodes = 5
scenarios = ['relay_failure']
strict_target_sensing = True
```

## Baseline Meaning

- `no_graph`: centralized-training/decentralized-execution MAPPO-style actor without graph message passing.
- `single`: single union-graph GAT-MAPPO baseline.
- `multi_relation`: proposed multi-relation EA-RG-MAPPO-S variant.

## Formal Expansion

After this smoke path passes, increase to at least five training seeds, 100--120 PPO updates, validation episodes 50, and test episodes 100. Do not use test rows for checkpoint selection.
