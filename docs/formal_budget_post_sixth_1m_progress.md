# Formal Budget Post-Sixth 1M Progress

Last updated: 2026-07-30

## Purpose

This tracks the formal 1M PPO budget study after the sixth-review protocol
freeze. These are in-training progress records, not final validation or test
evidence.

Output root:

```text
results/paper_config_runs/formal_budget_post_sixth_freeze/
```

Target budget:

```text
977 updates ~= 1M environment transitions with 8 envs * 128 rollout steps
```

## Execution Tools

Recommended resumable launcher:

```powershell
.\scripts\run_formal_post_sixth_1m_chunk.ps1 -Method <METHOD> -Seed <SEED>
```

Progress checker:

```powershell
& "D:/Anaconda/envs/.conda/envs/cac/python.exe" scripts/check_formal_post_sixth_1m_progress.py
```

## Current Progress

All `15/15` formal PPO method/seed tasks have reached at least update `20` and
have valid latest model and training-state checkpoints.

| Method | Seed | Update | Percent | Checkpoint | Last eval success | Collision | Timeout |
|---|---:|---:|---:|---|---:|---:|---:|
| no_graph | 0 | 20 | 2.0 | ok | 0.0 | 0.0 | 0.0 |
| no_graph | 1 | 20 | 2.0 | ok | 0.0 | 0.0 | 0.0 |
| no_graph | 2 | 29 | 3.0 | ok | 0.0 | 0.0 | 0.0 |
| single_graph | 0 | 20 | 2.0 | ok | 0.0 | 0.0 | 1.0 |
| single_graph | 1 | 20 | 2.0 | ok | 0.4 | 0.0 | 0.6 |
| single_graph | 2 | 24 | 2.5 | ok | 0.0 | 0.0 | 0.0 |
| param_matched_single | 0 | 20 | 2.0 | ok | 1.0 | 0.0 | 0.0 |
| param_matched_single | 1 | 20 | 2.0 | ok | 1.0 | 0.0 | 0.0 |
| param_matched_single | 2 | 24 | 2.5 | ok | 0.0 | 0.0 | 1.0 |
| ea_rg_mappo_s_gate_prior | 0 | 20 | 2.0 | ok | 1.0 | 0.0 | 0.0 |
| ea_rg_mappo_s_gate_prior | 1 | 20 | 2.0 | ok | 0.6 | 0.0 | 0.4 |
| ea_rg_mappo_s_gate_prior | 2 | 24 | 2.5 | ok | 0.2 | 0.0 | 0.8 |
| happo | 0 | 20 | 2.0 | ok | 0.0 | 0.0 | 0.0 |
| happo | 1 | 26 | 2.7 | ok | 0.0 | 0.0 | 0.0 |
| happo | 2 | 24 | 2.5 | ok | 0.0 | 0.0 | 0.0 |

The early online evaluation rows use only 5 monitor episodes and should not be
interpreted as method ranking.

## Next Execution Plan

Advance all runs in balanced chunks:

1. Bring every method/seed pair to update `100`.
2. Check for NaN, missing checkpoints, persistent collision spikes, and training
   stalls.
3. Continue balanced chunks to updates `200`, `400`, `600`, `800`, and `977`.
4. Only after all `15/15` runs reach update `977`, run the frozen validation
   checkpoint sweep.

Do not run held-out test during this stage.
