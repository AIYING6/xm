# Early Validation Mechanism Diagnostics

Last updated: 2026-07-28

## Scope

This diagnostic compares validation-selected checkpoints for:

```text
dropout030_delay2_relay_failure_early
```

Methods:

- MAPPO/no-graph;
- Single-Graph MAPPO;
- EA-RG-MAPPO.

The goal is to explain why EA-RG-MAPPO improves over no-graph but does not beat
Single-Graph MAPPO in this scenario.

## Aggregate Mechanism Metrics

| Method | Success/Recovery | Recovery Steps Censored | Tracking During Failure | Connectivity During Failure | Mean Message Age | Attack Window Rate | Timeout |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MAPPO/no-graph | 0.3667 | 167.1133 | 0.2277 | 0.1239 | 87.3436 | 0.0090 | 0.6333 |
| Single-Graph MAPPO | 0.5267 | 128.5267 | 0.4328 | 0.1586 | 55.7286 | 0.0133 | 0.4733 |
| EA-RG-MAPPO | 0.4733 | 140.8333 | 0.3458 | 0.1805 | 62.6521 | 0.0116 | 0.5267 |

## Interpretation

EA-RG-MAPPO is better than MAPPO/no-graph on the intended recovery mechanisms:

- higher success/recovery: `0.4733` vs `0.3667`;
- lower censored recovery time: `140.8333` vs `167.1133`;
- higher tracking during failure: `0.3458` vs `0.2277`;
- higher connectivity during failure: `0.1805` vs `0.1239`;
- lower mean message age: `62.6521` vs `87.3436`.

However, Single-Graph MAPPO remains stronger overall:

- higher success/recovery: `0.5267` vs EA `0.4733`;
- shorter censored recovery time: `128.5267` vs EA `140.8333`;
- higher tracking during failure: `0.4328` vs EA `0.3458`;
- higher attack-window rate: `0.0133` vs EA `0.0116`;
- lower timeout rate: `0.4733` vs EA `0.5267`.

EA has slightly higher connectivity during failure than Single-Graph
(`0.1805` vs `0.1586`), but this does not translate into better tracking or
faster recovery.

## Seed-Level Pattern

| Method | Seed 0 | Seed 1 | Seed 2 |
| --- | ---: | ---: | ---: |
| MAPPO/no-graph | 0.62 | 0.48 | 0.00 |
| Single-Graph MAPPO | 0.60 | 0.32 | 0.66 |
| EA-RG-MAPPO | 0.28 | 0.72 | 0.42 |

EA-RG-MAPPO is not uniformly weak. It beats Single-Graph on seed1, but loses on
seed0 and seed2. The issue is seed stability, not lack of any useful behavior.

## Working Hypothesis

The multi-relation graph can build better connectivity, but its relation routing
does not reliably preserve target tracking and attack-window formation. In some
seeds, the additional relation structure may create optimization variance or
early checkpoint overfitting.

## Next Step

Do not search for another stress scenario yet.

Next diagnostics:

1. run role-graph diagnostics on EA selected checkpoints:
   - seed0 update 100;
   - seed1 update 1200;
   - seed2 update 2900;
2. compare relation attention and task-support usage between weak and strong
   EA seeds;
3. inspect whether weak EA seeds overuse communication relation while underusing
   task-support relation;
4. only after that decide whether to tune training stability, relation loss, or
   relation weighting.

