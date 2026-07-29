# Dev-1M Dropout030 Delay2 Relay-Failure Validation Selection Summary

Last updated: 2026-07-28

## Protocol

Validation checkpoint selection was run under:

- scenario: `dropout030_delay2_relay_failure`;
- split: validation;
- seeds: 0, 1, 2;
- episodes per selected checkpoint: 50;
- target policy: `straight`;
- strict target sensing: enabled;
- actor target information bottleneck: enabled;
- communication dropout: 0.30;
- message delay: 2 steps;
- failed blue agent: 1, relay UAV;
- failure start step: 40;
- failure duration: 80 steps;
- collision threshold for selection: 0.0.

## Selected-Checkpoint Results

| Method | Seed 0 | Seed 1 | Seed 2 | Mean Success/Recovery | Collision Mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| EA-RG-MAPPO | 0.76 | 0.42 | 0.50 | 0.5600 | 0.0000 |
| Single-Graph MAPPO | 0.56 | 0.32 | 0.80 | 0.5600 | 0.0000 |
| MAPPO/no-graph | 0.64 | 0.78 | 0.00 | 0.4733 | 0.0000 |
| HAPPO | 0.26 | 0.02 | 0.28 | 0.1867 | 0.0000 |

Selected updates:

| Method | Seed 0 | Seed 1 | Seed 2 |
| --- | ---: | ---: | ---: |
| EA-RG-MAPPO | 1700 | 2200 | 2400 |
| Single-Graph MAPPO | 1800 | 200 | 2560 |
| MAPPO/no-graph | 3400 | 2400 | 3907 |
| HAPPO | 900 | 3300 | 2300 |

## Interpretation

This scenario is harder than the nominal strict-sensing relay-failure task and
does reduce the competitiveness of MAPPO/no-graph compared with the nominal
held-out test. However, it is not sufficient as the final main scenario because
EA-RG-MAPPO and Single-Graph MAPPO tie on mean validation success/recovery.

The result supports the value of graph-mediated information sharing over no
graph, but it does not yet support the stronger paper claim that the proposed
multi-relation role graph is clearly better than a single graph.

## Decision

Do not advance `dropout030_delay2_relay_failure` directly to final held-out
testing as the main paper scenario.

Next step:

1. Run validation checkpoint selection under
   `dropout030_delay2_relay_failure_early`.
2. Use the same seeds, episode count, checkpoint-selection rule, and safety
   threshold.
3. Only proceed to held-out test if EA-RG-MAPPO has a clear validation advantage
   over both MAPPO/no-graph and Single-Graph MAPPO without collisions.

