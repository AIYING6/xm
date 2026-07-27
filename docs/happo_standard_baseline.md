# HAPPO Baseline Status

Last updated: 2026-07-26

## Current Status

`scripts/train_happo_baseline.py` now implements a no-graph heterogeneous-policy HAPPO baseline with sequential agent updates and the previous-agent joint-ratio correction in the clipped PPO surrogate.

The implemented policy loss is:

```text
L_i = -E[min(M_i * r_i * A_i, M_i * clip(r_i, 1-eps, 1+eps) * A_i)]
M_i = product of post-update ratios from agents updated before i
```

Each blue UAV has its own actor and centralized critic. The baseline intentionally does not use graph message passing, role-pair gates, edge features, or multi-relation task-support structure.

## Evidence Boundary

Formal paper comparisons may use HAPPO only for runs generated after this correction.

Older `happo` outputs produced by the previous sequential PPO-style implementation are historical diagnostics. They should not be mixed with post-correction HAPPO checkpoints in validation, test, tables, or manuscript claims.

## Validation Completed

- `python -m py_compile scripts/train_happo_baseline.py scripts/evaluate_happo_3d.py scripts/evaluate_happo_checkpoint_sweep.py scripts/audit_paper_configs.py`
- `python -m pytest tests/test_happo_policy_loss.py -q`
- `python scripts/audit_paper_configs.py`
- one-update 3DOF HAPPO training smoke under `results/happo_standard_smoke/`
- refreshed `results/paper_command_manifest.csv`
- `python scripts/audit_paper_manifest.py`
- `python scripts/audit_checkpoint_selection_schema.py`
- `python -m pytest tests/test_gate1_communication_feasibility.py tests/test_happo_policy_loss.py -q`

## Next Use

Restart the HAPPO dev-1M run from a clean post-correction output directory before using it as a formal external baseline. Existing MAPPO, Single-Graph, and EA-RG-MAPPO runs can continue from their current checkpoints; HAPPO should be treated as needing a corrected rerun.

The paper command manifest writes corrected HAPPO checkpoints under:

```text
results/paper_config_runs/<mode>/runs/happo_standard/bc_ppo_seed<seed>/
```

The older directory below is retained only for historical diagnostics:

```text
results/paper_config_runs/<mode>/runs/happo/bc_ppo_seed<seed>/
```
