# 3DOF Compact Node-Failure Baselines

Generated: 2026-07-16T20:29:10

Inputs:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\intercept_3d_geometric_node_failure_eval\episode_metrics.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\intercept_3d_node_failure_curriculum_formal_node_failure_eval\episode_metrics.csv
```

Purpose:

```text
Put the oracle geometric pursuit diagnostic, single-graph MAPPO, and EA-RG-MAPPO-S under the same straight-target node-failure evaluation table.
The geometric policy uses simulator target state and is therefore an oracle-style demonstrator/reference, not a fair decentralized learning baseline.
Use this table to document task difficulty and baseline coverage; use the paired single-vs-multi and ablation tables for the method contribution.
```

## Compact Table

| Scenario | Method | N | Success % [95% CI] | Recovery % [95% CI] | Recovery Steps [95% CI] | Tracking-Failure % [95% CI] | Connectivity-Failure % [95% CI] | Steps [95% CI] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| relay_failure | Oracle geometric pursuit | 90 | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 5.2 [5.0, 5.4] | 100.0 [100.0, 100.0] | 44.4 [44.1, 44.8] | 45.2 [45.0, 45.4] |
| relay_failure | Single-graph MAPPO | 90 | 92.2 [86.7, 96.7] | 92.2 [86.7, 97.8] | 21.8 [10.1, 33.9] | 93.4 [88.7, 97.2] | 43.7 [42.9, 44.3] | 61.8 [50.0, 74.2] |
| relay_failure | EA-RG-MAPPO-S | 90 | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 5.6 [5.4, 6.0] | 100.0 [99.9, 100.0] | 43.8 [43.4, 44.2] | 45.6 [45.4, 46.0] |
| scout_failure | Oracle geometric pursuit | 90 | 100.0 [100.0, 100.0] | 100.0 [100.0, 100.0] | 5.2 [5.0, 5.4] | 100.0 [100.0, 100.0] | 44.4 [44.1, 44.8] | 45.2 [45.0, 45.4] |
| scout_failure | Single-graph MAPPO | 90 | 94.4 [88.9, 98.9] | 94.4 [90.0, 98.9] | 17.1 [7.6, 29.0] | 95.3 [90.7, 99.0] | 43.9 [43.2, 44.5] | 57.1 [47.7, 69.0] |
| scout_failure | EA-RG-MAPPO-S | 90 | 96.7 [92.2, 100.0] | 96.7 [92.2, 100.0] | 12.7 [5.5, 22.0] | 97.2 [93.5, 100.0] | 43.6 [43.0, 44.1] | 52.7 [45.5, 62.0] |

## Interpretation Boundary

```text
Straight-target node-failure episodes are now strong enough to show recovery timing differences, but they are not hard enough to separate an oracle geometric demonstrator from the learned policy.
For a Q2-level manuscript, the next quality step is a stricter intermittent-sensing or maneuvering-target protocol where target truth is not always injected into every blue observation.
```
