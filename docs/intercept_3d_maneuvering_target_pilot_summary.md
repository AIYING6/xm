# 3DOF Maneuvering-Target Pilot Summary

Generated: 2026-07-16

## Purpose

Evaluate whether the existing straight-target topology-curriculum checkpoints can support a stronger maneuvering-target scenario without retraining.

## Policies Tested

- `break_turn`: defensive lateral break turn when a blue UAV enters the threat zone.
- `weaving`: sinusoidal lateral and altitude maneuvering.
- `weaving_mild`: reduced-amplitude weaving.

## Results

| Target policy | Scope | Main observation |
| --- | --- | --- |
| `break_turn` | 3 seeds, relay/scout failure, 360 episodes | Multi-relation outperforms single-graph, but absolute success is low: relay `0.244`, scout `0.144`; single-graph is `0.000` on both. |
| `break_turn` after 20-update seed-0 fine-tune | seed 0, relay/scout failure, 120 episodes | Fine-tuning does not solve the task: multi-relation relay `0.267`, scout `0.000`; single-graph remains `0.000`. |
| `weaving` | 3 seeds, relay/scout failure, 360 episodes | Similar to break-turn: multi-relation relay `0.267`, scout `0.144`; single-graph is `0.000` on both. |
| `weaving_mild` | seed 0, relay/scout failure, 120 episodes | Still too hard in zero-shot form: multi-relation relay `0.267`, scout `0.000`; single-graph remains `0.000`. |

## Interpretation

```text
Maneuvering targets provide useful scenario-depth evidence because they create strong separation between single-graph and multi-relation policies.
However, zero-shot and short fine-tuning success rates are too low for a paper-facing main table.
The next useful step is not further zero-shot target-policy tuning; it is a staged maneuvering-target curriculum or a compact baseline comparison on the already stable relay/scout straight-target setting.
```

## Decision

```text
Keep break_turn/weaving/weaving_mild as scenario-depth pilot evidence.
Do not promote them to main paper results yet.
For Q2-level strengthening, either:
1. implement a staged target-policy curriculum: straight -> weaving_mild -> weaving -> break_turn, or
2. run a compact baseline comparison on the already stable relay/scout node-failure task.
```
