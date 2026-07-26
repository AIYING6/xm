# P1 Training Protocol Standardization

Generated: 2026-07-24

## Purpose

Start P1 from `docs/FINAL_Q1_SINGLE_PAPER_PLAN.md` after the first P0 information-boundary hardening passed.

This document defines the first paper-facing configuration skeleton for formal training. It does not launch long training by itself.

## Config Directory

Created:

```text
configs/paper/
```

The files are JSON-compatible YAML so they can be read by normal YAML tools later while also being auditable with Python standard-library `json` now.

## Scenario Config

Main scenario:

```text
configs/paper/main_gate1.yaml
```

It records:

- 3DOF strict-sensing 3v1 task;
- target-information bottleneck;
- relay failure;
- communication dropout test condition;
- message-cache TTL and confidence;
- environment-step training budget definition;
- validation/test seed policy;
- primary and secondary metrics.

## Method Configs

Created:

```text
configs/paper/mappo.yaml
configs/paper/single_graph.yaml
configs/paper/ea_rg_mappo.yaml
configs/paper/param_matched_single.yaml
configs/paper/happo.yaml
configs/paper/ippo.yaml
configs/paper/ablation_no_role_pair.yaml
configs/paper/ablation_no_task_support.yaml
configs/paper/ablation_no_role_identity.yaml
```

Important decision:

```text
HAPPO is a priority external strong baseline attempt for the Q1 target.
```

It has a stop rule: if it cannot pass smoke, BC compatibility, fair PPO training, and evaluation within 3-5 focused engineering days, the blocker must be documented and the minimum defensible package becomes IPPO/MAPPO/Single-Graph/Parameter-Matched Single plus EA-RG-MAPPO.

## Audit Script

Created:

```text
scripts/audit_paper_configs.py
```

It verifies:

- required config files exist;
- configs parse as JSON-compatible YAML;
- the budget unit is `environment_steps`;
- the 1M-step update approximation is at least 1M environment steps;
- required method configs are present.

## Next Work

## Command Manifest

Created:

```text
scripts/generate_paper_commands.py
```

It reads `configs/paper/` and generates training command manifests:

```text
results/paper_command_manifest.csv
docs/paper_command_manifest.md
```

Current supported modes:

- `smoke`;
- `probe_20`;
- `dev_1m`;
- `formal_bstar`.

`probe_20` is a short launch-readiness and runtime-estimation mode only. It is not paper evidence.

The first generated smoke manifest initially included:

- `mappo`: ready;
- `single_graph`: ready;
- `ea_rg_mappo`: ready;
- `happo`: pending implementation with the final-plan stop rule.

This has since been upgraded: HAPPO training smoke and validation/test checkpoint-sweep smoke have both passed, so HAPPO can move into the same `dev_1m` development-budget lane as the other main baselines.

## Config-Driven Smoke Result

The generated smoke commands were executed for:

```text
mappo
single_graph
ea_rg_mappo
```

All three produced one-update training logs under:

```text
results/paper_config_runs/smoke/
```

This verifies that the P1 config chain can generate executable commands for the existing MAPPO/single/full graph methods after the P0 edge-feature hardening.

The command generator also supports validation/test checkpoint sweeps via:

```text
--include-sweeps
```

Generated `dev_1m` manifest example:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/generate_paper_commands.py --mode dev_1m --methods mappo single_graph ea_rg_mappo happo --seeds 0 1 2 --include-sweeps
```

Result:

```text
commands: 20
```

The manifest includes:

- 12 training commands for MAPPO, Single-Graph, EA-RG-MAPPO, and HAPPO;
- 4 validation-sweep commands;
- 4 test-sweep commands.

Each test-sweep command includes `--selection-csv <validation_selected_checkpoints.csv>`, so final testing is explicitly tied to validation-selected checkpoints instead of selecting on test episodes.

## Remaining Work

P1 is not complete yet. Next steps:

1. review and dry-run the generated `dev_1m` commands before launching long training;
2. launch first development-budget training for MAPPO, Single-Graph, EA-RG-MAPPO, and HAPPO through the manifest runner;
3. run validation sweeps and select checkpoints;
4. run test sweeps only through validation-selected checkpoints.

## Manifest Runner

Created:

```text
scripts/run_paper_manifest.py
scripts/audit_paper_manifest.py
docs/paper_manifest_runner.md
```

The runner executes selected rows from `results/paper_command_manifest.csv`, replaces `python` with the active interpreter, saves stdout/stderr logs, and appends run status to:

```text
results/paper_manifest_run_status.csv
```

This gives the project a reproducible execution ledger for later 1M/2M/5M/10M training.

`scripts/audit_paper_manifest.py` checks the generated manifest before launch, including method/seed coverage, strict-sensing flags, relay-failure flags, unique training output directories, and validation-only checkpoint selection for final test sweeps.

Current dev_1m manifest audit:

```text
manifest rows: 20
train rows: 12
validation_sweep rows: 4
test_sweep rows: 4
paper manifest audit passed
```

The audited dev_1m manifest covers MAPPO, Single-Graph, EA-RG-MAPPO, and HAPPO with seeds 0, 1, and 2.

## Probe-20 Readiness

Recorded in:

```text
docs/paper_probe20_readiness.md
```

The 20-update launch-readiness probe passed for:

- MAPPO/no-graph seed 0;
- Single-Graph MAPPO seed 0;
- EA-RG-MAPPO seed 0;
- HAPPO seed 0.

The HAPPO probe initially exposed a parser mismatch for shared fairness/protocol arguments. After fixing `scripts/train_happo_baseline.py`, the HAPPO probe passed.

Smoke validation:

```text
python scripts/run_paper_manifest.py --kind train --method mappo --seed 0 --status ready --limit 1 --python-exe D:/Anaconda/envs/.conda/envs/cac/python.exe
```

Result:

```text
completed return_code=0
results/paper_manifest_run_status.csv
results/paper_manifest_logs/smoke_0000_train_mappo_seed0.stdout.txt
results/paper_manifest_logs/smoke_0000_train_mappo_seed0.stderr.txt
```

## Provenance

Created:

```text
scripts/write_paper_run_provenance.py
```

Generated:

```text
results/paper_run_provenance.csv
docs/paper_run_provenance.md
```

It hashes 24 critical config/code files, including:

- `configs/paper/`;
- 3DOF environment;
- RI/EA-RG-MAPPO implementation;
- training/evaluation scripts;
- P1 audit/command scripts.

This is the first formal run-provenance hook for future 1M/2M/5M training.

## Checkpoint-Selection Schema

Created:

```text
configs/paper/checkpoint_selection_schema.yaml
scripts/audit_checkpoint_selection_schema.py
```

The schema fixes:

- validation/test checkpoint summary columns;
- selected-checkpoint columns;
- episode-metrics prefix columns;
- selection policy.

Current audit result:

```text
checkpoint selection schema audit passed
summary columns: 27
selection columns: 22
episode columns: 58
```

Selection policy:

```text
validation split selects checkpoints;
test split evaluates selected validation checkpoints only;
test results must not be used for checkpoint or hyperparameter selection.
```

The provenance file was regenerated after adding the schema, HAPPO trainer, HAPPO evaluator, HAPPO checkpoint-sweep evaluator, manifest runner, manifest audit, and training-output audit. It now hashes 26 critical config/code files.

## HAPPO Smoke

Created:

```text
scripts/train_happo_baseline.py
docs/happo_baseline_smoke.md
```

Current status:

```text
HAPPO training smoke passed.
HAPPO validation/test checkpoint-sweep smoke passed.
```

The implementation is a 3DOF no-graph external baseline with one actor/critic per blue UAV and sequential PPO updates over agents.
