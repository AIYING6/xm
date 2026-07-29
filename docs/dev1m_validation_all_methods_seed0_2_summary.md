# Dev-1M Validation Summary, Seeds 0-2

Generated: 2026-07-27

## Scope

This document summarizes validation checkpoint selection for the dev-1M strict-sensing relay-failure experiment after all four methods completed 3907 training updates for seeds 0, 1, and 2.

All selected checkpoints use:

- validation split;
- relay-failure strict-sensing scenario;
- 50 matched validation episodes per checkpoint;
- zero-collision checkpoint-selection constraint;
- no held-out test reselection.

## Selected Checkpoints

| Method | Seed | Selected update | Success | Recovery | Recovery steps | Collision |
|---|---:|---:|---:|---:|---:|---:|
| EA-RG-MAPPO | 0 | 1600 | 0.94 | 0.94 | 19.7447 | 0.00 |
| EA-RG-MAPPO | 1 | 2200 | 0.34 | 0.34 | 9.4118 | 0.00 |
| EA-RG-MAPPO | 2 | 3800 | 0.48 | 0.48 | 25.2500 | 0.00 |
| Single-Graph MAPPO | 0 | 3907 | 0.82 | 0.82 | 19.2927 | 0.00 |
| Single-Graph MAPPO | 1 | 40 | 0.04 | 0.04 | 78.5000 | 0.00 |
| Single-Graph MAPPO | 2 | 40 | 0.44 | 0.44 | 23.4545 | 0.00 |
| MAPPO/no-graph | 0 | 3800 | 0.62 | 0.62 | 17.8065 | 0.00 |
| MAPPO/no-graph | 1 | 2400 | 0.98 | 0.98 | 20.1224 | 0.00 |
| MAPPO/no-graph | 2 | 3907 | 0.00 | 0.00 | inf | 0.00 |
| HAPPO | 0 | 900 | 0.14 | 0.14 | 81.2857 | 0.00 |
| HAPPO | 1 | 2900 | 0.20 | 0.20 | 88.2000 | 0.00 |
| HAPPO | 2 | 2100 | 0.02 | 0.02 | 70.0000 | 0.00 |

## Seed-Level Aggregate

| Method | Mean success | Std success | Min | Max |
|---|---:|---:|---:|---:|
| EA-RG-MAPPO | 0.5867 | 0.3139 | 0.34 | 0.94 |
| MAPPO/no-graph | 0.5333 | 0.4957 | 0.00 | 0.98 |
| Single-Graph MAPPO | 0.4333 | 0.3900 | 0.04 | 0.82 |
| HAPPO | 0.1200 | 0.0917 | 0.02 | 0.20 |

## Interpretation

The validation sweep is complete, but the result is not strong enough for the planned main claim in its current form.

EA-RG-MAPPO has the best 3-seed mean, but the margin over MAPPO/no-graph is small (`+0.0534`) and both methods have large seed variance. The MAPPO/no-graph seed-1 checkpoint reaches `0.98` success/recovery with zero collision, which means the current strict-sensing relay-failure validation split can be solved without graph message passing in at least one seed.

This does not invalidate the project, but it changes the next priority. The immediate task is no longer to rush held-out testing only. First, audit whether MAPPO/no-graph has any unintended actor-side information advantage. If the implementation is clean, then the scenario is too easy or too seed-sensitive to support a high-quality graph-centric claim by itself.

HAPPO is consistently weak under this protocol and remains useful as an external MARL baseline, but it is not the main threat to the paper claim.

## No-Graph Boundary Check

A first audit was performed after observing the strong MAPPO/no-graph seed-1 validation result.

Code inspection found:

- the `no_graph` actor branch sets graph features and intent context to zero;
- no-graph policy logits are driven by the same per-agent local observation path used by other methods;
- target cache propagation is tied to direct sensing and communication reachability;
- no direct global target broadcast to the no-graph actor was found in the inspected path.

The existing Gate 1 information-boundary test passed:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe -m pytest tests/test_gate1_communication_feasibility.py -q
24 passed
```

Current interpretation: the no-graph spike is more likely caused by scenario solvability and seed sensitivity than by an obvious actor information-boundary regression. A deeper audit can still add a dedicated no-graph logit-invariance test, but the existing Gate 1 tests did not fail.

## Required Next Steps

1. Audit no-graph actor information boundaries under strict sensing.
2. Compare actor input schemas for no-graph, single-graph, and multi-relation paths.
3. Freeze the current validation-selected checkpoints only after the audit passes.
4. Run held-out test on the selected checkpoints to confirm whether validation ordering transfers.
5. Add a harder but controlled stress condition if no-graph remains competitive, prioritizing sensing/communication constraints over larger scenario scale.

Until these checks are complete, do not claim that EA-RG-MAPPO clearly outperforms MAPPO/no-graph.
