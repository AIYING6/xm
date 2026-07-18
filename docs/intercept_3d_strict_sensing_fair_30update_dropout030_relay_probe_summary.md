# Strict-Sensing dropout030 relay failure Probe Summary

Result directory: `results/intercept_3d_strict_sensing_fair_30update_dropout030_relay_probe`

This is a diagnostic-only evaluation using validation-selected 30-update straight-target checkpoints. No retraining was performed.

| Method | Seeds | Success | Recovery | Recovery steps | Tracking | Connectivity | Timeout |
|---|---:|---:|---:|---:|---:|---:|---:|
| multi_relation | 3 | 98.3% | 98.3% | 5.69 | 98.6% | 33.1% | 1.7% |
| single | 3 | 76.7% | 76.7% | 4.82 | 81.4% | 31.2% | 21.7% |
| no_graph | 3 | 28.3% | 28.3% | 5.18 | 20.2% | 13.3% | 71.7% |

## Interpretation

Communication dropout 0.30 is the best harder-scenario candidate found so far. It keeps `multi_relation` near a high recovery regime while reducing `single` enough to expose a role-graph robustness gap. Seed-aware bootstrap gives a `multi_relation - single` recovery delta of `+21.7 pp` with 95% CI `[+3.3, +41.7] pp`, and a `multi_relation - no_graph` recovery delta of `+70.0 pp` with 95% CI `[+13.3, +100.0] pp`.

This should be treated as a formal-scenario candidate, not yet a final paper result, because the probe reuses checkpoints selected on the easier straight relay-failure validation split. The next step is to define a validation/test protocol where dropout relay failure is part of the checkpoint-selection setting.
