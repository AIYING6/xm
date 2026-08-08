# P3-A OOD Design Audit (2026-08-08)

- status: AUDIT COMPLETE — informs whether P3-A v1.1 cells are scientifically
  valid, discriminative, and feasible. Does NOT alter the locked
  `p3a-ood-protocol-v1.1` / `p3a-ood-raw-results-lock-v1.0` /
  `p3a-ood-stats-lock-v1.0` (Gate C under the original severe suite remains).
- method: environment-level probing (60 random resets) + trained-policy probing
  (20 episodes/cell with the FROZEN Full and MAPPO checkpoints, deterministic).
  Recovery / RMST were NOT computed; only algorithm-independent feasibility
  proxies (target visibility, attack-window achieved, success, pruned-pair
  dynamic reachability).

## Six-question audit

### 1. Implementation validity — PASS (no implementation error)
- G1/G2 config (spacing 1.20, rotation 20deg, range 1.40, bearing 25deg)
  reach the env config.
- M1/M2 target_policy = weaving / break_turn are active in the env.
- C1/C2 pruning logic is correct: `_ood_prune_links` computed from the longest
  blue-blue XY pair; `comm_adj[dst, src] = 0` removes src->dst; C1 prunes both
  directions, C2 prunes only lower-y -> higher-y.

### 2. Endpoint saturation / discriminability — PROBLEM FOUND (needs independent calibration)
| cell | method | target_visible | attack_window | success |
|---|---|---|---|---|
| G2 | full_ea_rg | 1.00 | 0.00 | 0.00 |
| G2 | mappo | 0.00 | 0.00 | 0.00 |
| M1 | full/mappo | 1.00 | 0.00 | 0.00 |
| M2 | full/mappo | 1.00 | 0.00 | 0.00 |
| J1 | full/mappo | 1.00 | 0.00 | 0.00 |
| C1/C2 | full | 1.00 | 1.00 | 1.00 |
| C1/C2 | mappo | 1.00 | 0.95 | 0.95 |

- G2: target range x1.40 + bearing +25deg puts the target outside MAPPO's
  detection envelope (visible 0.00); Full sees it (1.00) but cannot form an
  attack window either (0.00). The cell sits at a severe saturation boundary.
- M1/M2/J1: trained Full and MAPPO both achieve attack_window = 0.00 and
  success = 0.00. The RMST80 ceiling saturation observed in the formal run is
  severe endpoint saturation with limited discriminability; whether the task is
  genuinely infeasible requires an algorithm-independent oracle calibration
  (hand-coded policy, NOT Full/MAPPO/HAPPO/Wider results).
- C1/C2: both methods can still form attack windows and succeed (Full 1.00,
  MAPPO 0.95). Discriminative and feasible under the evaluated policies.

### 3. Endpoint discriminability — PARTIAL
- C1/C2: discriminative (Full vs MAPPO difference real, comparator-neutral).
- G2/M1/M2/J1: fully saturated (0/0/0), no discrimination power.

### 4. Shift realism — MIXED
- C1/C2 represent a plausible communication-topology degradation.
- G2 range x1.40 may exceed a reasonable deployment shift for the simple
  MAPPO policy (target leaves detection envelope).
- M1/M2 weaving / break_turn at current severity overwhelm all methods.

### 5. Shift isolation — G2 is not single-factor
- G1: spacing+rotation (geometry only, OK).
- G2: range + bearing together (two variables, not isolated).
- M1/M2: target policy only (OK). C1/C2: topology only (OK). J1: composition.

### 6. Comparator neutrality — C1/C2 NEUTRAL
- Pruned pair is dynamically reachable in ~0.57-0.63 of timesteps under both
  Full and MAPPO, i.e. the same topology change applies to both. MAPPO being
  more robust under C1/C2 is a REAL result, not a design bias.
- Note: at reset the longest pair is initially OUT of range (dist ~13202 vs
  comm range 8500), so the pruning has no effect at t=0 and only activates
  after agents approach; this is a dynamic-topology shift, not an ineffective
  one (reachability ~0.6 during flight confirms real effect).

## Verdict

- **C1/C2 reversal = REAL weakness of EA-RG under communication-topology
  pruning.** Comparator-neutral, discriminative, feasible. Keep as a scientific
  finding (already in Gate C).
- **M1/M2/J1 saturation = severe endpoint saturation / limited
  discriminability** (recovery endpoint unreachable within tau=80 for all
  evaluated methods). These cells do not discriminate algorithms under the
  evaluated policies; they behave as failure-boundary / severe-stress
  conditions. Their RMST80=80 is upper-ceiling saturation, not "Full ~ MAPPO".
  Whether the underlying task is genuinely infeasible will be settled by an
  algorithm-independent oracle feasibility calibration (P3-B, not yet run).
- **G2 is near the saturation boundary** (MAPPO cannot even see the target).
  Its severity is questionable as a moderate deployment shift.

## Implication for a calibrated suite (P3-B, NOT YET AUTHORIZED)

If a new calibrated OOD suite is designed (P3-B v1.0 or later), it should:
- keep C1/C2 as valid topology shifts (they are real and discriminative);
- re-calibrate G2 to keep the target inside the detection envelope for all
  methods (e.g. smaller range factor or separate range / bearing cells);
- re-calibrate M1/M2 to moderate severities where the attack window remains
  achievable for strong baselines, with an ALGORITHM-INDEPENDENT feasibility
  gate (e.g. oracle / heuristic policy attack-window rate >= threshold) frozen
  in the protocol before any formal run;
- freeze the new design BEFORE running; archive P3-A v1.1 as the original
  severe-suite diagnostic result (Gate C stands for v1.1).

## Amendment 1 (2026-08-08): qualified MPC feasibility oracle

A full-state centralized geometric MPC controller (hand-coded, no learning,
no access to Full/MAPPO/HAPPO/Wider checkpoints or results) was implemented
(`scripts/p3b_oracle_feasibility.py`). Nominal qualification PASS:
aw = success = 1.000 in the pure nominal environment.

With this qualified oracle:

| cell | full-state MPC aw | full-state MPC success |
|---|---|---|
| G1 | 1.000 | 1.000 |
| G2 | 1.000 | 1.000 |
| M1 | 1.000 | 1.000 |
| M2 | 1.000 | 1.000 |
| C1 | 1.000 | 1.000 |
| C2 | 1.000 | 1.000 |
| J1 | 1.000 | 1.000 |

> A qualified full-state MPC oracle confirms kinematic feasibility for all
> seven P3-A cells; the observed saturation therefore reflects limited
> learned-policy transfer and/or information-constrained task difficulty
> rather than physical infeasibility.

An information-constrained variant (IC-MPC: each agent may use only its own
legal detection / communication cache / constant-velocity extrapolation, never
the true target state without legal information) also passes nominal
(aw=success=1.000) and yields: G1=1.0, G2=0.575, M1=1.0, M2=1.0, C1=1.0,
C2=1.0, J1=0.875. This shows G2 carries genuine information/kinematic
difficulty, and that learned-policy saturation on M1/M2/J1 is not explained by
information infeasibility either.

## Boundaries

- No retraining, no fine-tuning, no checkpoint reselection, no re-tuning of
  tau / family weights / recovery definition.
- This audit does not modify any locked tag or result.
