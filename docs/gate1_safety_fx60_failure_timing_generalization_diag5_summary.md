# Gate 1 Safety Fixed-Update-60 Failure-Timing Generalization Diagnostic

This is a 5-episode-per-seed diagnostic only. It is not paper-level evidence.

Source CSV: `C:/Users/96251/Documents/Codex/2026-07-12/ni/work/ri_gmappo_uav/results/gate1_safety_fx60_failure_timing_generalization_diag5/test_checkpoint_summary.csv`

Failure-window metrics treat `-1` sentinel values as N/A when an episode terminates before the failure window contributes valid measurements.

| Scenario | Method | Recovery | Tracking | Chain | Timeout | Collision | Valid failure-window seeds |
|---|---|---:|---:|---:|---:|---:|---:|
| dropout030_relay_failure_early | no_graph | 28.0 | 19.2 | 1.3 | 72.0 | 0.0 | 5/5 |
| dropout030_relay_failure_early | single | 48.0 | 41.8 | 2.2 | 52.0 | 0.0 | 5/5 |
| dropout030_relay_failure_early | multi_relation | 76.0 | 58.7 | 3.3 | 24.0 | 0.0 | 5/5 |
| dropout030_relay_failure | no_graph | 20.0 | 14.5 | 3.1 | 80.0 | 0.0 | 5/5 |
| dropout030_relay_failure | single | 56.0 | 48.3 | 8.4 | 44.0 | 0.0 | 5/5 |
| dropout030_relay_failure | multi_relation | 84.0 | 69.3 | 11.6 | 16.0 | 0.0 | 5/5 |
| dropout030_relay_failure_late | no_graph | 0.0 | 0.0 | 0.0 | 80.0 | 0.0 | 4/5 |
| dropout030_relay_failure_late | single | 0.0 | 0.0 | 0.0 | 40.0 | 8.0 | 1/5 |
| dropout030_relay_failure_late | multi_relation | 4.0 | N/A | N/A | 20.0 | 0.0 | 0/5 |

## Diagnostic Reading

- Early relay failure is harder than the nominal failure timing, but the method ordering is preserved in this small diagnostic: `no_graph < single < multi_relation` on recovery.
- The nominal dropout-relay timing is still the cleanest current main scenario.
- Late relay failure needs careful metric handling because some policies finish or fail before the failure window produces valid failure-window tracking/chain measurements.
- A formal timing-generalization run is worthwhile, but the paper should report valid-window counts and avoid overinterpreting late-failure tracking averages if many episodes terminate before the window.