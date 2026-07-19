# Gate 1 Safety Fixed-Update-60 Failure-Timing Generalization Formal Summary

This is a fixed-checkpoint formal summary with 100 episodes per training seed.

Source CSVs:

- `results/gate1_safety_fx60_failure_timing_generalization_formal_merged/test_checkpoint_summary.csv`

Failure-window metrics treat `-1` sentinel values as N/A when an episode terminates before the failure window contributes valid measurements.

| Scenario | Method | Episodes/seed | Recovery | Tracking | Chain | Timeout | Collision | Valid failure-window seeds |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| dropout030_relay_failure_early | no_graph | 100 | 23.2 | 18.0 | 1.1 | 75.6 | 1.2 | 5/5 |
| dropout030_relay_failure_early | single | 100 | 46.6 | 42.7 | 2.1 | 50.0 | 3.4 | 5/5 |
| dropout030_relay_failure_early | multi_relation | 100 | 88.2 | 65.9 | 3.9 | 11.6 | 0.2 | 5/5 |
| dropout030_relay_failure | no_graph | 100 | 21.8 | 14.6 | 3.5 | 77.8 | 0.4 | 5/5 |
| dropout030_relay_failure | single | 100 | 53.8 | 47.1 | 8.1 | 44.4 | 1.8 | 5/5 |
| dropout030_relay_failure | multi_relation | 100 | 88.0 | 76.0 | 12.9 | 12.0 | 0.0 | 5/5 |

## Reading

- Early relay failure is harder than the nominal failure timing, but the method ordering is preserved: `no_graph < single < multi_relation` on recovery.
- The nominal dropout-relay timing is still the cleanest current main scenario.