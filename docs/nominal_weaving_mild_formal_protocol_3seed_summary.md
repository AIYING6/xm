# Nominal `weaving_mild` Frozen-Protocol Three-Seed Summary

Last updated: 2026-07-22

## Purpose

Run the Stage 2 frozen nominal `weaving_mild` scenario-depth protocol on three seeds before deciding whether to expand to five seeds.

This run uses the frozen protocol in `docs/nominal_weaving_mild_frozen_protocol.md`:

- methods: `no_graph`, `single`, `multi_relation`;
- seeds: `0, 1, 2`;
- target policy: `weaving_mild`;
- strict sensing: disabled;
- relay/node failure: disabled;
- oracle-assisted BC: offset mode, 30 episodes, 12 epochs, attacker action weight 4.0;
- PPO: 30 updates, snapshots every 5 updates;
- validation: 30 episodes per checkpoint, base seed `509000`;
- test: 100 episodes per selected checkpoint, base seed `609000`;
- test split was not used for checkpoint selection.

## Selected Checkpoints

| Method | Seed | Selected update | Validation success | Validation attack-window | Validation collision |
|---|---:|---:|---:|---:|---:|
| `no_graph` | 0 | 10 | 0.000 | 0.000 | 0.000 |
| `no_graph` | 1 | 5 | 0.000 | 0.000 | 0.000 |
| `no_graph` | 2 | 25 | 0.000 | 0.000 | 0.000 |
| `single` | 0 | 5 | 0.567 | 0.700 | 0.000 |
| `single` | 1 | 10 | 0.000 | 0.000 | 0.000 |
| `single` | 2 | 25 | 0.000 | 0.000 | 0.000 |
| `multi_relation` | 0 | 20 | 0.933 | 0.933 | 0.000 |
| `multi_relation` | 1 | 15 | 0.067 | 0.067 | 0.000 |
| `multi_relation` | 2 | 25 | 0.700 | 0.733 | 0.000 |

## Test Results

Each selected checkpoint is evaluated on 100 test episodes.

| Method | Episodes | Success | Attack-window formed | Collision | Timeout | Tracking | Connectivity |
|---|---:|---:|---:|---:|---:|---:|---:|
| `no_graph` | 300 | 0.000 | 0.000 | 0.000 | 1.000 | 0.050 | 0.414 |
| `single` | 300 | 0.140 | 0.180 | 0.003 | 0.857 | 0.203 | 0.545 |
| `multi_relation` | 300 | 0.427 | 0.463 | 0.000 | 0.573 | 0.453 | 0.760 |

Per-seed test success:

| Method | Seed 0 | Seed 1 | Seed 2 |
|---|---:|---:|---:|
| `no_graph` | 0.000 | 0.000 | 0.000 |
| `single` | 0.420 | 0.000 | 0.000 |
| `multi_relation` | 0.850 | 0.020 | 0.410 |

## Interpretation

The method hierarchy is preserved:

```text
no_graph < single < multi_relation
```

However, the run does not pass the predefined Stage 2 acceptance gate:

- `multi_relation` success is `42.7%`, below the roughly `60%` minimum target;
- seed 1 remains almost unsolved for `multi_relation`;
- `single` has one collision episode;
- the result is useful diagnostic scenario-depth evidence, but not strong enough for a formal paper-facing table.

## Decision

Do not expand this protocol to seeds `3` and `4` yet.

Do not tune on the `609000` formal test split.

Recommended next action:

1. Treat the current Stage 2 result as a diagnostic showing that maneuvering-target transfer is not yet robust enough.
2. Return to the Stage 1 Gate 1 manuscript package as the primary publishable evidence.
3. If scenario-depth is still required for a Q1 attempt, design a new Stage 2 revision using validation-only diagnostics first, such as stronger oracle BC, longer PPO, or a two-stage `weaving_tiny -> weaving_mild` oracle-assisted route.
4. Freeze any revised Stage 2 protocol before touching a new final test split.
