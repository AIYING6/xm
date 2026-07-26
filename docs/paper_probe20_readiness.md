# Probe-20 Launch Readiness

Generated: 2026-07-24

## Purpose

`probe_20` is an engineering-only launch-readiness mode for the final single-paper experiment pipeline.

It verifies that each main method can run through the audited strict-sensing relay-failure command path before expensive 1M/2M/5M training starts.

Probe outputs are not paper evidence.

## Scenario

All probes used:

- 3DOF strict target sensing;
- target-information bottleneck;
- relay node failure: blue agent 1;
- failure start step: 40;
- failure duration: 80;
- communication dropout probability: 0.3;
- target policy: straight.

## Result

| Method | Seed | Updates | Outcome | Duration Sec | Note |
|---|---:|---:|---|---:|---|
| MAPPO/no-graph | 0 | 20 | completed | 13.918 | manifest-runner path passed |
| Single-Graph MAPPO | 0 | 20 | completed | 15.576 | manifest-runner path passed |
| EA-RG-MAPPO | 0 | 20 | completed | 22.878 | manifest-runner path passed |
| HAPPO | 0 | 20 | completed | 18.055 | passed after adding shared fairness arguments to HAPPO parser |

An earlier HAPPO probe failed because `train_happo_baseline.py` did not accept shared fairness/protocol arguments:

```text
--safety-proximity-distance
--safety-proximity-penalty-weight
--intent-coef
```

The parser now accepts these arguments and maps them into `RIGMAPPOConfig`.

## Runtime Implication

The 20-update probe uses only 320 environment steps per method. The `dev_1m` configuration uses 1,000,192 environment steps per training run.

The probe therefore confirms launch compatibility, not final runtime. A rough CPU-only estimate suggests each 1M run may be hours-level. Actual runtime should be measured from the first real `dev_1m` seed because `dev_1m` has larger rollouts and much less frequent online evaluation.

## Next Execution Step

Start development-budget training through:

```text
scripts/run_paper_manifest.py
```

Recommended order:

1. EA-RG-MAPPO seed 0;
2. Single-Graph seed 0;
3. MAPPO seed 0;
4. HAPPO seed 0;
5. repeat seeds 1 and 2 after checking logs.

After all training rows finish, run validation sweeps first, then test sweeps through validation-selected checkpoints.
