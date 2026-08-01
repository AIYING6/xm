# Freeze Rehearsal Plan

Last updated: 2026-08-02

## Purpose

Run a low-cost end-to-end rehearsal before any expensive formal experiment
freeze.

This rehearsal verifies command generation, audited manifest execution,
checkpoint production, validation-only checkpoint selection, test-only
evaluation of selected checkpoints, schema audit, and artifact gates.

Rehearsal evidence is not paper evidence.

## Frozen Rehearsal Scope

Methods:

- `mappo`
- `single_graph`
- `ea_rg_mappo`
- `happo`

Seed:

- `0`

Budget:

- mode: `freeze_rehearsal`
- updates: `200`
- `num_envs`: `4`
- `rollout_steps`: `64`
- approximate environment steps per method: `51,200`
- budget ratio relative to the 1M-step setting: about `5.12%`
- checkpoint/eval interval: `20`

Evaluation:

- validation scenarios: frozen four-scenario relay-failure suite from
  `configs/paper/main_gate1.yaml`
- test scenarios: same scenario suite, disjoint base seed
- validation episodes per scenario/checkpoint: `5`
- test episodes per scenario/selected checkpoint: `5`

## Command Manifest

Generated manifest:

```text
results/freeze_rehearsal_command_manifest.csv
docs/FREEZE_REHEARSAL_COMMAND_MANIFEST.md
```

Generation command:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/generate_paper_commands.py --mode freeze_rehearsal --methods mappo single_graph ea_rg_mappo happo --seeds 0 --include-sweeps --out-csv results/freeze_rehearsal_command_manifest.csv --out-md docs/FREEZE_REHEARSAL_COMMAND_MANIFEST.md
```

Audit command:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/audit_paper_manifest.py --manifest results/freeze_rehearsal_command_manifest.csv --methods mappo single_graph ea_rg_mappo happo --seeds 0
```

Dry-run commands:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/run_paper_manifest.py --manifest results/freeze_rehearsal_command_manifest.csv --python-exe D:/Anaconda/envs/.conda/envs/cac/python.exe --dry-run
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/run_paper_manifest.py --manifest results/freeze_rehearsal_command_manifest.csv --python-exe D:/Anaconda/envs/.conda/envs/cac/python.exe --status ready_after_training --dry-run
```

## Execution Order

1. Run the four `train` rows.
2. Audit training outputs before sweeps.
3. Run the four `validation_sweep` rows.
4. Run `scripts/audit_checkpoint_selection_schema.py`.
5. Run the four `test_sweep` rows.
6. Run `scripts/audit_checkpoint_selection_schema.py` again.
7. Run `scripts/check_reproducibility_artifacts.py`.
8. Update this document and `docs/PROJECT_STATE.md` with pass/fail status.

## Pass Criteria

The rehearsal passes only if:

- all four methods produce training logs and snapshot checkpoints;
- validation sweep produces `validation_selected_checkpoints.csv` for every
  method;
- test sweep consumes only the validation selection CSV;
- checkpoint-selection schema audit passes;
- reproducibility artifact gate passes;
- no information-boundary regression is introduced;
- failures, if any, are documented before formal training decisions.

## Current Status

Partially executed.

Completed checks:

- command manifest generated with 12 rows;
- manifest audit passed;
- training rows dry-run passed;
- validation/test sweep rows dry-run passed.
- MAPPO seed 0 train row completed:
  - 200 updates;
  - 10 policy snapshots from update 20 to update 200;
  - training output audit passed;
  - training log summary passed and was written to
    `results/freeze_rehearsal_training_summary.csv`.
- MAPPO validation sweep completed:
  - validation selected update 40;
  - checkpoint-selection schema audit passed.
- MAPPO test sweep completed:
  - test consumed only the validation selection CSV;
  - checkpoint-selection schema audit passed;
  - reproducibility artifact gate passed.
- Single-Graph seed 0 train row completed:
  - 200 updates;
  - 10 policy snapshots from update 20 to update 200;
  - training output audit passed;
  - training log summary was updated in
    `results/freeze_rehearsal_training_summary.csv`.
- Single-Graph validation sweep completed:
  - validation selected update 180;
  - checkpoint-selection schema audit passed.
- Single-Graph test sweep completed:
  - test consumed only the validation selection CSV;
  - checkpoint-selection schema audit passed;
  - reproducibility artifact gate passed.
- EA-RG-MAPPO seed 0 train row completed:
  - 200 updates;
  - 10 policy snapshots from update 20 to update 200;
  - training output audit passed;
  - training log summary was updated in
    `results/freeze_rehearsal_training_summary.csv`.
- EA-RG-MAPPO validation sweep completed:
  - validation selected update 100;
  - checkpoint-selection schema audit passed.
- EA-RG-MAPPO test sweep completed:
  - test consumed only the validation selection CSV;
  - checkpoint-selection schema audit passed;
  - reproducibility artifact gate passed.

Remaining rehearsal execution:

- `happo` seed 0 train, validation sweep, and test sweep;
- final all-method training-output audit;
- final schema and reproducibility gates.
