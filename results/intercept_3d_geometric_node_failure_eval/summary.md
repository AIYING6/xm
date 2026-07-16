# 3DOF Geometric Node-Failure Evaluation

Generated: 2026-07-16T20:27:37

## Protocol

```text
target_policy = straight
scenarios = ['relay_failure', 'scout_failure']
replicate_seeds = [0, 1, 2]
episodes_per_replicate = 30
node_failure = one blue communication node disabled for 80 steps starting at step 40
controller = deterministic geometric pursuit policy, no training
```

## Seed-Mean Summary

| Scenario | Success | Recovered | Recovery Steps | Tracking During Failure | Connectivity During Failure | Timeout | Steps |
|---|---:|---:|---:|---:|---:|---:|---:|
| relay_failure | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 5.167 +/- 0.109 | 1.000 +/- 0.000 | 0.444 +/- 0.002 | 0.000 +/- 0.000 | 45.167 +/- 0.109 |
| scout_failure | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 5.167 +/- 0.109 | 1.000 +/- 0.000 | 0.444 +/- 0.002 | 0.000 +/- 0.000 | 45.167 +/- 0.109 |

## Boundary

```text
This is a rule-based reference under the same node-failure evaluation protocol.
It should be used as a compact baseline, not as evidence for graph-message mechanisms.
```
