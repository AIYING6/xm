# Gate Prior Mechanism Protocol v1.5

- status: **FROZEN** (freeze tag: `gate-prior-mechanism-protocol-freeze-v1.5.0`)
- frozen at: 2026-08-07
- scope: mechanism analysis ONLY. Does NOT re-open held-out / robustness / efficiency locks.
- All comparison objects, metrics, checkpoint nodes, and interpretation boundaries below are
  pre-registered. Any change requires a new protocol revision.

## 0. Objective and boundary

Q: why does the role-pair gate *initialization prior* (logit init 0.4) improve optimization
stability and worst-seed behavior?

- This is NOT a re-evaluation of task performance. Held-out (locked) already shows:
  Full recovery 0.971 ± 0.021 vs w/o-Gate-Prior 0.772 ± 0.244 (3-seed, ddof=1).
- Concept boundary (frozen, must be respected in the paper):
  - `role_pair_gate` = learned **static** role-pair embedding, NOT a failure-conditioned dynamic gate.
  - Claimable: Gate Prior is an initialization/optimization prior over static role-pair
    modulation; its observed role is training stability and cross-seed consistency.
  - NOT claimable: Gate Prior dynamically adapts communication to failures.

## 1. Comparison objects (locked)

| method | role_gate_prior_strength | logit init | initial sigmoid gate |
|---|---|---|---|
| Full (`ea_rg_mappo_s_gate_prior`) | 0.4 | +0.4 | sigmoid(0.4) = 0.59868766 |
| w/o Gate Prior (`w_o_gate_prior`) | 0.0 | 0.0 | sigmoid(0.0) = 0.5 |

- Architecture identical on the gate axis: `role_pair_gate = nn.Embedding(num_roles*num_roles, out_dim=hidden=64)`
  inside each of 3 `RoleConditionedGraphAttentionLayer`s (perception/communication/task-support relations).
- Aggregate unit for reporting = (relation, role-pair) gate mean over the 64 hidden dims
  => 3 relations x 16 pairs = **48 gate values**. Raw scalar population = 48 x 64 = 3072.

Data sources (locked paths, 3 seeds x 2 methods = 6 runs):
- Full: `D:/Code/Codex/ri_gmappo_uav/results/paper_config_runs/formal_budget_post_sixth_freeze_v1.4_formal_main_20260802/ea_rg_mappo_s_gate_prior/ppo_seed{S}_1m/` (S=0,1,2)
- w/o GP: `D:/Code/Codex/ri_gmappo_uav_ablation_v1.5/results/paper_config_runs/formal_ablation_v1.5_ppo_977_20260804/w_o_gate_prior/ppo_seed{S}_1m/` (S=0,1,2)

## 2. Checkpoint nodes (locked)

- **Main bilateral nodes (all 6 runs exist):** update = {100, 200, 300, 400, 500, 600, 700, 800, 900, 977}.
- **update = 0** (initial) is computed analytically from the locked init rule
  (Full 0.59868766 / w/o 0.5), NOT read from a checkpoint.
- Full-only early nodes {2,4,20,40} and w/o seed0 node {10} are NOT used in bilateral
  main comparison (may appear in raw CSVs only).
- Fault tolerance (pre-registered): if a run misses a node, that node is dropped from the
  bilateral comparison and flagged in the report; the main figures plot only nodes present
  in all compared runs.

## 3. Block 1 — Optimization stability (Full vs w/o GP, always both)

Curves from `train_log.csv`, 977 update rows, eval points at {1, 100, ..., 900}:
- Primary: `eval_success_rate` (eval grid)
- Auxiliary (appendix only): `train_avg_reward`, `policy_loss`, `value_loss`, `entropy`,
  `approx_kl`, `grad_norm`.

Pre-registered statistics (per method, n=3 seeds, sample SD ddof=1):
1. Final-window mean ± SD: per-seed mean of eval_success_rate over the last 3 eval points
   {700, 800, 900}, then 3-seed mean ± SD.
2. Cross-seed SD vs update: SD of the 3 seeds at each eval point.
3. Worst-seed curve: min over seeds at each eval point.
4. Curve AUC: trapezoidal integral of eval_success_rate over eval nodes {1,...,900},
   normalized by update span.
5. First update with success >= 0.9 (on eval grid).
6. First update where K=3 consecutive eval points are all >= 0.9 (K frozen at 3).

Forbidden: cherry-picking a favorable training interval of Full as the main analysis.

## 4. Block 2 — Gate parameter evolution (Full AND w/o GP, bilateral)

Extract `role_pair_gate.weight` from each locked checkpoint node (Section 2). Per node:
- raw logit, sigmoid gate (48 aggregated values + full 3072-scalar population)
- over the 48 values: mean, SD, min, max, mean |gate - initial_gate|
- per-relation means: relation-1 / relation-2 / relation-3 (16 pairs each)
- **gate saturation fraction**: proportion of the 3072 scalars with sigmoid < 0.1 or > 0.9
- **cross-seed trajectory similarity**: at each (method, node), pairwise Pearson correlation
  and mean L2 distance of the 48-dim gate vector across the 3 seeds

Main figures use only the frozen nodes (Section 2).

## 5. Block 3 — Concept boundary (frozen wording)

Gate Prior is an initialization/optimization prior over static role-pair modulation; its
observed role is optimization stability and cross-seed consistency, NOT runtime failure awareness.

## 6. Association analysis (descriptive only, n=3)

- Per-seed gate drift (mean |gate_977 - gate_0|) vs per-seed held-out recovery vs per-seed
  validation recovery.
- n=3: report as descriptive association / qualitative consistency only. NO significance
  claims ("significant correlation" is forbidden).

## 7. Pre-registered verdict (frozen)

- SUPPORT if all: Full gate trajectory more consistent across seeds AND less gate saturation
  AND worst-seed training more stable AND direction consistent with the held-out ablation
  effect => claim "Gate Prior improves optimization stability and cross-seed robustness."
- NEUTRAL if gate trajectories are nearly identical yet performance differs clearly =>
  claim "strong empirical regularization effect; exact parameter-level mechanism inconclusive."
- COUNTER if w/o GP gates are instead more stable => report honestly, no forced explanation.

## 8. Deliverables

- `docs/GATE_PRIOR_MECHANISM_PROTOCOL_V1_5.md` (this file)
- `docs/gate_prior_v1_5_assets/`
  - `gate_prior_training_stability.csv`
  - `gate_prior_gate_trajectory.csv`
  - `gate_prior_gate_summary.csv`
  - `gate_prior_seed_consistency.csv`
  - `gate_prior_mechanism_report.md`
  - figures (exactly 4):
    1. `fig_success_curves.png` (Full vs w/o GP, 3 raw seed lines + mean)
    2. `fig_worst_seed.png`
    3. `fig_gate_evolution.png`
    4. `fig_cross_seed_dispersion.png`
- All CSVs carry schema + provenance (method, seed, update node, metric, value, source lock tag).

---

## Addendum A (frozen 2026-08-07) — gate unit accounting, implementation fact

Frozen after checkpoint inspection; corrects the unit count in Section 1 without
changing any statistic, node list, or verdict rule.

1. `multi_relation_graph` contains **two** stacked graph layers (`layer1`, `layer2`),
   each with 3 relation channels => **6** `RoleConditionedGraphAttentionLayer`s that own a
   `role_pair_gate` (`layer{1,2}.{0,1,2}.role_pair_gate.weight`, shape (25, 64)).
2. Role ids: SCOUT=0, RELAY=1, ATTACKER=2, INTERCEPTOR=3, TARGET=4 => `num_roles=5`,
   Embedding covers 5x5 = 25 pairs (all 25 kept in statistics; unused pairs stay at init).
3. Aggregated gate unit = (layer, relation, pair) mean over 64 hidden dims =>
   **150 values** (6 channels x 25 pairs). Scalar population = 6 x 25 x 64 = 9600.
   Section 1's "48 values" is superseded by 150; all per-node statistics (mean/SD/min/max/
   |gate-initial|, relation grouping, saturation, cross-seed similarity) use the 150-vector
   (or 9600-scalar) definition.
4. Per-relation grouping = 2 layers x 25 pairs = 50 values per relation (layer1+layer2 pooled).
5. Prior-filled pairs (logit init +0.4, sigmoid = 0.59868766), identical in layer1 and layer2:
   - PERCEPTION (r0): (S,T),(R,T),(A,T),(I,T) — 4 pairs
   - COMMUNICATION (r1): (S,R),(R,S),(R,A),(R,I),(A,R),(I,R) — 6 pairs
   - TASK_SUPPORT (r2): (A,S),(I,S),(S,R),(A,R),(I,R),(R,A),(R,I) — 7 pairs
   - total 17 (relation, pair) units x 2 layers = 34 gate channels start at 0.5987;
     the remaining 150-34=116 channels start at sigmoid(0)=0.5.
   (S=scout, R=relay, A=attacker, I=interceptor, T=target; pair=(receiver, sender).)
6. `gate drift |gate - initial_gate|` uses per-channel initial: 0.5987 for the 34
   prior channels, 0.5 otherwise.
7. All other frozen content (Section 2 nodes, Section 3 stats, Section 4 metrics,
   Section 6/7 verdict rules) is unchanged.
