# Formal v1.4 Launch Plan

Last updated: 2026-08-02

## Purpose

Define the launch sequence for the next formal-main experiment cycle after the
corrected five-method freeze rehearsal and clean freeze precheck.

This plan uses the BC-gated formal launchers, not the direct-PPO
`formal_bstar` command manifest path.

## Freeze Identity

Tags to create after this document and launcher defaults are committed:

```text
formal-post-sixth-freeze-v1.4
formal-post-sixth-ops-v1.4.0
```

Formal result root:

```text
results/paper_config_runs/formal_budget_post_sixth_freeze_v1.4_formal_main_20260802
```

The two tags should point to the same clean commit for this cycle. The separate
names preserve the existing distinction between algorithm/protocol provenance
and launcher/tooling provenance.

## Authoritative Methods

Use the five formal-main methods:

- `no_graph`
- `single_graph`
- `param_matched_single`
- `ea_rg_mappo_s_gate_prior`
- `happo`

The paper-facing method identifiers remain documented in
`docs/FORMAL_MAIN_METHOD_SET.md`.

## Launch Order

1. Run `scripts/run_freeze_precheck.py` and require 8 checks, 0 failures, 0
   warnings.
2. Commit all source, config, protocol, and launcher changes.
3. Create the two local freeze tags listed above.
4. Generate/verify all 15 BC initializations:

```text
pwsh -File scripts/run_formal_post_sixth_1m_bc.ps1 -Python D:/Anaconda/envs/.conda/envs/cac/python.exe -Method all -Seed 99 -ResumeValid
```

5. Check BC readiness:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/check_formal_post_sixth_1m_progress.py --expected-tag formal-post-sixth-freeze-v1.4
```

Expected pre-PPO state:

```text
BC loadable = 15/15
BC architecture exact = 15/15
BC manifest valid = 15/15
BC SHA256 match = 15/15
freeze commit match = 15/15
FRESH = 15
READY = 0
COMPLETE = 0
BLOCKED = 0
```

6. Run the 0 -> 2 -> 4 resume validation for every method/seed using
   `scripts/run_formal_post_sixth_1m_chunk.ps1` with small `-TotalUpdates` and
   `-ChunkUpdates` settings before any long run.
7. Advance all 15 PPO runs in controlled chunks toward candidate checkpoints
   `200/400/600/800/977`.
8. Run validation checkpoint selection only after all methods and seeds reach
   the same candidate budget.
9. Do not run held-out test until the shared budget and selected checkpoints
   are frozen.

## Guardrails

- Do not use `scripts/run_formal_post_sixth_1m.ps1` for formal evidence.
- Do not use direct-PPO `formal_bstar` commands for v1.4 formal evidence unless
  the protocol is explicitly changed and re-frozen.
- Do not use `-AllowUnfrozen` for formal evidence.
- Do not use `-Force` unless deliberately discarding a failed BC directory.
- If any BC is `BC_INVALID`, stop and inspect before PPO.
- If any PPO run has log/checkpoint disagreement, treat the training-state
  checkpoint as authoritative and inspect manually before resuming.
