# Freeze Precheck Report

Generated: 2026-08-02T10:16:40

Purpose:

```text
Run the non-training checks required before freeze rehearsal or formal experiment freeze.
FAIL blocks freeze. WARN requires review before creating a freeze tag.
```

## Summary

| Item | Value |
|---|---:|
| Checks | 8 |
| Failures | 0 |
| Warnings | 1 |

## Checks

| Name | Category | Status | Notes |
|---|---|---:|---|
| `docs/INFORMATION_BOUNDARY_AUDIT.md` | protocol_doc | PASS | ok |
| `docs/BASELINE_FAIRNESS_PROTOCOL.md` | protocol_doc | PASS | ok |
| `docs/TRAINING_EVALUATION_PROTOCOL.md` | protocol_doc | PASS | ok |
| `paper config audit` | config | PASS | ok |
| `checkpoint selection schema audit` | config | PASS | ok |
| `information boundary tests` | test | PASS | ok |
| `reproducibility artifact gate` | artifact | PASS | ok |
| `git status clean` | git | WARN | working tree has local changes; commit before formal freeze |

## Attention Items

### git status clean

Status: `WARN`

Command:

```text
git status --short
```

stdout:

```text
M .gitignore
 M configs/paper/ea_rg_mappo_gate_prior.yaml
 M configs/paper/param_matched_single.yaml
 M docs/FREEZE_PRECHECK_REPORT.md
 M docs/FREEZE_REHEARSAL_PLAN.md
 M docs/PROJECT_STATE.md
 M docs/TRAINING_EVALUATION_PROTOCOL.md
 M results/freeze_precheck_audit.csv
 M scripts/audit_paper_configs.py
 M scripts/audit_paper_manifest.py
 M scripts/audit_training_outputs.py
 M scripts/check_training_progress.py
 M scripts/generate_paper_commands.py
?? docs/FORMAL_MAIN_METHOD_SET.md
?? docs/FREEZE_REHEARSAL_FORMAL_MAIN_COMMAND_MANIFEST.md
?? results/freeze_rehearsal_formal_main_command_manifest.csv
```

stderr:

```text

```

