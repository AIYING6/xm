# Paper Asset Build Report

Generated: 2026-08-11T23:19:21

Purpose:

```text
Regenerate paper tables/figures from existing result files and run non-training validation gates.
This script does not retrain policies or rerun long evaluation jobs.
```

## Summary

| Step | Status |
|---|---|
| Runtime environment report | OK |
| Checkpoint inventory | OK |
| Submission action register | OK |
| Experiment extension decision plan | OK |
| Supplemental data README | OK |
| Submission readiness report | OK |
| Submission package manifest | OK |
| English manuscript readiness audit | FAILED |

## Step Details

### Runtime environment report

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/write_runtime_environment_report.py
```

stdout:

```text
D:\Code\Codex\ri_gmappo_uav\docs\runtime_environment_report.md
```

### Checkpoint inventory

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/write_checkpoint_inventory.py
```

stdout:

```text
D:\Code\Codex\ri_gmappo_uav\docs\checkpoint_inventory.md
```

### Submission action register

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/write_submission_action_register.py
```

stdout:

```text
D:\Code\Codex\ri_gmappo_uav\results\submission_action_register.csv
D:\Code\Codex\ri_gmappo_uav\docs\submission_action_register.md
items: 10
blocked: 2
deferred: 1
open: 7
```

### Experiment extension decision plan

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/write_experiment_extension_decision_plan.py
```

stdout:

```text
D:\Code\Codex\ri_gmappo_uav\results\experiment_extension_decision_plan.csv
D:\Code\Codex\ri_gmappo_uav\docs\experiment_extension_decision_plan.md
options: 7
blocked: 1
deferred: 3
ready: 3
```

### Supplemental data README

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/write_supplemental_data_readme.py
```

stdout:

```text
D:\Code\Codex\ri_gmappo_uav\docs\supplemental_data_readme.md
```

### Submission readiness report

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/write_submission_readiness_report.py
```

stdout:

```text
D:\Code\Codex\ri_gmappo_uav\docs\submission_readiness_report.md
```

### Submission package manifest

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/write_submission_package_manifest.py
```

stdout:

```text
D:\Code\Codex\ri_gmappo_uav\docs\submission_package_manifest.md
```

### English manuscript readiness audit

Status: `FAILED`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/audit_english_manuscript_readiness.py
```

stdout:

```text
D:\Code\Codex\ri_gmappo_uav\docs\english_manuscript_readiness_audit.md
```
