# Freeze Precheck Report

Generated: 2026-08-02T02:52:25

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
M docs/PROJECT_STATE.md
 M docs/TRAINING_EVALUATION_PROTOCOL.md
 M scripts/generate_paper_commands.py
?? docs/FREEZE_REHEARSAL_COMMAND_MANIFEST.md
?? docs/FREEZE_REHEARSAL_PLAN.md
?? results/freeze_rehearsal_command_manifest.csv
```

stderr:

```text

```

