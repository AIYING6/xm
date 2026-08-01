# Relay-Failure Case Replay

Generated: 2026-08-02T01:40:59

This is a matched qualitative case replay selected from the formal relay-failure evaluation candidates. It is meant to support interpretation of the quantitative table, not replace aggregate statistics.

## Candidate

```text
train_seed = 0
episode = 0
single_rollout_seed = 91000
multi_rollout_seed = 91000
node_failure = agent 1, steps 40--119
```

## Replay Summary

| Graph encoder | Success | Steps | First chain close step | Tracking during failure | Connectivity during failure |
| --- | ---: | ---: | ---: | ---: | ---: |
| `single` | 0 | 260 | -1 | 0.100 | 0.154 |
| `multi_relation` | 0 | 260 | -1 | 0.146 | 0.333 |

## Figure

- `results/figures/intercept_3d_relay_failure_case_replay.png`
