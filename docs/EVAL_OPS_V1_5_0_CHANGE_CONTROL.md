# formal-ablation-eval-ops-v1.5.0 — Change Control

**Created:** 2026-08-05
**Branch:** ablation-v1.5-train
**Base:** formal-ablation-freeze-v1.5.1 (a048e91) + formal-ablation-ops-v1.5.0 (076667e)
**Tag:** `formal-ablation-eval-ops-v1.5.0`

## 1. Scope (evaluation-only)

Implements the frozen v1.5 checkpoint-selection policy
(`docs/V1_5_CHECKPOINT_SELECTOR_ADJUDICATION.md`, SHA
`868C4DF3...`; split freeze `docs/V1_5_VALIDATION_SPLIT_FREEZE.md`,
validation_base_seed=641939).

Files changed (evaluation tooling only; no model / env / PPO / BC change):

- `scripts/evaluate_3d_checkpoint_sweep.py`
  - new `wilson_lower_95`, `failure_exposure_stats`, `parse_time`, `_to_int`
  - per-scenario summary rows now carry:
    `failure_exposed_count`, `recovered_given_exposure_count`,
    `recovery_given_exposure`, `wilson_lower_95`, `estimate_unstable`,
    `time_to_recovery_given_exposure`, `time_to_success`, `selection_policy`
  - suite aggregation pools exposure counts across the 4 scenarios and
    recomputes the Wilson lower bound on the pooled k/n
  - `select_checkpoints` gains `--selection-policy v1_5_wilson`: eligibility
    collision<=0 AND failure_exposed_count>0; ranking
    `(wilson95 up, success up, recovery-time down, success-time down,
    checkpoint_update up)`; raises when no v1.5-eligible checkpoint exists
  - `SELECTION_COLUMNS` / `SUMMARY_COLUMNS` extended (v1.4 columns preserved)
- `scripts/evaluate_happo_checkpoint_sweep.py`
  - identical exposure statistics (failure step from the scenario definition)
    and identical `select_checkpoints` (shared function)
  - same `--selection-policy` argparse
- `tests/test_selection_v1_5_wilson.py` — 13 regression tests for the frozen
  v1.5 rule (Wilson maths, ranking order, tie-break, collision/exposure
  eligibility, N<10 flag, suite pooling, HAPPO identity)
- `scripts/evaluate_ri_gmappo_3d.py` — `build_config` now forwards
  `role_gate_prior_strength` and `role_pair_gate_fixed_value` into the model
  config (fix: without this, evaluating the w/o Role-Pair Gate ablation would
  fall back to fixed gate 0.5 instead of sigmoid(0.4)=0.598687660112452)
- `scripts/evaluate_3d_checkpoint_sweep.py` — argparse gains
  `--role-gate-prior-strength` / `--role-pair-gate-fixed-value`

## 2. What is NOT changed

- v1.4 frozen results, checkpoints, selection CSVs (untouched)
- `formal-post-sixth-eval-ops-v1.4.2` tag and code (not moved)
- training code, environments, PPO, BC, ablations
- v1.5 validation seed 641939 has NOT been run by this version

## 3. Preflight (dev seed 888000, 3 episodes, single scenario)

All passed:

- Full EA-RG (v1.4) checkpoint: loaded 74/0, Wilson fields correct
- w/o Gate Prior (v1.5) checkpoint: loaded 74/0
- no_graph: loaded 28/0
- HAPPO: loaded 84/0, identical selection schema to the main chain

Manual Wilson check: k=3/n=3 -> wilson_lower_95 = 0.438494, matches the
formula; estimate_unstable=1 for n<10 as frozen.

## 4. Test status

- `tests/test_selection_v1_5_wilson.py`: 13/13 PASS
- `tests/test_checkpoint_selection_v1_4_1.py`: 18/18 PASS (v1.4 unchanged)
- `tests/test_ablation_semantics_v1_5.py`: 7/7 PASS
- Total 38/38 PASS

## 5. Boundary

No formal validation, no held-out test, no robustness evaluation has been run
with this version. Formal v1.5 validation uses base_seed=641939 (not 120000,
not 888000), 4 scenarios, 50 episodes, all 24 method-seed groups, serial.
