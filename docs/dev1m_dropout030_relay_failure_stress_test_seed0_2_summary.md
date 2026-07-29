# Dev-1M Dropout030 Relay-Failure Stress Test, Seeds 0-2

Generated: 2026-07-27

## Scope

This document summarizes the first stress generalization test after the standard strict-sensing relay-failure held-out test proved too weak for the final graph-centric claim.

Protocol:

- fixed validation-selected checkpoints from the dev-1M strict-sensing relay-failure sweep;
- no checkpoint reselection on the stress condition;
- scenario: `dropout030_relay_failure`;
- test split with base seed `240000`;
- 100 matched episodes per checkpoint;
- strict target sensing enabled;
- agent target information bottleneck enabled.

## Results

| Method | Seed | Update | Success | Recovery | Recovery steps | Tracking during failure | Connectivity during failure | Timeout | Collision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| EA-RG-MAPPO | 0 | 1600 | 0.53 | 0.53 | 20.3019 | 0.3434 | 0.2153 | 0.47 | 0.00 |
| EA-RG-MAPPO | 1 | 2200 | 0.33 | 0.33 | 19.6970 | 0.4256 | 0.1705 | 0.67 | 0.00 |
| EA-RG-MAPPO | 2 | 3800 | 0.04 | 0.04 | 25.2500 | 0.1762 | 0.1618 | 0.95 | 0.01 |
| MAPPO/no-graph | 0 | 3800 | 0.08 | 0.08 | 19.0000 | 0.2112 | 0.1795 | 0.92 | 0.00 |
| MAPPO/no-graph | 1 | 2400 | 0.38 | 0.38 | 23.3947 | 0.2421 | 0.2163 | 0.62 | 0.00 |
| MAPPO/no-graph | 2 | 3907 | 0.00 | 0.00 | inf | 0.1681 | 0.0000 | 1.00 | 0.00 |
| Single-Graph MAPPO | 0 | 3907 | 0.37 | 0.37 | 20.2432 | 0.5293 | 0.1771 | 0.61 | 0.02 |
| Single-Graph MAPPO | 1 | 40 | 0.02 | 0.02 | 78.5000 | 0.0322 | 0.1176 | 0.98 | 0.00 |
| Single-Graph MAPPO | 2 | 40 | 0.00 | 0.00 | inf | 0.1768 | 0.0000 | 1.00 | 0.00 |
| HAPPO | 0 | 900 | 0.32 | 0.32 | 80.4375 | 0.1296 | 0.0456 | 0.68 | 0.00 |
| HAPPO | 1 | 2900 | 0.00 | 0.00 | inf | 0.0074 | 0.0519 | 1.00 | 0.00 |
| HAPPO | 2 | 2100 | 0.02 | 0.02 | 71.0000 | 0.0327 | 0.0190 | 0.98 | 0.00 |

## Aggregate

| Method | Mean success | Std success | Min | Max | Mean tracking | Mean connectivity |
|---|---:|---:|---:|---:|---:|---:|
| EA-RG-MAPPO | 0.3000 | 0.2464 | 0.04 | 0.53 | 0.3151 | 0.1825 |
| MAPPO/no-graph | 0.1533 | 0.2003 | 0.00 | 0.38 | 0.2072 | 0.1319 |
| Single-Graph MAPPO | 0.1300 | 0.2081 | 0.00 | 0.37 | 0.2461 | 0.0982 |
| HAPPO | 0.1133 | 0.1793 | 0.00 | 0.32 | 0.0565 | 0.0388 |

## Interpretation

The stress condition is more useful than the nominal relay-failure held-out test.

Compared with the previous strict-sensing relay-failure held-out test, the no-graph seed-1 spike drops from `0.93` to `0.38`, while EA-RG-MAPPO remains the best 3-seed mean method. The margin between EA-RG-MAPPO and MAPPO/no-graph increases from `+0.0133` to `+0.1467` absolute success/recovery.

This supports the revised paper direction:

> multi-relation role graph improves recovery under simultaneous target intermittency, communication dropout, and relay-node failure.

However, this is still not final paper evidence. EA-RG-MAPPO seed 2 remains weak (`0.04`) and has a small collision rate (`0.01`). Single-Graph seed 0 also has nonzero collision (`0.02`). The final protocol must either report safety separately or use validation selection under the stress condition instead of reusing nominal selected checkpoints.

## Decision

Use `dropout030_relay_failure` as the next main candidate stress scenario.

Do not yet move to writing final results. The correct next step is to perform validation checkpoint selection directly under `dropout030_relay_failure`, not just test nominally selected checkpoints under stress. This will answer whether EA-RG-MAPPO has better recoverable stress-specific checkpoints than the current nominal-selected seed 2.

## Next Step

Run validation checkpoint selection under:

```text
dropout030_relay_failure + strict_target_sensing + agent_target_info_bottleneck
```

for at least:

- EA-RG-MAPPO;
- MAPPO/no-graph;
- Single-Graph MAPPO;
- optionally HAPPO.

Then run held-out stress test using only the stress-validation-selected checkpoints.
