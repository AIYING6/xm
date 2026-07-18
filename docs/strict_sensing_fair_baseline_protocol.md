# Strict-Sensing Fair Baseline Protocol

This protocol validates fair baseline coverage for the strict-sensing relay-failure experiment.

## Baseline Definitions

- `no_graph`: MAPPO-style CTDE baseline. The critic remains centralized, while the actor does not use graph message passing.
- `single`: single union-graph GAT-MAPPO baseline.
- `multi_relation`: proposed EA-RG-MAPPO-S multi-relation role graph.

## Fairness Rule

All learned baselines should use the same:

- behavior-cloning demonstration policy;
- BC episode and epoch budget;
- PPO topology curriculum budget;
- strict intermittent sensing switch;
- validation episodes for checkpoint selection;
- disjoint final test episodes;
- random training seeds and matched evaluation seeds.

The test split must not be used to choose checkpoints or tune hyperparameters.

## Smoke Command

```bash
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/run_3d_strict_sensing_fair_baseline_protocol.py ^
  --seeds 0 ^
  --graph-encoders no_graph single multi_relation ^
  --bc-episodes 4 ^
  --bc-epochs 1 ^
  --updates 1 ^
  --num-envs 1 ^
  --rollout-steps 8 ^
  --save-interval 1 ^
  --validation-episodes 1 ^
  --test-episodes 1 ^
  --out-dir results/intercept_3d_strict_sensing_fair_baselines_smoke
```

## Formal Expansion

After smoke validation, expand to at least:

```text
seeds = 0 1 2 3 4
bc_episodes = 200
bc_epochs = 80
updates = 100--120
validation_episodes = 50
test_episodes = 100
scenarios = relay_failure
```

Keep `scout_failure` as supporting evidence unless a later formal run separates it cleanly.
