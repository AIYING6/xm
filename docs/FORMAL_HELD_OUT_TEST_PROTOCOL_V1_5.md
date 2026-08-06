# FORMAL_HELD_OUT_TEST_PROTOCOL_V1_5

> Status: FROZEN — this protocol defines the one-shot formal held-out test for
> the v1.5 study (9 methods, 27 checkpoints). Once the test runs, no method,
> checkpoint, budget, scenario, reward, BC, or safety parameter may be changed
> based on the test results (per `formal_protocol_freeze.md`).

---

## 1. Scope

One-shot held-out evaluation of the **27 locked checkpoints** (9 methods x 3
training seeds). This is the final core experiment that determines paper
positioning. It is NOT validation (no selection happens) and NOT a
development run.

```
MAPPO TRAINING/VALIDATION COMPLETE
27-checkpoint joint held-out manifest (24 v1.5 + 3 MAPPO) frozen
-> run held-out test ONCE on a brand-new split
-> freeze raw outputs
-> 27/27 held-out audit
-> unified statistics
-> 3-color decision (green/yellow/red)
```

## 2. Frozen evidence chain

| Asset | Lock / Tag |
| --- | --- |
| MAPPO BC | `mappo-bc-freeze-v1.5.0 @ 05c9847` |
| MAPPO PPO entry (role_onehot fix) | `mappo-ppo-freeze-v1.5.0 @ 3d5346d` |
| MAPPO training audit | `mappo-ppo-training-lock-v1.5.0 @ 989e338` |
| MAPPO 641939 validation | `mappo-validation-lock-v1.5.0 @ ec08b50` |
| Original 8-method validation (24 ckpt) | `formal-ablation-validation-lock-v1.5.0 @ 65bd96c` |
| 27-checkpoint joint manifest | built by `build_mappo_joint_27_manifest.py` |
| Eval implementation (MAPPO) | `mappo-freeze-v1.5.0 @ 11fa019` (`evaluate_mappo_v1_5.py`) |
| Eval implementation (8 methods) | `formal-ablation-eval-ops-v1.5.0 @ 9e48fe7` |
| Held-out eval ops (selector-skip fix) | `held-out-eval-ops-v1.5.1` (see addendum below) |

`evaluate_mappo_v1_5.py` SHA256 (frozen, unchanged by audit-script commits):
`C4F969DAF54EE7B6E7429B40A6B35D47FB6C7560450298D3EC595C4752F678B4`

## 3. Held-out split

### 3.1 Base seed (deterministic, no cherry-picking)

The split base seed is derived deterministically from the joint manifest and a
fixed anchor string, so the test split cannot be chosen to favor any method:

```
anchor = SHA256_hex(joint_held_out_manifest_27.csv) + "formal-held-out-v1.5"
h = SHA256(anchor)                                     # hex, uppercase
candidate = (int(h[0:8], 16) % 900000) + 100000        # range 100000..999999
while candidate in {888000, 120000, 641939}:
    candidate = ((candidate + 1) % 900000) + 100000
base_seed = candidate
```

Computed values:

```
joint_held_out_manifest_27.csv SHA256 = 0C4CA4F2A2DCA077EDBBA2949D74CA1D8B200811B6946D8A9C897E7D79E1DEA0
seed-derivation hash                = E00E7C255D236509259DEA8F869D7A7D2EB7F6F4E841201BA60A5C8B19E7460E
HELD-OUT BASE SEED                  = 745669
```

`745669` has never been used for training, BC, smoke, `888000`, `120000`,
`641939`, or any prior validation/test.

### 3.2 Episode seed derivation

Episode seeds are derived identically to validation (matched episodes):

```
episode_seed = base_seed + episode_index
```

All 27 checkpoints evaluate the SAME 100 episode seeds per scenario
(`episode_index = 0..99`), guaranteeing matched-episode comparability across
methods.

### 3.3 Scenarios (frozen, same family as validation)

```
dropout030_delay2_relay_failure_early
dropout030_delay2_relay_failure
dropout030_delay2_relay_failure_delayed
dropout030_delay2_relay_failure_late
```

### 3.4 Test volume

```
27 checkpoints x 4 scenarios x 100 episodes = 10,800 episodes
```

## 4. Inputs: the 27 locked checkpoints

The exclusive test input list is the frozen joint manifest:

```
results/paper_config_runs/formal_mappo_v1.5_validation_selector_v1.5.1_20260806/
  _operator_notes/final_mappo_validation_audit_v1_5/
    joint_held_out_manifest_27.csv      (27 rows: method, train_seed, update,
                                         checkpoint, sha256, ...)
```

- No re-scanning of training directories.
- No checkpoint selection. No new "selected checkpoint" is produced.
- Every one of the 27 checkpoint SHA256 must match the manifest before the
  test starts (input SHA audit, step 6.1).

## 5. Evaluation settings (frozen)

| Setting | Value |
| --- | --- |
| split | `test` |
| base_seed | `745669` |
| scenarios | the 4 scenarios above |
| episodes per scenario | `100` |
| eval batch size | `1` |
| deterministic action | argmax of actor logits (same as validation) |
| strict target sensing | enabled |
| agent target info bottleneck | enabled |
| device | `cuda` |
| execution | serial, single Scheduled Task |
| selection policy | NONE (no selection in held-out) |

Execution method: each (method, seed) checkpoint is evaluated through the
corresponding frozen evaluation entrypoint with `--split test` and
`--checkpoint-updates` set to that checkpoint's locked update (27 serial
calls from one orchestrator). This avoids modifying the frozen evaluation
implementations.

Method -> entrypoint mapping (frozen):

| Method | Entrypoint |
| --- | --- |
| full_ea_rg / ablations / no_graph / single_graph / param_matched_single | `evaluate_3d_checkpoint_sweep.py` (`--split test`) |
| happo | `evaluate_happo_checkpoint_sweep.py` (`--split test`) |
| mappo | `evaluate_mappo_v1_5.py` (`--split test`) |

## 6. Gate / audit / freeze sequence

### 6.1 Input SHA audit (before running)

- 27/27 checkpoint paths exist (resolved across the two worktrees:
  `ri_gmappo_uav_ablation_v1.5` for the 24 v1.5 checkpoints,
  `ri_gmappo_uav_mappo_v1.5` for the 3 MAPPO checkpoints).
- 27/27 file SHA256 == `joint_held_out_manifest_27.csv` entries.
- Failure to match => STOP; do not hand-fix.

### 6.2 Run

- Single-instance Scheduled Task, serial, `--split test`, base_seed 745669,
  100 episodes/scenario, 4 scenarios, 27 checkpoints = 10,800 episodes.
- No `_smoke` assets, no reuse of prior output directories.

### 6.3 Freeze raw outputs

- Raw episode/summary files frozen with SHA256 immediately after completion.

### 6.4 Held-out audit (27/27)

- 10,800 episode rows; per-method 4 scenarios x 100 episodes complete.
- No NaN/Inf/traceback; no missing updates; no cross-checkpoint leakage.
- Statistical unit = training seed (3 seeds per method; per-seed reporting,
  mean +/- SD, worst seed).

### 6.5 Unified statistics

For every method, report (per seed AND 3-seed mean +/- SD):
success, recovery-given-exposure, recovered/exposed counts, Wilson interval,
time-to-recovery, time-to-success, collision, worst seed, and Full-minus-rival
per-seed deltas.

Primary comparisons:
- Strong baselines: Full vs MAPPO; Full vs HAPPO; Full vs param_matched_single
- Structural baselines: Full vs no_graph; Full vs single_graph
- Ablations: Full vs w/o Gate Prior; Full vs w/o Task-Support; Full vs w/o Role-Pair Gate

## 7. No-reselection / failure policy

- **No checkpoint reselection on the test split** — inputs are fixed.
- **No checkpoint replacement based on test results.**
- A failed task (non-zero exit, incomplete rows, SHA mismatch, duplicate
  instance, missing scenario, NaN/Inf, traceback) stops the process. Do NOT
  hand-pick results to fill gaps; the whole group (or the affected task) must
  be re-run from the frozen inputs, never partially patched.
- Selection from validation is never recomputed from held-out data.

## 8. Decision thresholds (3-color gate, applied AFTER unified statistics)

- **Green** (promote to zone-1 upgrade package): Full in top reliability
  tier + >=15-20% faster recovery/completion vs MAPPO/HAPPO/param-matched +
  advantage widens under strong perturbations + Gate Prior and Task-Support
  contributions reproduce.
- **Yellow** (safe zone-2): Full reliability on par with strong baselines +
  stable ~8-15% speed lead (or clearly more stable under some perturbation)
  + collision not worse + at least one ablation module effective.
- **Red** (simplify or v1.6): Full not better on reliability/speed/robustness
  vs MAPPO/HAPPO/param-matched and ablation gaps vanish.

## 9. Freeze marker

This document + the held-out split manifest + the 27-checkpoint input SHA
audit are committed and tagged before any held-out evaluation runs.

Tag: `held-out-eval-ops-v1.5.0`

## Addendum A (2026-08-07): selector-skip fix for held-out (ops v1.5.1)

### Root cause (attempt01 failure)

The first held-out attempt ran 5/27 groups then stopped at
`w_o_gate_prior/seed2` with a non-zero exit. Diagnosis on the isolated copy
(`results/paper_config_runs/_failed_attempts/
formal_held_out_v1_5_10800_20260807_attempt01`) showed:

- episode rows: 400/400 (4 scenarios x 100), unique keys, no NaN/Inf; split=test
- summary rows: 4/4, update=977, selection_policy=v1_5_wilson
- `test_selected_checkpoints.csv` missing; IN_PROGRESS left; Task LastResult=1

Replaying the frozen selector on the isolated summary reproduced the failure
deterministically:

```
RuntimeError: no collision-eligible checkpoint for split=test, scenario=scenario_suite,
graph_encoder=multi_relation, ..., train_seed=2
```

Cause: `w_o_gate_prior/seed2` has `collision_mean=0.01 > 0` on the early
scenario under the held-out split; the suite-aggregated collision exceeds the
`--max-selection-collision-rate 0.0` gate, so the validation selector (which
the frozen eval entrypoints always invoked) raised and aborted the whole task.
Held-out must record locked checkpoints faithfully even when a checkpoint would
not be *selectable*; it must never depend on the selector.

### Fix (minimal, held-out semantics)

- `evaluate_3d_checkpoint_sweep.py`, `evaluate_happo_checkpoint_sweep.py`,
  `evaluate_mappo_v1_5.py`: on `--split test`, skip `select_checkpoints`
  entirely (`selected_rows = []`); validation behavior is unchanged.
- The selection CSV is still written as an empty mechanical artifact and is
  NEVER used for any decision.
- Both worktree copies of `evaluate_3d_checkpoint_sweep.py` were patched
  (ablation + MAPPO) because MAPPO's `evaluate_mappo_v1_5.py` imports the
  local copy.
- New tests `tests/test_held_out_selector_skip.py` (7 cases) verify:
  - split=test never calls the selector (3 entrypoints),
  - split=validation still calls it (3 entrypoints),
  - a collision-bearing suite summary still raises on the validation selector
    path (root-cause regression).
- Verified: 52/52 MAPPO test suite; test-split smoke with the previously
  failing `w_o_gate_prior/seed2` checkpoint completes exit=0 with empty
  selection CSV.

### Impact on the attempt

The failed attempt01 was preserved in full (SHA-frozen) as evidence and is
NOT used as a formal result. The formal held-out test must be re-run as a
single one-shot task with a fresh output root and the same frozen split
(base_seed 745669, 27 checkpoints, 4 scenarios x 100 episodes = 10,800).

Ops tag for this addendum: `held-out-eval-ops-v1.5.1`.
