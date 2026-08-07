# Paper Restructure Map — v1.5 (target: 二区可投稿)

- status: working document (not a frozen protocol)
- source manuscript: `paper_latex_3d_en/` (current draft)
- evidence base: all locks below are frozen and referenced by tag.

## 0. Final evidence status (locked, drives everything)

| module | evidence | paper status |
|---|---|---|
| Gate Prior | SUPPORT (cross-seed gate corr 0.962 vs 0.562; AUC 0.545 vs 0.396; first≥0.9 Full 200/200/600 vs w/o 600/500/None) | Core contribution |
| Task-Support | EMPIRICAL SUPPORT ONLY (removal degrades recovery 0.971→0.892, t_rec 10.82→16.14; but pre 0.141→early 0.092→pre-rec 0.090, no post-failure activation rise) | Effective component, restrained mechanism wording |
| Role-Pair Gate | REMOVE/simplify (same params 117,302; same messages; slower 12.05ms; no held-out/robustness gain) | Auxiliary design, ≤1 sentence, no core claim |

New storyline: **task-graph-driven multi-relation representation + state-dependent
edge-feature-modulated attention preserve task-dependency information after failure;
Gate Prior stabilizes role-structured optimization; Task-Support is an empirical
task-dependent relational mask.**

## 1. Title / Abstract direction

- Title candidate (EN): "Task-Graph-Driven Multi-Relation Coordination for Fast
  Post-Failure Recovery in Multi-UAV Semantic Search"
- Keywords: task graph, multi-relation coordination, post-failure recovery,
  multi-UAV semantic search (NO gate-centric keywords).
- Abstract skeleton: (background) MARL recovers but slowly; (method) task graph +
  multi-relation GAT + Gate Prior + Task-Support; (result) near-saturated reliability
  with recovery latency reduced ~38% vs MAPPO, ~34% vs HAPPO, ~59% vs param-matched
  (3-seed means; locked t_rec 10.8 vs 17.4/16.3/26.2); Gate Prior improves cross-seed
  stability. No "全面最高" claim. RPG not presented as a contribution.

## 2. Restructured section outline (target)

1. Introduction
2. Related Work (keep 4 subsections; add task-graph/recovery-latency angle)
3. Problem Formulation (keep, minor)
4. Method (restructure to 3.1–3.7, see §4 below)
5. Experiments — 6 RQs (see §5–§10)
6. Discussion (trade-off framing; RPG honest statement)
7. Conclusion

## 3. Data/Figure/Table map (target ~6–8 items)

### 3.0 LOCKED main held-out table (27 ckpt, 10800 rows; base_seed 745669) — the single
source of truth for all RQ1/RQ2/RQ3 numbers. Do NOT substitute other numbers.

| method | success | recovery | wilson95 | t_succ | t_rec | collision |
|---|---|---|---|---|---|---|
| full_ea_rg | 0.9850±0.0109 | 0.9706±0.0213 | 0.9384±0.0294 | 46.1±0.4 | 10.8±0.6 | 0.0000 |
| w_o_gate_prior | 0.8642±0.1520 | 0.7716±0.2442 | 0.7237±0.2614 | 49.3±1.7 | 15.3±2.5 | 0.0008 |
| w_o_task_support | 0.9392±0.0906 | 0.8918±0.1600 | 0.8536±0.1817 | 49.0±2.8 | 15.0±4.5 | 0.0008 |
| w_o_role_pair_gate | 0.9942±0.0029 | 0.9902±0.0051 | 0.9654±0.0084 | 48.5±4.3 | 13.8±5.6 | 0.0008 |
| no_graph | 0.9358±0.1026 | 0.9113±0.1413 | 0.8809±0.1611 | 100.9±19.7 | 86.6±22.9 | 0.0000 |
| single_graph | 0.7183±0.4428 | 0.6841±0.4618 | 0.6489±0.4606 | 54.4±13.9 | 22.4±19.3 | 0.0008 |
| param_matched_single | 0.9967±0.0058 | 0.9949±0.0087 | 0.9749±0.0114 | 57.6±18.0 | 26.2±23.6 | 0.0000 |
| happo | 1.0000±0.0000 | 1.0000±0.0000 | 0.9820±0.0007 | 49.9±3.0 | 16.3±4.1 | 0.0000 |
| mappo | 0.9708±0.0290 | 0.9471±0.0514 | 0.9114±0.0636 | 51.0±3.6 | 17.4±7.2 | 0.0000 |

NOTE (number audit): earlier working numbers (MAPPO t_rec 15.6, HAPPO 19.8,
param-matched 20.9, w/o TS 16.14) do NOT match the locked audit and must not be used.
Locked t_rec: mappo 17.4±7.2, happo 16.3±4.1, param_matched 26.2±23.6, w/o GP 15.3±2.5,
w/o TS 15.0±4.5, w/o RPG 13.8±5.6.

| item | content | locked source | lock tag |
|---|---|---|---|
| Table 1 | Main held-out: 9 methods × 3 seeds (table above) | held-out audit | held-out-results-lock-v1.5.1 |
| Fig 1 | Method framework (task graph → multi-relation → edge-modulated attention → Gate Prior) | (draw) | — |
| Fig 2 | **Pareto: Recovery↑ × t_rec↓** (Full, HAPPO, MAPPO, param-matched, no_graph, single_graph) | held-out audit (same) | same |
| Table 2 | Ablations: Full / w/o GP / w/o TS / w/o RPG (recovery 0.971/0.772/0.892/0.990; t_rec 10.8/15.3/15.0/13.8) | held-out ablation variants | same |
| Fig 3 | Robustness R00–R09: ΔRecovery, Δt_rec, worst-seed degradation curves | `formal_robustness_v1.5_10500_20260807` | robustness-results-lock-v1.5.0 |
| Table 3 | Efficiency: params, joint-decision latency (batch1/8), e2e env-steps/s, training peak memory, msg stats | `formal_efficiency_v1.5_20260807` | efficiency-results-lock-v1.5.0 |
| Fig 4 | Gate Prior: gate trajectory + cross-seed dispersion (0.962 vs 0.562) | `docs/gate_prior_v1_5_assets/` | gate-prior-mechanism-results-lock-v1.5.0 |
| Fig 5 | Typical failure-recovery trajectories (case examples) | `docs/task_support_v1_5_assets/` case manifest | task-support-mechanism-results-lock-v1.5.0 |
| (Appx) | Task-Support internal windows (pre 0.141 → early 0.092 → pre-rec 0.090); loss/grad_norm curves | task_support / gate_prior assets | same |

## 4. Method section restructure (3.1–3.7)

```
3.1 Problem formulation
3.2 Task graph construction
3.3 Multi-relation graph representation
3.4 State-dependent edge-feature-modulated attention
3.5 Task-Support relation
3.6 Gate Prior and role-pair modulation   (split concepts!)
     - Role-Pair Gate: static learned modulation (auxiliary)
     - Gate Prior: initialization/optimization prior (core)
3.7 Actor-critic optimization
```

Method claims allowed:
- dynamic = state-dependent attention, edge features, relation masks,
  environment communication availability.
Method claims FORBIDDEN (consistency audit must remove from current draft):
- failure-responsive gate; dynamically adapts gate to node failures;
  dynamically activates role pairs according to failures.

## 5. RQ1 — Overall performance (Table 1)

- Report Success, Recovery, Wilson lower bound, t_succ, t_rec, collision.
- Do NOT bold Full success as best (Full success 0.985 is not the max).
- Frame as **reliability–recovery-speed trade-off**, not "best everywhere".

## 6. RQ2 — Does it actually speed up recovery? (MOST IMPORTANT)

- Locked numbers (3-seed mean t_rec): Full 10.8±0.6 vs MAPPO 17.4±7.2 (≈ −38%),
  vs HAPPO 16.3±4.1 (≈ −34%), vs param-matched 26.2±23.6 (≈ −59%). Also note the
  variance gap: Full t_rec SD 0.6 vs rivals 2.5–23.6 (fast AND stable).
- Include Pareto figure (Fig 2).
- Wording: "EA-RG maintains near-saturated recovery reliability while substantially
  reducing the latency of post-failure coordination recovery." (NOT "不牺牲可靠性";
  reliability is not strictly higher than HAPPO/param-matched, so use
  "near-saturated reliability").

## 7. RQ3 — Which components matter? (Table 2)

| variant | recovery | t_rec | success | t_succ |
|---|---|---|---|---|
| Full | 0.9706±0.0213 | 10.8±0.6 | 0.9850±0.0109 | 46.1±0.4 |
| w/o Gate Prior | 0.7716±0.2442 | 15.3±2.5 | 0.8642±0.1520 | 49.3±1.7 |
| w/o Task-Support | 0.8918±0.1600 | 15.0±4.5 | 0.9392±0.0906 | 49.0±2.8 |
| w/o RPG | 0.9902±0.0051 | 13.8±5.6 | 0.9942±0.0029 | 48.5±4.3 |

- Conclusion (state openly): Gate Prior = strong contribution; Task-Support =
  moderate empirical contribution; RPG = **no consistent independent gain**.

## 8. RQ4 — Robustness under strong perturbations (Fig 3)

- NOT "Full dominates". Use: "Full remains competitive under severe communication
  perturbations while preserving fast-recovery characteristics."
- Show ΔRecovery from R00, Δt_rec from R00, worst-seed (not only absolutes).
- RPG: "role-pair modulation does not improve robustness consistently."

## 9. RQ5 — Computational cost (Table 3)

- Honest framing: Full 117k params, 12.05 ms joint decision, 242 env-steps/s,
  71.9 MB training peak. NOT computationally efficient.
- Distinguish computational latency (ms/forward) vs recovery latency (env steps):
  "EA-RG trades additional computational cost for faster task-level recovery."

## 10. RQ6 — Why does Gate Prior work? (Fig 4)

- Body data: cross-seed gate corr 0.962 vs 0.562; AUC 0.545 vs 0.396;
  first ≥0.9: Full 200/200/600, w/o 600/500/None.
- Conclusion sentence (data-supported): "Gate Prior does not drive gates toward
  saturation; it preserves a consistent structured role-pair initialization across
  seeds and reduces optimization drift."
- Task-Support internal mechanism → appendix; body keeps ablation only:
  "Although removing Task-Support degrades held-out recovery and increases recovery
  latency, temporal analysis does not reveal a consistent post-failure activation
  increase; its benefit is supported empirically while the exact temporal mechanism
  remains inconclusive."

## 11. Consistency audit checklist (final pass)

Forbid (search & remove across full text):
- [ ] "dynamic role gate" / "adaptive role-pair gating" / "failure-responsive gate"
- [ ] "dynamically adapts the gate to node failures"
- [ ] "dynamically activates role pairs according to failures"
- [ ] "Task-Support creates an independent communication channel"
- [ ] "without Task-Support there is no task graph"
- [ ] "Full dominates under perturbations"
- [ ] conflating computational latency with recovery latency
- [ ] claiming RPG communication compression (efficiency shows identical msg counts)
- [ ] claiming Full success is best

## 12. Do NOT do (guard rails)

- No architecture change + retrain; no removing RPG to redefine the main method;
- no model re-selection on held-out; no new standard seeds for prettier numbers;
- no forcing a Task-Support "activation enhancement" story;
- no mixing computational vs task recovery efficiency.

## 13. Next steps (二区 track)

① frozen ✅ → ② unified result tables (held-out/ablation/robustness/efficiency)
→ ③ final figures (Pareto, robustness, Gate Prior, trajectories)
→ ④ rewrite Method (drop dynamic-RPG narrative)
→ ⑤ rewrite Experiments (RQ1–RQ6)
→ ⑥ rewrite Abstract/Intro/Contributions (3 contributions)
→ ⑦ full consistency audit (§11)
→ ⑧ target journal fit.
一区 second phase (only after complete 二区 draft): 5 seeds + external comm baseline +
unseen layout/failure generalization.

## 14. Contribution list (rewritten, exactly 3)

1. Task-graph relational coordination (task-dependency structure, not RPG).
2. Fast post-failure coordination recovery (state-dependent edge-feature-modulated
   attention; near-saturated reliability + faster recovery) — the primary experimental
   contribution.
3. Stabilized role-structured optimization (Gate Prior; ablation + parameter-trajectory
   evidence for stability, cross-seed consistency, worst-seed).
Task-Support folded into Contribution 1 (one sentence, no separate hype).
