# Formal Main Method Set

Last updated: 2026-08-02

## Purpose

Freeze the method identifiers that should be used for the next formal
experiment cycle.

This document exists because earlier development and rehearsal commands used
`ea_rg_mappo` as the proposed method and did not always include the
parameter-matched single-graph baseline. Those runs remain useful pipeline or
development evidence, but they are not the final formal main method set.

## Formal Main Methods

Use exactly these method identifiers for the main formal experiment:

| Paper role | Method id | Config | Key setting |
|---|---|---|---|
| No-graph MAPPO baseline | `mappo` | `configs/paper/mappo.yaml` | `graph_encoder=no_graph` |
| Ordinary single-graph baseline | `single_graph` | `configs/paper/single_graph.yaml` | `hidden_dim=64` |
| Capacity-control single-graph baseline | `param_matched_single` | `configs/paper/param_matched_single.yaml` | `hidden_dim=96` |
| Proposed method | `ea_rg_mappo_gate_prior` | `configs/paper/ea_rg_mappo_gate_prior.yaml` | output `ea_rg_mappo_s_gate_prior`; `role_gate_prior_strength=0.4` |
| External MARL baseline | `happo` | `configs/paper/happo.yaml` | sequential HAPPO baseline |

## Command Generation

The default method set in `scripts/generate_paper_commands.py` is now
`formal_main`.

Generate formal-main rehearsal commands:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/generate_paper_commands.py --mode freeze_rehearsal --method-set formal_main --seeds 0 --include-sweeps --out-root results/paper_config_runs/freeze_rehearsal_formal_main --out-csv results/freeze_rehearsal_formal_main_command_manifest.csv --out-md docs/FREEZE_REHEARSAL_FORMAL_MAIN_COMMAND_MANIFEST.md
```

Generate formal-budget commands:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/generate_paper_commands.py --mode formal_bstar --method-set formal_main --seeds 0 1 2 3 4 --include-sweeps
```

## Guardrails

- `scripts/audit_paper_configs.py` requires `ea_rg_mappo_gate_prior.yaml` and a
  positive `role_gate_prior_strength`.
- `configs/paper/ea_rg_mappo_gate_prior.yaml` writes outputs under
  `ea_rg_mappo_s_gate_prior` to match the paper method name and existing formal
  launch/progress scripts.
- `configs/paper/param_matched_single.yaml` explicitly inherits PPO
  hyperparameters from `single_graph`.
- `scripts/audit_paper_manifest.py`, `scripts/audit_training_outputs.py`, and
  `scripts/check_training_progress.py` default to the formal main method set.
- Earlier four-method `freeze_rehearsal` runs are pipeline evidence only because
  they used `ea_rg_mappo` rather than `ea_rg_mappo_gate_prior` and omitted
  `param_matched_single`.
