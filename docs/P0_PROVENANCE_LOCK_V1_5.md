# P0 Provenance Lock — v1.5 (pre-survival)

- locked: 2026-08-07
- tag: `paper-v1.5-pre-survival`
- purpose: single source of truth for manuscript HEAD, result locks, and protocol versions.
  After the survival analysis (P1), this document is updated and a new tag
  `paper-v1.6-survival-locked` is created. All figures, tables, and claims MUST derive from
  this canonical HEAD; no mixing of older snapshots.

## Provenance fields

| field | value |
|---|---|
| MANUSCRIPT_HEAD_SHA | `04a6b06` (branch `codex/project-state-20260802`, main worktree `ri_gmappo_uav`) |
| MANUSCRIPT_HEAD_TAG | `paper-v1.5-pre-survival` |
| RESULTS_PROTOCOL_VERSION | v1.5 (pre-registered protocol chain, frozen) |
| TRAINING_SEEDS | 3 (n_seed = 3 is the independent statistical unit) |
| HELD_OUT_BASE_SEED | 745669 (evaluated once) |
| HELD_OUT_RESULTS_LOCK | `formal-held-out-results-lock-v1.5.1` (10,800 episodes, 27 checkpoints, 27/27 audit) |
| ROBUSTNESS_RESULTS_LOCK | `formal-robustness-results-lock-v1.5.0` (10,500 episodes, 210/210, RPG verdict REMOVE/simplify) |
| EFFICIENCY_RESULTS_LOCK | `formal-efficiency-results-lock-v1.5.0` (5 methods × 5 blocks, OVERALL PASS) |
| GATE_PRIOR_MECH_LOCK | `gate-prior-mechanism-results-lock-v1.5.0` (SUPPORT) |
| TASK_SUPPORT_MECH_LOCK | `task-support-mechanism-results-lock-v1.5.0` (EMPIRICAL SUPPORT ONLY) |
| CANONICAL_DATA | `docs/paper_assets_v1_5/canonical_results_v1_5.csv` (single numeric source) |
| SURVIVAL_PROTOCOL_VERSION | pending (`docs/statistics/survival_protocol_v1_0.md`, next step) |

## Standing rules (frozen)

1. No retraining unless: (a) implementation bug in the formal runs; (b) baseline fairness
   cannot be fixed by renaming; (c) explicit decision to enter P3-B/P4.
2. No new network modules, no tuning to beat HAPPO, no redundant small ablations.
3. No Abstract headline lock before the P1 Decision Gate.
4. Statistical unit = training seed (n=3). Episodes are within-seed samples; effect size +
   uncertainty + seed consistency is the reporting standard, not p-value chasing.
5. `param_matched_single` is a DATA key (kept for provenance); its PAPER label is
   "wider single-graph baseline" (higher-capacity single-relation encoder) — NOT
   "parameter-matched" (Full 117,302 vs 84,694 is not matched).
6. Task domain label: "Heterogeneous UAV Cooperative Interception" (kill-chain /
   scout-relay-attacker); the phrase "Multi-UAV Semantic Search" is removed from title and
   keywords.
