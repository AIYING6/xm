# Gate 1 Safety Fixed-Update-60 Failure-Timing Generalization Formal Evidence

Last updated: 2026-07-19

## Protocol

- Policies: fixed `actor_critic_update_0060.pt` from the safety-enabled five-seed package.
- Methods: `no_graph`, `single`, `multi_relation`.
- Scenarios: `dropout030_relay_failure_early` and `dropout030_relay_failure`.
- Evaluation: 5 training seeds, 100 matched episodes per seed, 3000 total episodes after deduplication.
- No retraining or checkpoint selection was performed for this timing-generalization test.

## Mean Results

Failure-window metrics treat `-1` sentinel values as N/A when an episode terminates before the failure window contributes valid measurements.

| Scenario | Method | Episodes/seed | Recovery | Tracking | Chain | Timeout | Collision | Valid failure-window seeds |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| dropout030_relay_failure_early | no_graph | 100 | 23.2 | 18.0 | 1.1 | 75.6 | 1.2 | 5/5 |
| dropout030_relay_failure_early | single | 100 | 46.6 | 42.7 | 2.1 | 50.0 | 3.4 | 5/5 |
| dropout030_relay_failure_early | multi_relation | 100 | 88.2 | 65.9 | 3.9 | 11.6 | 0.2 | 5/5 |
| dropout030_relay_failure | no_graph | 100 | 21.8 | 14.6 | 3.5 | 77.8 | 0.4 | 5/5 |
| dropout030_relay_failure | single | 100 | 53.8 | 47.1 | 8.1 | 44.4 | 1.8 | 5/5 |
| dropout030_relay_failure | multi_relation | 100 | 88.0 | 76.0 | 12.9 | 12.0 | 0.0 | 5/5 |

## Seed-Aware Recovery Deltas

| Scenario | Comparison | Recovery delta pp | Tracking delta pp | Timeout delta pp | Restricted recovery-step delta |
|---|---|---:|---:|---:|---:|
| Early relay failure | Full vs Single | 41.6 [4.4, 78.6] | 23.3 [2.4, 44.9] | -38.4 [-74.8, -2.0] | -77.9 [-158.6, -0.5] |
| Early relay failure | Full vs No graph | 65.0 [27.2, 93.2] | 47.9 [31.4, 62.8] | -64.0 [-91.0, -27.2] | -133.7 [-189.1, -57.1] |
| Nominal relay failure | Full vs Single | 34.2 [0.6, 71.8] | 29.0 [-1.3, 62.1] | -32.4 [-68.8, -0.4] | -63.8 [-147.8, 5.7] |
| Nominal relay failure | Full vs No graph | 66.2 [29.4, 93.2] | 61.5 [42.6, 82.7] | -65.8 [-92.8, -29.2] | -134.8 [-190.9, -60.4] |

## Interpretation

- Early relay failure is a valid scenario-depth extension: the method ordering remains `no_graph < single < multi_relation` and the full-vs-single recovery interval is separated from zero.
- The nominal timing result is consistent with the main fixed-update-60 evidence package.
- This experiment supports limited timing robustness against earlier relay loss, not arbitrary failure-time robustness.
- Delayed/late relay failure remains deferred because the current episode termination can end successful episodes before the delayed failure window produces valid post-failure metrics.
