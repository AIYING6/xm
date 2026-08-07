# Survival Protocol v1.0 — censor-aware post-failure recovery analysis

- status: **FROZEN** (tag: `survival-protocol-v1.0`)
- frozen: 2026-08-07, BEFORE running the formal statistics
- scope: determines the paper's recovery headline via a Decision Gate. Nothing below is
  chosen after looking at the results. Changes require a new protocol revision.
- upstream: P0 provenance lock (paper-v1.5-pre-survival); this analysis does NOT retrain.

## 1. Analysis population

- Only **failure-exposed episodes** from the locked held-out split (base seed 745669).
- In the four held-out scenarios the relay-failure window is always scheduled
  (`node_failure_start_step` fixed), so every episode is failure-exposed.
- Data source (locked): `formal_held_out_v1_5_10800_20260807/held_out_v1.5/{method}/seed{S}/
  test_episode_metrics.csv`, one row per episode, 9 methods x 3 seeds x 4 scenarios x 100
  episodes = 10,800 rows total.
- Statistical unit = **training seed** (n_seed = 3). Episodes are within-seed samples.

## 2. Time origin and event

- Time origin t = 0 := `node_failure_start_step` (relay-failure onset).
- Event time T := `post_failure_first_chain_step` − `node_failure_start_step`
  (first post-failure chain closure, in steps after failure onset). This is the first
  re-establishment of the post-failure task chain, NOT the episode success time.
- Event indicator δ := `post_failure_chain_recovered` (1 if chain recovered before
  episode termination, 0 otherwise).

## 3. Right censoring

- If the episode terminates (timeout / horizon / collision eligibility) before chain
  recovery, the observation is right-censored at C := `steps` − `node_failure_start_step`.
- `post_failure_chain_recovery_steps_censored` is the sanity-check field: for recovered
  episodes it equals T, for censored episodes it equals the observation window C.

## 4. Collision handling

- Collisions are extremely rare (Full: 0.0; ablations/baselines ≤ 0.0008 in held-out).
- Primary analysis: horizon censoring; collision-terminated episodes are treated as
  censored at their termination step (standard single-event framework).
- Sensitivity analysis: collision treated as a competing terminal outcome (episodes
  ending in collision excluded from the primary estimand and reported separately).
- This is a sensitivity check, not a competing-risk method paper.

## 5. Primary estimand and τ

- Per-scenario common follow-up H_s := the maximum observed
  (`steps − node_failure_start_step`) over non-censored episodes of scenario s,
  truncated to the scheduled `node_failure_duration_steps` (80).
- τ_primary := min_s H_s over the four held-out scenarios.
- Primary estimand: RMST(τ_primary) = ∫₀^{τ_primary} S(t) dt, with S(t) = P(T > t)
  estimated by the per-seed Kaplan–Meier estimator.
- If a common τ_primary is too short to be meaningful, fallback (pre-registered):
  scenario-specific RMST_s(τ_s) with τ_s = H_s, aggregated by fixed equal weights
  across scenarios; a pooled RMST over unequal follow-ups is NOT reported.

## 6. Required output (all four, no selection)

1. Recovery probability P_rec = recovered/exposed (terminal reliability) — kept.
2. **Conditional mean recovery time** E[T | recovered] — renamed from the ambiguous
   "mean recovery time"; reported per method as seed-wise mean ± SD.
3. Kaplan–Meier curve S(t) per method (pooled display + per-seed overlay) — shows
   whether Full is better throughout or only front-loaded.
4. Primary RMST(τ_primary), per (method, seed): RMST_{m,s}; reported as
   mean ± SD over seeds, plus the per-seed differences Δ_s = RMST_{Full,s} − RMST_{baseline,s}
   listed explicitly for every seed.

## 7. Sensitivity (pre-registered, not headline)

- τ ∈ {50, 100, 150, τ_primary} are sensitivity windows, NOT used to pick a headline.
- Optional secondary endpoint P(T ≤ 50) (probability of recovery within 50 steps) is
  allowed ONLY if a task rationale (50 steps ≈ missed tactical window) is written into
  the protocol before running — recorded in the companion note if used.

## 8. Statistical reporting standard

- Effect size + uncertainty + seed consistency; seed-wise Δ_s must be fully listed.
- Pooled KM may be drawn; hierarchical/cluster bootstrap (resample seeds, then episodes
  within seeds) may be used as supplement. No p-value chasing.

## 9. Decision Gate (run AFTER results; headline follows data)

- **A (broad faster recovery)**: RMST_Full < RMST_MAPPO, RMST_HAPPO, RMST_single
  AND seed consistency good → headline "fast post-failure recovery with high terminal
  reliability".
- **B (competitive overall RMST)**: Full clearly better than MAPPO and the wider
  single-graph baseline, close to HAPPO → headline "EA-RG substantially accelerates
  recovery relative to MAPPO and the single-graph baseline while remaining competitive
  with HAPPO in censor-aware recovery performance"; drop "34% faster than HAPPO" from
  the abstract headline.
- **C (early/front-loaded)**: RMST(50)/RMST(100) clearly better but full-horizon RMST
  not → headline "front-loaded post-failure recovery" / "earlier concentration of
  successful recovery after failure".

## 10. Role-Pair Gate verdict (decided by P1, not by hand)

- If Full primary RMST clearly better than w/o RPG: "Role-Pair Modulation is associated
  with faster recovery dynamics but slightly lower terminal reliability."
- If close: "Role-Pair Modulation provides limited independent benefit."
- If w/o RPG better: "the simpler no-RPG variant remains competitive or preferable
  under the overall censor-aware recovery metric." — no forced explanation.

## 11. Stop rules

- No retraining; no new modules; no tuning to beat HAPPO; no redundant ablations.
- No Abstract headline lock before the Decision Gate.
- After P1: update P0 provenance → tag `paper-v1.6-survival-locked`, then P2 rewrite.

## 12. Deliverables

- `docs/statistics/survival_results_v1_0/`
  - `km_recovery_curve.png` (pooled + per-seed)
  - `rmst_seedwise.csv` (method, seed, scenario, RMST_τ, event/censor counts)
  - `rmst_summary.csv` (method, RMST mean±SD, Δ_s vs Full per seed)
  - `sensitivity_rmst.csv` (τ ∈ {50,100,150,τ_primary})
  - `survival_report_v1_0.md` (Decision Gate outcome + RPG verdict)
