# Delayed-Recovery Candidate Sweep: Small Diagnostic

Generated: 2026-07-29

## Purpose

This diagnostic tested whether existing dev-1M checkpoints contain a usable
strict delayed-recovery signal under the fresh-message stress protocol:

- scenario: `dropout030_delay2_relay_failure`
- strict target sensing: enabled
- agent target-info bottleneck: enabled
- max target message age: `20`
- communication dropout: `0.30`
- message delay: `2`
- relay failure: blue agent `1`, start step `40`, duration `80`
- validation episodes: `5` matched episodes per checkpoint
- checkpoint selection metric: `delayed_recovery`
- delayed recovery minimum step: `80`
- success weight in selection score: `0`

The sweep used only selected update candidates from the existing dev-1M runs to
avoid a full expensive checkpoint sweep.

## Tooling Update

`scripts/evaluate_3d_checkpoint_sweep.py` now supports:

```text
--checkpoint-updates <update> [<update> ...]
--selection-group scenario|suite
```

This filters checkpoint discovery after `--checkpoint-glob`, allowing small,
reproducible candidate sweeps over specific snapshots. `--selection-group suite`
selects one checkpoint per method/seed using the mean validation score across
all requested scenarios, which prevents per-scenario checkpoint cherry-picking.
The report protocol now also records `checkpoint_updates`,
`selection_group`, and `selection_success_weight`.

Validation:

```text
python -m py_compile scripts/evaluate_3d_checkpoint_sweep.py scripts/analyze_strict_recovery_hardening.py
python scripts/audit_checkpoint_selection_schema.py
```

Both checks passed.

## Results

Selected checkpoints under `delayed_recovery_min_step = 80`:

| Method | Seed | Selected update | Delayed recovery | Legacy recovery | Success |
| --- | ---: | ---: | ---: | ---: | ---: |
| EA-RG-MAPPO-S | 0 | 3907 | 0.000 | 0.000 | 0.000 |
| EA-RG-MAPPO-S | 1 | 3800 | 0.200 | 0.200 | 0.200 |
| EA-RG-MAPPO-S | 2 | 3907 | 0.000 | 0.000 | 0.000 |
| Single-Graph MAPPO | 0 | 3907 | 0.000 | 0.000 | 0.000 |
| Single-Graph MAPPO | 1 | 3907 | 0.000 | 0.000 | 0.000 |
| Single-Graph MAPPO | 2 | 3907 | 0.000 | 0.000 | 0.000 |
| MAPPO/no-graph | 0 | 3907 | 0.000 | 0.000 | 0.000 |
| MAPPO/no-graph | 1 | 3907 | 0.000 | 0.000 | 0.000 |
| MAPPO/no-graph | 2 | 3907 | 0.000 | 0.000 | 0.000 |

Only one EA checkpoint had a non-zero delayed-recovery rate at the strict
`min_step=80` threshold, so the current existing checkpoints do not provide a
strong formal delayed-recovery signal.

## Threshold Sensitivity

The same episode data were checked with lower minimum post-failure chain-closure
thresholds:

| Method | Best at min step 50 | Best at min step 60 | Best at min step 80 |
| --- | --- | --- | --- |
| EA-RG-MAPPO-S | seed1/update2200: 0.400 | seed1/update3800: 0.200 | seed1/update3800: 0.200 |
| Single-Graph MAPPO | seed2/update2200: 0.800 | seed2/update2200: 0.800 | 0.000 |
| MAPPO/no-graph | seed1/update2400: 1.000 | seed1/update2300: 0.600 | 0.000 |

This shows that lower thresholds reintroduce early geometric-intercept behavior.
Several baseline successes occur shortly after failure start and before step
80, which makes them poor evidence for sustained post-failure task-chain
recovery.

## Interpretation

The current `dropout030_delay2_relay_failure` setting has a confound:

- with a loose threshold, fast interception during the failure interval can look
  like recovery;
- with a strict threshold, recovery becomes too sparse for the existing
  checkpoints.

Therefore the next step is not to claim the current sweep as paper evidence.
It should be treated as a development diagnostic showing that the final protocol
must separate kill-chain recovery from early geometry-driven interception.

## Next Action

Freeze a small scenario suite instead of searching for a single favorable
scenario:

- `dropout030_delay2_relay_failure_early`
- `dropout030_delay2_relay_failure`
- `dropout030_delay2_relay_failure_delayed`
- `dropout030_delay2_relay_failure_late`

Then retrain all methods under the same protocol and use validation-only
checkpoint selection before any held-out test evaluation. If the strict delayed
metric remains too sparse, the paper should report both:

- legacy post-failure recovery as a broad operational metric;
- delayed recovery or recovery-survival curves as a mechanism hardening metric.

Do not continue adding stress conditions only until EA-RG-MAPPO-S wins.

For the frozen multi-scenario protocol, validation should use:

```text
--selection-group suite
```

Test evaluation must consume the suite-selected validation checkpoint CSV.
