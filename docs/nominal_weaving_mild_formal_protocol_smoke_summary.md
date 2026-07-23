# Nominal `weaving_mild` Formal Protocol Smoke Summary

Last updated: 2026-07-22

## Purpose

Validate the orchestration path for the frozen nominal `weaving_mild` scenario-depth protocol before launching any formal training/evaluation budget.

This is an integration smoke only. It is not experimental evidence.

## Command

```text
python scripts/run_3d_nominal_weaving_mild_formal_protocol.py --smoke --seeds 0 --graph-encoders no_graph --device cpu --skip-existing
```

## Smoke Budget

```text
graph_encoders = ['no_graph']
seeds = [0]
bc_episodes = 2
bc_epochs = 1
ppo_updates = 1
validation_episodes = 2
validation_base_seed = 509000
test_episodes = 2
test_base_seed = 609000
```

## Result

The protocol completed all required stages:

- offset geometric-oracle BC from the existing Gate 1 source checkpoint;
- nominal `weaving_mild` PPO continuation;
- validation checkpoint selection;
- frozen-selection test evaluation.

Generated artifacts:

- `results/gate1_nominal_weaving_mild_formal_protocol_smoke/protocol_run_summary.md`
- `results/gate1_nominal_weaving_mild_formal_protocol_smoke/validation_checkpoint_selection/validation_selected_checkpoints.csv`
- `results/gate1_nominal_weaving_mild_formal_protocol_smoke/test_checkpoint_selection/test_selected_checkpoints.csv`

## Decision

The Stage 2 orchestration path is executable. The next step is not to tune on the test split, but to run the frozen protocol at a development/formal budget according to `docs/nominal_weaving_mild_frozen_protocol.md`.

Recommended next execution:

```text
python scripts/run_3d_nominal_weaving_mild_formal_protocol.py --seeds 0 1 2 --graph-encoders no_graph single multi_relation --device cpu --skip-existing
```

If the three-seed result preserves the current hierarchy and remains collision-free, expand to seeds `3 4` using the same script and unchanged validation/test seeds.
