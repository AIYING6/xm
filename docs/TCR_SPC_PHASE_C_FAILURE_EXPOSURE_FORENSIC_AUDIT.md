# TCR/SPC Phase-C Failure-Exposure Forensic Audit

- **Status:** completed; zero training and zero re-evaluation
- **Final classification:** **NATURAL_PRE_TRIGGER_TERMINATION_CONFIRMED**
- **Historical Phase-C decision:** remains **TECHNICAL INVALID** and is not rewritten
- **Audit scope:** all 15 method �� training-seed cells and every failure row with `failure_exposed != 1`
- **Source archive:** `D:\\File\\Downloads\\tcr_spc_phase_c_results.tar.gz`
- **Tape:** Phase-C development tape `440000�C440099`
- **Tape SHA256:** `56adbdc2fda3faf14decd94b45cae9a0b6178760725a6fec391ad671e8a30b65`

## 1. Scope and frozen rule

The audit uses the archived final-checkpoint evaluation artifact only:

`results/development/tcr_spc_phase_c_1m/evaluations/final_1m/raw_episode_metrics.csv`

The frozen Phase-C aggregator treats a cell as exposure-valid when:

`abs(failure_exposure - 1.0) <= 0.01`

and constraint violation is zero. This is a cell-level hard gate. This audit additionally inspects every individual unexposed episode, including episodes in cells whose aggregate exposure still remains above 0.99.

No checkpoint was promoted, no episode was rerun, and no threshold or historical decision was changed.

## 2. Evidence extraction and field semantics

The archived raw schema contains:

- method, training seed, topology condition, episode ID;
- scheduled onset and duration;
- terminal step;
- success, collision, timeout, constraint violation;
- `failure_exposed`;
- path/task-support telemetry.

The raw schema does **not** contain a separate `termination_reason`, `failure_event_triggered`, or per-step relay-trigger state. Therefore:

- termination reason below is derived from the mutually exclusive terminal flags; every audited row has `collision=1`;
- failure scheduled is read from the frozen tape condition and onset/duration;
- failure triggered and `failure_active ever true` are inferred from the evaluator contract: an episode whose terminal step is strictly before onset cannot enter the active interval;
- relay status around trigger is recorded as ��not reached��; there is no post-onset relay state to inspect;
- evaluator trigger state is ��loop terminated before onset; active trace empty��.

This is sufficient to distinguish A from B: B requires an episode to survive to onset while exposure remains false. No such row exists.

## 3. Cell-level audit

The Phase-C tape contains 11 failure conditions �� 100 episodes = 1,100 failure rows per method �� seed cell.

| Method | Seed | Failure rows | Exposed | Unexposed | Exposure |
|---|---:|---:|---:|---:|---:|
| utr_sg | 2002 | 1100 | 1100 | 0 | 1.000000 |
| utr_sg | 2101 | 1100 | 1100 | 0 | 1.000000 |
| utr_sg | 2102 | 1100 | 1100 | 0 | 1.000000 |
| utr_sg | 2103 | 1100 | 1100 | 0 | 1.000000 |
| utr_sg | 2104 | 1100 | 1100 | 0 | 1.000000 |
| spc_sg | 2002 | 1100 | 1100 | 0 | 1.000000 |
| spc_sg | 2101 | 1100 | 1100 | 0 | 1.000000 |
| spc_sg | 2102 | 1100 | 1051 | 49 | 0.955455 |
| spc_sg | 2103 | 1100 | 1100 | 0 | 1.000000 |
| spc_sg | 2104 | 1100 | 1100 | 0 | 1.000000 |
| tcr_sg | 2002 | 1100 | 1100 | 0 | 1.000000 |
| tcr_sg | 2101 | 1100 | 1100 | 0 | 1.000000 |
| tcr_sg | 2102 | 1100 | 1100 | 0 | 1.000000 |
| tcr_sg | 2103 | 1100 | 1088 | 12 | 0.989091 |
| tcr_sg | 2104 | 1100 | 1092 | 8 | 0.992727 |

Summary:

- UTR: 5/5 cells have 1,100/1,100 exposure.
- SPC: 4/5 cells have 1,100/1,100; SPC seed2102 has 1,051/1,100.
- TCR: seed2002, 2101, and 2102 have 1,100/1,100; seed2103 has 1,088/1,100; seed2104 has 1,092/1,100.
- Total unexposed rows: **69**.
- All 69 have `terminal_step < scheduled onset`.
- All 69 have `success=0, collision=1, timeout=0, constraint_violation=0`.

The two cells that caused the historical Phase-C technical-invalid gate are:

- SPC seed2102: 49 unexposed rows, exposure 0.955455.
- TCR seed2103: 12 unexposed rows, exposure 0.989091.

TCR seed2104 has 8 unexposed rows but its aggregate exposure is 0.992727, above the frozen 0.99 cell threshold; it is nevertheless included here because the audit is episode-complete.

## 4. Classification result

### A �� NATURAL_PRE_TRIGGER_TERMINATION

All 69/69 unexposed episodes satisfy:

[
\\text{terminal step} < \\text{scheduled failure onset}
]

and terminate with collision. Consequently:

- failure event was scheduled: **yes**;
- failure event was triggered: **no**, because the environment never reached the onset step;
- failure-active ever true: **no** in the evaluator trace;
- exposure flag: **0**;
- relay status around trigger: **not applicable; no trigger was reached**;
- termination reason: **collision before failure onset**.

### B �� EVALUATOR_OR_TRIGGER_DEFECT

**0 episodes.**

There is no archived row with `terminal_step >= onset` and `failure_exposed=0`. Therefore the artifact does not support an evaluator-trigger defect.

### C �� UNRESOLVED_INCONSISTENCY

**0 episodes.**

Every unexposed row is explained by the same observable relation: collision termination strictly before the scheduled onset.

## 5. Complete episode-level audit

Each row below is one unique method �� seed �� condition �� episode record. `scheduled`, `triggered`, `active`, and evaluator-state columns use the evidence semantics defined in Section 2.

| Method | Seed | Condition | Episode | Onset | Duration | Terminal | Reason | S | C | T | Constraint | Scheduled | Triggered | Active ever | Exposure | Relay around trigger | Evaluator trigger state | Class |
|---|---:|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---|---|---|---:|---|---|---|
| spc_sg | 2102 | f0_seen_44_80 | 440003 | 44 | 80 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | f0_seen_44_80 | 440030 | 44 | 80 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | f0_seen_44_80 | 440049 | 44 | 80 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | f0_seen_44_80 | 440062 | 44 | 80 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | f0_seen_44_80 | 440081 | 44 | 80 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | timing_36_80 | 440003 | 36 | 80 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | timing_36_80 | 440030 | 36 | 80 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | timing_36_80 | 440049 | 36 | 80 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | timing_36_80 | 440062 | 36 | 80 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | timing_36_80 | 440081 | 36 | 80 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | timing_52_80 | 440003 | 52 | 80 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | timing_52_80 | 440030 | 52 | 80 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | timing_52_80 | 440049 | 52 | 80 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | timing_52_80 | 440062 | 52 | 80 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | timing_52_80 | 440081 | 52 | 80 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | timing_60_80 | 440003 | 60 | 80 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | timing_60_80 | 440030 | 60 | 80 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | timing_60_80 | 440049 | 60 | 80 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | timing_60_80 | 440062 | 60 | 80 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | timing_60_80 | 440071 | 60 | 80 | 52 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | timing_60_80 | 440081 | 60 | 80 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | timing_60_80 | 440087 | 60 | 80 | 52 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | duration_44_40 | 440003 | 44 | 40 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | duration_44_40 | 440030 | 44 | 40 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | duration_44_40 | 440049 | 44 | 40 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | duration_44_40 | 440062 | 44 | 40 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | duration_44_40 | 440081 | 44 | 40 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | duration_44_60 | 440003 | 44 | 60 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | duration_44_60 | 440030 | 44 | 60 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | duration_44_60 | 440049 | 44 | 60 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | duration_44_60 | 440062 | 44 | 60 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | duration_44_60 | 440081 | 44 | 60 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | duration_44_100 | 440003 | 44 | 100 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | duration_44_100 | 440030 | 44 | 100 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | duration_44_100 | 440049 | 44 | 100 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | duration_44_100 | 440062 | 44 | 100 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | duration_44_100 | 440081 | 44 | 100 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | duration_44_120 | 440003 | 44 | 120 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | duration_44_120 | 440030 | 44 | 120 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | duration_44_120 | 440049 | 44 | 120 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | duration_44_120 | 440062 | 44 | 120 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | duration_44_120 | 440081 | 44 | 120 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | compound_60_120 | 440003 | 60 | 120 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | compound_60_120 | 440030 | 60 | 120 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | compound_60_120 | 440049 | 60 | 120 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | compound_60_120 | 440062 | 60 | 120 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | compound_60_120 | 440071 | 60 | 120 | 52 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | compound_60_120 | 440081 | 60 | 120 | 28 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| spc_sg | 2102 | compound_60_120 | 440087 | 60 | 120 | 52 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| tcr_sg | 2103 | timing_60_80 | 440026 | 60 | 80 | 52 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| tcr_sg | 2103 | timing_60_80 | 440071 | 60 | 80 | 53 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| tcr_sg | 2103 | timing_60_80 | 440078 | 60 | 80 | 53 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| tcr_sg | 2103 | timing_60_80 | 440087 | 60 | 80 | 52 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| tcr_sg | 2103 | timing_60_80 | 440089 | 60 | 80 | 53 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| tcr_sg | 2103 | timing_60_80 | 440099 | 60 | 80 | 53 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| tcr_sg | 2103 | compound_60_120 | 440026 | 60 | 120 | 52 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| tcr_sg | 2103 | compound_60_120 | 440071 | 60 | 120 | 53 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| tcr_sg | 2103 | compound_60_120 | 440078 | 60 | 120 | 53 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| tcr_sg | 2103 | compound_60_120 | 440087 | 60 | 120 | 52 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| tcr_sg | 2103 | compound_60_120 | 440089 | 60 | 120 | 53 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| tcr_sg | 2103 | compound_60_120 | 440099 | 60 | 120 | 53 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| tcr_sg | 2104 | f0_seen_44_80 | 440076 | 44 | 80 | 36 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| tcr_sg | 2104 | timing_52_80 | 440076 | 52 | 80 | 36 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| tcr_sg | 2104 | timing_60_80 | 440076 | 60 | 80 | 36 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| tcr_sg | 2104 | duration_44_40 | 440076 | 44 | 40 | 36 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| tcr_sg | 2104 | duration_44_60 | 440076 | 44 | 60 | 36 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| tcr_sg | 2104 | duration_44_100 | 440076 | 44 | 100 | 36 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| tcr_sg | 2104 | duration_44_120 | 440076 | 44 | 120 | 36 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |
| tcr_sg | 2104 | compound_60_120 | 440076 | 60 | 120 | 36 | COLLISION | 0 | 1 | 0 | 0 | yes | no | no | 0 | pre-trigger; no post-onset relay state | evaluator loop ended before onset | A |

## 6. Other possible causes

No other method �� seed cell contains an unexposed failure row. The phenomenon is therefore concentrated in three policy cells:

- SPC seed2102;
- TCR seed2103;
- TCR seed2104.

The shared signature is not a missing scheduled event. It is early collision before the onset window. The concentration is policy-dependent, but the immediate exposure cause is the same natural pre-trigger termination.

## 7. Decision and next action

The permitted final audit classification is:

[
oxed{\\text{NATURAL_PRE_TRIGGER_TERMINATION_CONFIRMED}}
]

Per the authorization:

1. continue with a **zero-training exposure-gate adequacy review**;
2. assess whether requiring near-100% exposure across all timing/duration conditions is scientifically appropriate when some policies terminate before the scheduled intervention;
3. preserve the original Phase-C **TECHNICAL INVALID** result;
4. do not relabel Phase-C as GO;
5. do not start 3M, held-out, canonical, or any new training.

## 8. Provenance

- Frozen contract: `docs/TCR_SPC_PHASE_C_1M_STABILITY_SCREEN_CONTRACT.md`
- Evaluation implementation: `scripts/run_tcr_spc_phase_c_evaluation.py`
- Environment failure semantics: `envs/uav_intercept_3d_env.py`
- Archived raw evaluation: `evaluations/final_1m/raw_episode_metrics.csv`
- Archived historical decision: `evaluations/final_1m/PHASE_C_DECISION.json`
