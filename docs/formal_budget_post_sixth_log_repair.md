# Formal Budget Post-Sixth Log Repair

Last updated: 2026-07-30

## Context

During the first formal 1M PPO budget launch, several long-running chunks exceeded the Codex command timeout while the underlying training processes may have continued writing logs. Later resumed chunks could therefore append rows after an older background process, causing duplicate or nonmonotonic `update` rows in some `train_log.csv` files.

This is a training-operation artifact, not a model-definition change. Checkpoints are not deleted or rewritten.

## Code Changes

- `scripts/run_formal_post_sixth_1m_chunk.ps1`
  - `Get-LastUpdate` now reads the maximum valid `update` in `train_log.csv`.
  - This prevents resumed chunks from moving backward when the last CSV row is out of order.

- `scripts/check_formal_post_sixth_1m_progress.py`
  - Progress is now reported by maximum valid `update`.
  - Latest eval is selected by highest eval update.
  - Duplicate and nonmonotonic logs are reported as warnings.

- `scripts/repair_formal_post_sixth_1m_logs.py`
  - Normalizes each formal 1M `train_log.csv`.
  - Keeps the last row for each duplicate update.
  - Sorts rows by update.
  - Writes `train_log.csv.bak_unsorted` before modifying a log.
  - Does not touch checkpoints.

## Required Local Validation

Run:

```powershell
D:/Anaconda/envs/.conda/envs/cac/python.exe -m py_compile scripts/check_formal_post_sixth_1m_progress.py scripts/repair_formal_post_sixth_1m_logs.py
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/repair_formal_post_sixth_1m_logs.py --dry-run
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/repair_formal_post_sixth_1m_logs.py
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/check_formal_post_sixth_1m_progress.py
```

## Decision

Do not continue formal PPO chunks until the repair script has been run and the progress checker no longer reports duplicate or nonmonotonic log warnings.

After the repair, resume each method/seed from the maximum existing update using:

```powershell
.\scripts\run_formal_post_sixth_1m_chunk.ps1 -Method <method> -Seed <seed>
```
