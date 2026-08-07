# P3-A OOD Generalization Protocol v1.0

- status: **FROZEN** (tag: `p3a-ood-protocol-v1.0`); frozen BEFORE any OOD performance is viewed.
- scientific question (only):
  > Does task-graph relational coordination retain its early post-failure recovery behavior
  > under distribution shifts absent from training, formal held-out evaluation, and the
  > existing robustness suite?
- upstream locks (mandatory references):
  - `paper-v1.6-p2.5-content-ready` (manuscript), `formal-held-out-results-lock-v1.5.1`,
    `survival-protocol-v1.1`, `robustness-results-lock-v1.5.0`.

## 1. Methods (fixed)

- Primary: EA-RG Full, MAPPO, HAPPO, Wider Single-Graph.
- Optional 5th (budget-permitting): w/o Task-Support — mechanism-only question, does NOT
  enter the primary Decision Gate.
- NOT run: w/o Role-Pair Modulation (adjudicated "limited independent benefit" in P1;
  further OOD budget on it has low information gain), no-graph, single-graph, w/o Gate Prior.
- Assets: every (method, training seed, checkpoint) has its SHA256 recorded in the results
  manifest. **Zero-shot evaluation only; no retraining; no fine-tuning; no checkpoint
  reselection.** No checkpoint re-selection even if a cell looks poor.

## 2. OOD families (7 pre-registered cells)

| cell | family | definition | env capability (audited) |
|---|---|---|---|
| G1 | geometry | initial blue formation rotated + spacing scaled (e.g., 20° rotation, 1.2× spacing) | eval-side init config (to add) |
| G2 | geometry | target initial relative bearing/range shift (e.g., range ×1.4, bearing +25°) | eval-side init config (to add) |
| M1 | maneuver | target `weaving` (sinusoidal turn+alt) | **already implemented** (`weaving`) |
| M2 | maneuver | target `break_turn` (reactive turn away) | **already implemented** (`break_turn`) |
| C1 | comm topology | spatially structured link suppression (e.g., west-sector links pruned) | eval-side comm config (to add) |
| C2 | comm topology | asymmetric link availability (directional loss pattern) | eval-side comm config (to add) |
| J1 | joint | G1(moderate) × M1(moderate) × C1(moderate) — each at its moderate level, NOT hardest×hardest×hardest | composition of the above |

- Non-overlap rule: G/M/C parameters must lie OUTSIDE the union of the training / held-out /
  R00–R09 parameter support. Documented in the P3-A.0 support-range audit appendix:
  - training & held-out & robustness use `target_policy = straight` → M1/M2 unseen;
  - initial geometry is deterministic-fixed in reset → G1/G2 unseen;
  - comm perturbations in R00–R09 are range/dropout/delay scalars → C1/C2 (topology
    patterns) unseen.
- Severity is kept low (2 per family + 1 joint), NOT a new robustness benchmark.

## 3. Failure exposure (designed, not post-hoc)

- Failure onset fixed early (same logic as the formal early scenario, onset=25).
- Preflight check (BEFORE any performance is viewed): exposure rate ≥ 99% in every
  (method × seed × cell); if a cell fails, revise the OOD generation rule, re-freeze the
  protocol, and only then run. No post-hoc exposure handling.

## 4. Survival setup (inherited from P1, no new metric)

- t = 0 := failure onset; event := start of the stable task-chain closure window
  (formal recovery clock, `stable_window_start - onset`); unrecovered → right censored at
  `steps - onset`; horizon = 260.
- τ_common := 220 (the largest complete post-failure follow-up shared under onset ≤ 40;
  equals P1's primary horizon; structurally fixed, not selected post-hoc).
- Collision: primary = horizon censoring (P1 convention); sensitivity = competing
  terminal outcome; collision rate reported separately.

## 5. Primary estimand (aggregate, cell-weight-invariant)

Per seed s and cell c:
\[
\Delta_{s,c}^{80} = \mathrm{RMST}^{80}_{\mathrm{Full},s,c} - \mathrm{RMST}^{80}_{\mathrm{MAPPO},s,c}
\]
Aggregate over all pre-registered cells (equal weight):
\[
\Delta_s^{\mathrm{OOD}} = \frac{1}{C}\sum_{c=1}^{C}\Delta_{s,c}^{80}, \qquad
\bar{\Delta}^{\mathrm{OOD}} = \frac{1}{3}\sum_s \Delta_s^{\mathrm{OOD}}
\]
The headline does NOT depend on any single cell. Family-level summaries
Δ_G, Δ_M, Δ_C, Δ_J are secondary and may NOT be cherry-picked as the headline.

## 6. Mandatory four metrics (per method × seed × cell)

1. Terminal recovery P_rec.
2. Conditional mean recovery time E[T_rec | recovered] (named "conditional", never as
   unconditional).
3. Primary early recovery RMST(80).
4. RMST(τ_common=220).

## 7. Roles of comparators

- Primary statistical contrast: **Full vs MAPPO** (P1's most reproducible comparator).
- HAPPO and Wider Single-Graph = strong-reference comparators: does EA-RG stay
  competitive / degrade / only beat MAPPO? NO requirement that Full beats all three.

## 8. Statistical unit and inference

- n_seed = 3. Report seed-wise Δ_s^{OOD}, mean ± sample SD, paired deltas; hierarchical
  paired bootstrap (resample seeds, then episodes within seed × cell, matched episode
  index, B = 10,000, RNG 20260807) as supplement. Same evaluation randomness across
  methods where possible (matched episode resampling).

## 9. Pre-registered Decision Gate (three tiers)

- **Gate A (generalization supported)**: aggregate Δ̄^{OOD}_80 < 0 with 3 seeds largely
  consistent, no family shows a clear reversal, uncertainty supports the early-recovery
  advantage → claim "EA-RG's early post-failure recovery advantage over MAPPO persists
  across unseen geometry, maneuver, and communication-topology shifts" (joint shift noted
  separately).
- **Gate B (partial/family-dependent)**: aggregate favorable but some family clearly
  reverses → "the early-recovery advantage generalizes to selected distribution shifts but
  is not invariant across OOD families" (list which persist / vanish). Publishable.
- **Gate C (distribution-dependent)**: aggregate no longer supports the advantage →
  "EA-RG's early-recovery advantage is distribution-dependent and does not consistently
  persist under unseen shifts." No retraining, no OOD redesign, no severity re-selection;
  lock the result.

## 10. w/o Task-Support (if run)

- Single question: does the task-dependent relation retain an empirical contribution under
  OOD? Report RMST80_Full vs RMST80_w/oTS. Report honestly even if w/o TS is better.
- No further ablations (no Gate Prior / RPG / no-graph) in P3-A.

## 11. Experiment scale

- 4 methods × 3 seeds × 7 cells × 100 episodes = 8,400 episodes (with w/o TS: 10,500).
- No 500/1000 episodes per cell; independent replication remains n=3.

## 12. Execution order

```
P3-A.0  support-range audit (done: G fixed-init, M straight-only, C scalar-only)
P3-A.1  this protocol (frozen) + commit/tag p3a-ood-protocol-v1.0
P3-A.2  env eval-side extensions (G/C configs) + exposure preflight only (no performance)
P3-A.3  formal zero-shot evaluation (4 methods × 3 seeds × 7 cells)
P3-A.4  audit → RMST80 + RMST220 → seed-level + bootstrap → Decision Gate → LOCK
```
Final results tag (regardless of outcome): `p3a-ood-results-lock-v1.0`.

## 13. Deliverables

- `docs/statistics/p3a_ood_results_v1_0/`
  - `p3a_preflight_exposure.csv`, `p3a_cell_summary.csv` (4 metrics × cells),
    `p3a_seedwise_rmst.csv`, `p3a_aggregate.csv`, `p3a_bootstrap.csv`,
    `p3a_decision_memo.md`, `p3a_ood_manifest.csv` (checkpoint SHA256).
