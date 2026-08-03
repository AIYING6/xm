# Evaluation-Only Change Control — `formal-post-sixth-eval-ops-v1.4.1`

**Date:** 2026-08-04
**Branch:** `eval-ops-v1.4.1` (worktree `D:/Code/Codex/ri_gmappo_uav_eval_v1.4.1`)
**Base commit:** `6f391694ccb12244ba0ba5f453a79bb25cc782a4` (v1.4 training freeze)

This document records the evaluation-only rule unification decided under the
v1.4 checkpoint-selection adjudication (Case C). It exists so the evaluation
tool version is auditable independently of the frozen training evidence.

## 1. Historical conflict

| Rule | Frozen schema intent | Executed code | Result |
|---|---|---|---|
| selection metric | `legacy_recovery` (schema `score` default) | `fresh_info_recovery` (argparse default; rehearsal output; generator omission) | conflict |
| ranking | weighted score formula | multi-dim tuple (recovery, -collision, -steps, success, -update) | conflict |
| tie-break | `larger checkpoint_update` | `-int(checkpoint_update)` (earlier preferred) | conflict |

`audit_checkpoint_selection_schema.py` checked only CSV column structure, so it
did not catch these value-level conflicts. The freeze rehearsal verified only
that the pipeline can run end-to-end; it was not selection-policy approval. The
generator not passing `--selection-metric` was an implementation omission, not a
policy decision. Schema v2 (commit `e4f69d5`) deliberately retained
`legacy_recovery` as the default while adding `fresh_info_recovery` CSV columns.

## 2. Case-C adjudication (minimum deviation)

No single source produced a unique, contradiction-free rule, so a controlled
clarification was registered **before any formal validation/test result
existed**. The frozen rule (full rationale and per-source matrix in the
adjudication record) is a single weighted-score algorithm:

```text
Eligibility      : collision_rate <= 0.0 (higher -> excluded, not part of score)
Selection score  : 1000 * post_failure_chain_recovered_mean
                   + 100 * success_mean
                   - post_failure_chain_recovery_steps_mean
Ranking          : maximise selection_score
Final tie-break  : when scores tie exactly, larger checkpoint_update wins
Grouping         : each train_seed independent
Eligible         : 100, 200, 300, 400, 500, 600, 700, 800, 900, 977
CSV producer     : evaluate_3d_checkpoint_sweep.py::select_checkpoints()
HAPPO            : identical (imports select_checkpoints)
```

No validation/test/robustness result was produced or observed before this
decision. The metric, weight, and tie-break must not be changed later in
response to validation results.

Adjudication record (operator note, not tracked):
`results/paper_config_runs/formal_budget_post_sixth_freeze_v1.4_formal_main_20260802/_operator_notes/v1.4_selection_protocol_adjudication.md`
Final SHA256: `CCDB813C6E545477DEBD39C6D1E5D81C2D454D0CF001F48A5AE43493344E36D7`.

## 3. Changes in this evaluation-only version

Allowed scope (evaluation tooling only):

- `scripts/evaluate_3d_checkpoint_sweep.py`
  - `select_checkpoints`: rank by `(selection_score, +checkpoint_update)` —
    removed the recovery/steps/success lexicographic tuple and the `-update`
    tie-break.
  - argparse defaults aligned to the frozen rule: `--selection-metric
    legacy_recovery`, `--selection-success-weight 100`.
  - `SELECTION_COLUMNS` gains `checkpoint_sha256`; the selected row now records
    the SHA256 of the selected checkpoint file.
- `scripts/evaluate_happo_checkpoint_sweep.py`
  - Same argparse defaults (`legacy_recovery`, `100`); selector shared with the
    main sweep (unchanged import).
- `scripts/generate_paper_commands.py`
  - Sweep commands now explicitly emit `--selection-metric legacy_recovery`,
    `--selection-success-weight 100`, `--max-selection-collision-rate 0.0`
    (no reliance on defaults).
- `configs/paper/checkpoint_selection_schema.yaml`
  - `schema_version` -> `checkpoint_selection_v3_2026_08_04`;
    `selection_columns` gains `checkpoint_sha256`;
    `selection_policy` now states metric, score (weight 100), collision
    threshold 0.0, eligible snapshots, per-seed grouping, HAPPO same rule, and
    the frozen tie-break.
- `scripts/audit_checkpoint_selection_schema.py`
  - Now audits `selection_policy` values and performs row-level selection-CSV
    checks: metric == legacy_recovery, success weight == 100,
    selected update within eligible snapshots, one selection per
    method/seed group, checkpoint file existence, and SHA match.
- `tests/test_checkpoint_selection_v1_4_1.py`
  - 16 regression tests (score wins, later-update tie-break, collision
    exclusion, success weight 100, score-not-lexicographic, per-seed grouping,
    0977 participation, HAPPO shared selector, generator explicit args, audit
    rejection of wrong metric/weight/update/duplicates/tie-break, test mode
    consuming only the selection CSV).

Forbidden (unchanged): model code, environment, PPO, BC, training config,
v1.4 checkpoints, and the formal training result directory
`results/paper_config_runs/formal_budget_post_sixth_freeze_v1.4_formal_main_20260802`.

## 4. Relationship to the v1.4 training freeze

- `formal-post-sixth-freeze-v1.4` and `formal-post-sixth-ops-v1.4.0` point to
  `6f391694…` and are **unchanged**.
- The v1.4 training commit, checkpoints, training states, logs, and formal
  result directory are **completely unchanged** by this version.
- `formal-post-sixth-eval-ops-v1.4.1` marks this evaluation tool version only.
- No validation, test, or robustness evaluation has been run.
