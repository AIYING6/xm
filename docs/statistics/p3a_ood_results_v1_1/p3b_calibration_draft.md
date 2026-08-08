# P3-B Calibration Draft v2 — Candidate Grids & Frozen Rules (for review, NOT frozen)

- status: **DRAFT v2 — for review. No calibration run, no protocol freeze.**
- v1 was reviewed with GO-with-revisions; v2 incorporates every revision.
- basis: `uav_intercept_3d_env.py` physical parameters (read verbatim);
  legacy P3-A v1.1 cells used only as anchors.

---

## P3-B primary topology (frozen NOW)

Exactly **2G + 2M + 2C + 1J = 7 primary cells**:

```
G-R   target range-only
G-B   target bearing-only

M-W   weaving single-axis
M-BT  break-turn single-axis

C-S   symmetric topology perturbation
C-D   directed topology perturbation

J     predetermined G + M + C composition (rule frozen below)
```

- GS (spacing-only) / GRot (rotation-only): remain candidate grid entries but
  are SECONDARY / supplementary stress cells; they never enter the primary
  seven-cell aggregate (keeps Geometry family weight equal to others).

---

## Table 1 — Geometry candidate grid

### Coordinate convention (corrected)

- Range scale applies to the target vector RELATIVE TO THE BLUE CENTROID
  (≈(−14667, 0)), not to the target's world-frame radius.
- Table reports BOTH `relative-to-blue-centroid range` and
  `absolute world-frame target radius`; they must never be conflated.
- Nominal: rel range ≈ 24667 m; world target ≈ (10000, y∈[−2000,2000]);
  world radius ≈ 10000 m.
- World-safe xy radius < 38000 m (world_radius 50000 − boundary margin 12000).

### Range-only axis (GR) — only `target_init_range_scale` changes

| id | scale | rel-to-centroid range (m) | world x ≈ −14667+rel | world radius (m) | safe (<38000) | initial radar | legacy | primary eligible |
|---|---|---|---|---|---|---|---|---|
| GR0 | 1.00 | 24667 | 10000 | ≈10000 | yes | outside (as nominal) | = nominal anchor | no |
| GR1 | 1.10 | 27133 | 12467 | ≈12467 | yes | outside | no | candidate |
| GR2 | 1.20 | 29600 | 14933 | ≈14933 | yes | outside | no | candidate |
| GR3 | 1.30 | 32067 | 17400 | ≈17400 | yes | outside | no | candidate |
| GR4 | 1.40 | 34534 | 19867 | ≈19867 | yes | outside | legacy-derived value (G2 range term) | conservative: avoid as primary |
| GR5 | 1.50 | 37000 | 22333 | ≈22333 | yes | outside | no | candidate (kept; margin is large, ≈15.7 km to 38 km) |

- **Correction from v1**: GR5 ×1.50 does NOT approach the 38 km world
  boundary. Relative range is from the blue centroid; the world-frame target
  x ≈ 22333 m, leaving ≈15.7 km margin. GR5 is retained.

### Bearing-only axis (GB) — only `target_init_bearing_offset_deg` changes (dist fixed at r0)

| id | offset (deg) | world target | world radius (m) | safe | legacy | primary eligible |
|---|---|---|---|---|---|---|
| GB0 | +0 | (10000, ~0) | ≈10000 | yes | = nominal anchor | no |
| GB1 | +5 | rotated 5° about centroid | ≈10000–12000 | yes | no | candidate |
| GB2 | +10 | rotated 10° | same | yes | no | candidate |
| GB3 | +15 | rotated 15° | same | yes | no | candidate |
| GB4 | +20 | rotated 20° | same | yes | no | candidate |
| GB5 | +25 | rotated 25° | same | yes | legacy-derived value (G2 bearing term) | conservative: avoid as primary |

### Legacy-exact vs legacy-derived distinction

- The legacy G2 was the COMBINATION (range×1.40 + bearing+25°). We have NOT
  observed learned-policy results for range-only ×1.40 or bearing-only +25°.
- Therefore GR4/GB5 are "legacy-derived parameter values", not legacy exact
  cells; excluding them from primary is a conservative cleanliness choice,
  not a statistical requirement.
- Conservative rule: primary grid avoids legacy-exact AND legacy-derived
  magnitudes where possible (GR4/GB5 flagged; kept only as reference).

### Spacing / rotation (GS / GRot) — secondary only

| id | param | value | legacy | role |
|---|---|---|---|---|
| GS1 | blue_init_spacing_scale | 1.10 | no | secondary |
| GS2 | blue_init_spacing_scale | 1.20 | legacy-derived (G1) | secondary/reference |
| GRot1 | blue_init_rotation_deg | +10 | no | secondary |
| GRot2 | blue_init_rotation_deg | +20 | legacy-derived (G1) | secondary/reference |

These never enter the primary aggregate.

---

## Table 2 — Maneuver candidate grid (single-axis)

### Weaving — only heading amplitude A_h varies

Fixed: altitude amplitude (350 m), heading frequency (0.07), altitude
frequency (0.045), target speed / dynamics unchanged.

| id | A_h (rad) | alt_amp (m) | freq | legacy |
|---|---|---|---|---|
| W1 | 0.10 | 350 | 0.07 / 0.045 | no |
| W2 | 0.20 | 350 | same | ≈ weaving_mild alt, heading differs |
| W3 | 0.30 | 350 | same | no |
| W4 | 0.45 | 350 | same | heading = legacy M1 heading, alt different |
| W5 | 0.60 | 350 | same | no |

### Break-turn — only desired break-heading offset θ varies

Fixed: trigger range (9000 m), phase (0.045), speed, dynamics.
Parameterization: `target_break_turn_amp_rad` = DESIRED HEADING OFFSET
relative to LOS (NOT turn radius; actual achieved turn is still limited by the
env's max_turn_rate / dynamics).

| id | desired break-heading offset | trigger | phase | legacy |
|---|---|---|---|---|
| BT1 | 0.35π | 9000 | 0.045 | no |
| BT2 | 0.40π | 9000 | 0.045 | no |
| BT3 | 0.45π | 9000 | 0.045 | no |
| BT4 | 0.50π (=90°) | 9000 | 0.045 | = legacy M2 offset |
| BT5 | 0.55π (≈99°) | 9000 | 0.045 | no (severe) |

Terminology note: these are desired heading offsets, not turn radii.

### Env parameterized extension (approved)

- New: `target_policy="weaving_param"` with `target_heading_amp`;
  `target_policy="break_turn_param"` with `target_break_turn_amp_rad`.
- Legacy code paths (`weaving`, `weaving_mild`, `weaving_tiny`,
  `break_turn`) remain EXACTLY UNCHANGED (separate `if/elif` branches, no
  refactor through a shared generic function).
- Backward compatibility: legacy trajectories byte-for-byte identical.

---

## Table 3 — Communication structural metrics (tightened)

### Metric definitions (same-state offline counterfactual)

1. **p_affected** — fraction of timesteps the to-be-removed edge actually
   exists in the unperturbed communication graph (edge must really exist
   before removal).
2. **Δp_path = p_path^base − p_path^shift** — change in the fraction of
   timesteps with a task-relevant directed path.
3. **p_alt** — fraction of timesteps an alternate task-relevant directed path
   exists after perturbation (graceful degradation, not task destruction).

### Counterfactual discipline (strict)

- Use ONE algorithm-independent qualification trajectory (e.g., the IC-MPC
  nominal trajectory). Save each step's blue positions + direct sensing state.
- Build G_base(t) offline from the SAVED states.
- Apply the candidate perturbation to the SAME states → G_shift(t).
- G_base(t) and G_shift(t) therefore share IDENTICAL physical states; any
  difference is purely topological.

### Task path definition (environment-defined, architecture-independent)

- Source set: blue nodes with legal direct target information per
  environment rules (detected_by or fresh cache), i.e. environment truth,
  NOT learned Task-Support / EA-RG graph / any learned policy.
- Task path: ∃ directed physical communication path from a source to an
  attacker/interceptor, using env comm_adj (range/dropout/delay/failure rules).
- No reading of EA-RG graph, Task-Support, MAPPO, or any learned output.

### Thresholds

- NOT frozen yet. First run nominal structural qualification (see below) and
  report per-edge activity, path redundancy, source→attacker path nominal
  availability. Freeze C eligibility thresholds from these distributions
  BEFORE any new C candidate metric is opened.

---

## Table 4 — Frozen calibration / selection / RNG rules

### Oracle & normalization

- IC-MPC oracle only (implemented, nominal-qualified). Do NOT tighten it
  further to create discrimination; nominal 1.0 is a valid qualification
  result. Verify only: uses env-legal API, agent-specific detection/cache,
  freshness rules, last-known+prediction after loss, and NO true-state
  fallback. If all hold, 1.0 is accepted.
- q_c = P_success^IC(cell) / P_success^IC(nominal).

### Severity bands (frozen)

| level | criterion |
|---|---|
| Mild | 0.80 ≤ q ≤ 1.00 |
| Moderate (primary eligible) | 0.50 ≤ q < 0.80 |
| Severe stress | 0.20 ≤ q < 0.50 |
| Failure boundary | q < 0.20 |

### Primary selection rule (frozen)

c* = argmin over Moderate of |q_c − 0.65|; tie → smaller shift magnitude.

### Calibration effort (frozen)

- 3 calibration seeds × 100 episodes / seed / candidate = 300 episodes/candidate.
- Classification and selection are made from the FIXED 300-episode estimate;
  NO extra episodes are added because a candidate lies near a threshold.
- Calibration seeds are disjoint from formal P3-B evaluation seeds.

### RNG derivation (deterministic, frozen)

```
calibration_base_seed = first 8 hex of SHA256("P3B-CALIBRATION-v1.0")
formal_base_seed      = first 8 hex of SHA256("P3B-FORMAL-v1.0")
```
Three seeds derived deterministically from each base seed (e.g., base, base+1,
base+2). Exact integer values are committed at the PRE-CALIBRATION FREEZE.

### Refinement (frozen, max once)

- Wide grid first (5–7 levels/family). If no candidate lands in Moderate,
  allow exactly ONE deterministic midpoint refinement between the nearest
  Mild and Severe parameter values. If still none: the family produces no
  P3-B primary cell.

### J composition (frozen NOW, before any calibration)

```
J = selected G-R moderate + selected M-W moderate + selected C-S moderate
```
- If ANY of the three families yields no Moderate candidate, J primary is NOT
  formed; J is omitted (or demoted to secondary severe-stress) WITHOUT
  substituting G-B / M-BT / C-D. No result-driven substitution.

### Hard constraints (frozen)

- Legacy P3-A exact cells and legacy-derived parameter magnitudes are
  conservative-excluded from primary where feasible (GR4/GB5 flagged).
- Full / MAPPO / HAPPO / Wider are forbidden from any P3-B cell until the
  protocol is frozen.
- No post-hoc grid expansion, threshold change, severity re-tuning, or
  oracle tightening.

---

## Gate to PRE-CALIBRATION FREEZE

Two prerequisites must PASS before `p3b-ood-precalibration-freeze-v1.0`:

1. **Legacy env regression tests** — same seed / initial state / action
   sequence: legacy env BEFORE vs AFTER the parameterized-policy extension
   must be identical (positions, headings, altitude, policy phase,
   observations, transitions), ideally bit-exact. This is a software
   regression test, NOT a calibration run.
2. **Nominal C structural qualification** — run p_affected / Δp_path / p_alt
   on legacy C1/C2 motifs under a fixed nominal IC-oracle trajectory; report
   distributions; do NOT freeze thresholds yet.

After both PASS → tag `p3b-ood-precalibration-freeze-v1.0`. From that commit:
IC-MPC may open new G/M candidates and the structural evaluator may open new C
candidates; Full/MAPPO/HAPPO/Wider remain forbidden until protocol freeze.

---

## Current state

| step | status |
|---|---|
| full-state MPC | done, nominal-qualified |
| IC-MPC | done, nominal-qualified (do not tighten further) |
| audit memo amendment 1 | done |
| candidate grid drafting | DRAFT v2 (this file) |
| env parameterized target policy | PENDING (approved; needs regression) |
| legacy env regression tests | PENDING |
| nominal C structural qualification | PENDING |
| PRE-CALIBRATION FREEZE | PENDING (after 2 prerequisites PASS) |
| calibration → protocol freeze → formal run | BLOCKED until freeze |
