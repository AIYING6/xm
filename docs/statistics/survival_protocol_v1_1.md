# Survival Protocol v1.1 — censor-aware post-failure recovery analysis

- status: **FROZEN** (tag: `survival-protocol-v1.1`)
- frozen: 2026-08-07, BEFORE running the formal KM/RMST (the four definition fixes below
  were identified by a data-semantics audit, not by inspecting results)
- local file SHA256: `b2500d768f77c753652c76ffbbfe4805a818543586ff0c95339d52313d3a84dd`
  (the sandbox execution used the same rules with SHA `453d1011b914b7451d3cd12ef62e121928c70e9fa08d72584663f7fb719267ea`; the two files are not byte-identical but encode the same frozen rules)
- supersedes: `survival-protocol-v1.0`
- upstream: P0 provenance lock (paper-v1.5-pre-survival). No retraining.

## 1. v1.0 → v1.1 definition fixes (frozen before running)

1. **Failure exposure is `steps >= node_failure_start_step`** (the frozen evaluation code
   definition), not "scenario scheduled a failure".
2. **Recovery clock is the stable-window start**: the code first computes
   `stable_window_start = max(node_failure_start_step, first_chain_step - attack_hold_steps + 1)`
   and sets `recovery_steps = stable_window_start - node_failure_start_step`.
   `post_failure_first_chain_step` is the confirmation/terminus of the 4-step stable
   window, not the t_rec clock used by the paper.
3. **Exposure structure is scenario-dependent** (audited):

   | scenario | failure start | episodes | exposed |
   |---|---|---:|---:|
   | Early | 25 | 2,700 | 2,700 |
   | Nominal | 40 | 2,700 | 2,700 |
   | Delayed | 55 | 2,700 | 343 |
   | Late | 70 | 2,700 | 329 |

   Delayed/Late exposure varies by method (audited: full 8, mappo 40, no_graph 204, …),
   so pooling all four scenarios yields a landmark-selection problem.
4. **Primary population = Early + Nominal only**: every (method, seed, scenario) cell has
   exactly 100 exposed episodes; scenario composition is perfectly matched (54/54 cells).

## 2. Time origin / event / censoring (unchanged from v1.0)

- t = 0 := `node_failure_start_step`.
- T := `stable_window_start − node_failure_start_step` for recovered episodes
  (`post_failure_chain_recovered = 1`); event δ = 1.
- Otherwise right-censored at C := `steps − node_failure_start_step`; δ = 0.
- Collision: primary = horizon censoring; sensitivity = collision as competing terminal
  outcome (collisions ≤ 0.0008 in held-out; reported separately).

## 3. τ_primary (frozen before results)

- Environment horizon = 260. Early follow-up = 260−25 = 235; Nominal follow-up = 260−40 = 220.
- **τ_primary := 220** = min over the primary scenarios of the common complete follow-up.
- RMST(τ) = ∫₀^τ S(t) dt via per-seed Kaplan–Meier.

## 4. Required outputs (all four)

1. Recovery probability (terminal reliability) — kept.
2. **Conditional mean recovery time** E[T | recovered] — renamed (per protocol v1.0 §6).
3. Kaplan–Meier curve (pooled + per-seed).
4. Primary RMST(220) per (method, seed); mean ± SD over seeds; per-seed Δ_s listed fully.

## 5. Sensitivity (pre-registered, not headline)

- τ ∈ {50, 80, 100, 150, 190, 220}; task rationale for τ = 80: node-failure active
  duration = 80 steps, i.e., recovery while the failed node is still down.
- Hierarchical paired bootstrap: resample seeds, then episodes within seed × scenario,
  same episode index for Full and comparator; B = 10,000; RNG seed = 20260807.

## 6. Statistical unit and reporting

- n_seed = 3 independent replications; episodes are within-seed samples.
- Effect size + uncertainty + seed consistency; no p-value chasing.

## 7. Decision Gate (frozen wording; run AFTER results)

- **A (broad faster recovery)**: RMST_Full < RMST of MAPPO/HAPPO/single with good seed
  consistency → "fast post-failure recovery with high terminal reliability".
- **B (competitive overall RMST)**: Full clearly better than MAPPO and wider single-graph,
  close to HAPPO → drop the "34% faster than HAPPO" headline.
- **C (early/front-loaded)**: RMST(50)/RMST(100) clearly better but full-horizon not →
  "front-loaded post-failure recovery".
- If none holds cleanly: conservative comparator/time-scale claim (documented in the
  Decision Memo).

## 8. Role-Pair Gate verdict rule

- Full clearly better than w/o RPG → "associated with faster recovery dynamics but
  slightly lower terminal reliability".
- Close → "limited independent benefit".
- w/o RPG better → "the simpler no-RPG variant remains competitive or preferable".

## 9. Deliverables

- `docs/statistics/survival_results_v1_1/`
  - `survival_data_audit.csv` (11 checks)
  - `rmst_seedwise.csv`, `rmst_summary.csv`, `sensitivity_rmst.csv`,
    `hierarchical_bootstrap.csv`
  - `km_recovery_curve_primary.png`, `km_recovery_curve_primary_per_seed.png`
  - `survival_report_v1_1.md`, `P1B_DECISION_MEMO_V1_1.md`
