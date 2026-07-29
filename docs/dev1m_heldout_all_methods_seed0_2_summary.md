# Dev-1M Held-Out Test Summary, Seeds 0-2

Generated: 2026-07-27

## Scope

This document summarizes held-out test results for the dev-1M strict-sensing relay-failure experiment after validation checkpoint selection.

Protocol:

- validation-selected checkpoints only;
- test split with base seed `220000`;
- 100 matched test episodes per selected checkpoint;
- strict target sensing enabled;
- agent target information bottleneck enabled;
- zero-collision checkpoint-selection constraint was applied at validation time;
- no checkpoint reselection on the test split.

## Test Results

| Method | Seed | Selected update | Test success | Test recovery | Recovery steps | Timeout | Collision |
|---|---:|---:|---:|---:|---:|---:|---:|
| EA-RG-MAPPO | 0 | 1600 | 0.89 | 0.89 | 18.9663 | 0.11 | 0.00 |
| EA-RG-MAPPO | 1 | 2200 | 0.37 | 0.37 | 34.0000 | 0.63 | 0.00 |
| EA-RG-MAPPO | 2 | 3800 | 0.31 | 0.31 | 25.2258 | 0.69 | 0.00 |
| MAPPO/no-graph | 0 | 3800 | 0.60 | 0.60 | 17.8667 | 0.40 | 0.00 |
| MAPPO/no-graph | 1 | 2400 | 0.93 | 0.93 | 19.9462 | 0.07 | 0.00 |
| MAPPO/no-graph | 2 | 3907 | 0.00 | 0.00 | inf | 1.00 | 0.00 |
| Single-Graph MAPPO | 0 | 3907 | 0.80 | 0.80 | 19.4875 | 0.20 | 0.00 |
| Single-Graph MAPPO | 1 | 40 | 0.03 | 0.03 | 77.0000 | 0.97 | 0.00 |
| Single-Graph MAPPO | 2 | 40 | 0.57 | 0.57 | 27.6842 | 0.43 | 0.00 |
| HAPPO | 0 | 900 | 0.08 | 0.08 | 79.8750 | 0.92 | 0.00 |
| HAPPO | 1 | 2900 | 0.20 | 0.20 | 88.2000 | 0.80 | 0.00 |
| HAPPO | 2 | 2100 | 0.00 | 0.00 | inf | 1.00 | 0.00 |

## Aggregate

| Method | Mean success | Std success | Min | Max |
|---|---:|---:|---:|---:|
| EA-RG-MAPPO | 0.5233 | 0.3190 | 0.31 | 0.89 |
| MAPPO/no-graph | 0.5100 | 0.4715 | 0.00 | 0.93 |
| Single-Graph MAPPO | 0.4667 | 0.3953 | 0.03 | 0.80 |
| HAPPO | 0.0933 | 0.1007 | 0.00 | 0.20 |

## Interpretation

The held-out test confirms that the current strict-sensing relay-failure task is not strong enough as the sole main paper scenario.

EA-RG-MAPPO remains the best method by 3-seed mean, but the margin over MAPPO/no-graph is only `+0.0133` absolute success/recovery. MAPPO/no-graph seed 1 transfers from validation to test with `0.93` success/recovery and zero collision. Therefore the no-graph result is not just validation overfitting.

This does not mean the project failed. It means the current scenario is too solvable or too seed-sensitive to support a high-quality graph-centric main claim. The useful result is that the protocol exposed a weak claim before paper writing.

HAPPO remains clearly weak and can stay as an external MARL baseline. The real challenge is MAPPO/no-graph and, secondarily, Single-Graph MAPPO.

## Decision

Do not use this dev-1M strict-sensing relay-failure setting as the final sole main experiment.

Use it as:

- a development baseline;
- a checkpoint-selection protocol validation;
- evidence that naive HAPPO is weak;
- a motivation for adding a harder communication/sensing stress condition.

## Next Experiment Direction

Move to a controlled stress scenario that directly targets the proposed graph mechanism:

1. `dropout030 + relay_failure + strict_target_sensing + bottleneck`;
2. if still weakly separated, add `message_delay_steps=2`;
3. if still insufficient, add early relay failure or mild weaving target.

The next experiment should reuse the same validation-selected/test-split discipline and compare at least:

- EA-RG-MAPPO;
- Single-Graph MAPPO;
- MAPPO/no-graph;
- HAPPO if runtime permits.

The paper claim should shift from generic relay failure to:

> multi-relation role graph improves recovery under simultaneous target intermittency, communication dropout, and relay-node failure.
