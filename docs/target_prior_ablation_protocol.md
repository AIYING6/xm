# Target-Prior Ablation Protocol

Generated: 2026-07-26

## Purpose

The strict-sensing 3DOF task uses a target prior before any valid target detection or communication message is available:

```text
target_prior_position = (10000, 0, 5000)
```

This is a search prior, not direct target-state leakage. However, because the red target can start near this region, a paper-facing robustness check must verify that EA-RG-MAPPO does not rely on an overly accurate fixed prior.

## Implementation Status

The following entry points now expose the prior explicitly:

```text
scripts/train_ri_gmappo.py --target-prior-position X Y Z
scripts/train_happo_baseline.py --target-prior-position X Y Z
scripts/evaluate_ri_gmappo_3d.py --target-prior-position X Y Z
scripts/evaluate_happo_3d.py --target-prior-position X Y Z
scripts/evaluate_3d_checkpoint_sweep.py --target-prior-position X Y Z
scripts/evaluate_happo_checkpoint_sweep.py --target-prior-position X Y Z
```

The paper command manifest reads the default prior from:

```text
configs/paper/main_gate1.yaml
```

Evaluation CSVs and checkpoint-selection CSVs record:

```text
target_prior_position
```

## Recommended Experiments

Run these only after dev-1M seed-0 training and validation checkpoint selection are complete.

| Setting | Prior | Purpose |
|---|---|---|
| fixed accurate | `(10000, 0, 5000)` | Current main setting |
| lateral offset | `(10000, 8000, 5000)` | Tests horizontal prior bias |
| range offset | `(18000, 0, 5000)` | Tests range prior bias |
| altitude offset | `(10000, 0, 7500)` | Tests vertical prior bias |
| far prior | `(0, -20000, 5000)` | Tests strong prior mismatch |

## Interpretation

This is a robustness and credibility experiment, not a main algorithm contribution.

Safe claim if results hold:

```text
EA-RG-MAPPO keeps its recovery advantage under target-prior perturbations,
suggesting that recovery depends on communication-feasible target information
rather than only on a fixed target-location prior.
```

Unsafe claim:

```text
The method performs target search without any prior information.
```

That claim would require a separate no-prior/unknown-token design and retraining protocol.

## Execution Boundary

Do not tune models based on test-prior results. Use selected validation checkpoints first, then run prior perturbations as frozen-checkpoint diagnostics.
