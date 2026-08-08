# P3-B Calibration Draft — Candidate Grids & Frozen Rules (for review, NOT frozen)

- status: **DRAFT — for review only. No calibration run, no protocol freeze.**
- basis: `uav_intercept_3d_env.py` physical parameters (read verbatim);
  legacy P3-A v1.1 cells used only as anchors.
- Rules follow the user-specified design constraints (single-axis G, single
  severity axis M, structural C gate, J = G_mod+M_mod+C_mod, no post-hoc
  re-tuning).

---

## Table 1 — Geometry candidate grid

Initial geometry (nominal): blue centroid ≈ (−14667, 0, 4867);
target (10000, y∈[−2000,2000], 5000); target relative range from centroid
r0 ≈ 24667 m; nominal bearing ≈ 0° (y noise ±4.6°). World-safe xy radius < 38000 m.

### Range-only axis (GR) — only `target_init_range_scale` changes

| id | scale | dist from centroid (m) | world ok (<38000) | initial radar envelope | legacy overlap | primary eligible |
|---|---|---|---|---|---|---|
| GR0 | 1.00 | 24667 | yes | all outside scout radar (as nominal) | = nominal | no (anchor) |
| GR1 | 1.10 | 27133 | yes | outside (as nominal) | no | candidate |
| GR2 | 1.20 | 29600 | yes | outside | no | candidate |
| GR3 | 1.30 | 32067 | yes | outside | no | candidate |
| GR4 | 1.40 | 34534 | yes | outside | **= legacy G2 range term** | **no (legacy)** |
| GR5 | 1.50 | 37000 | yes (margin 1000) | outside | no | candidate (near boundary) |

Note: nominal target is already outside all blue radar at t=0, so range shift
does not change the binary detectability, only the time-to-close.

### Bearing-only axis (GB) — only `target_init_bearing_offset_deg` changes (dist fixed at r0)

| id | offset (deg) | target xy | world ok | initial radar envelope | legacy overlap | primary eligible |
|---|---|---|---|---|---|---|
| GB0 | +0 | (10000, ~0) | yes | outside | = nominal | no (anchor) |
| GB1 | +5 | rotated 5° | yes | outside | no | candidate |
| GB2 | +10 | rotated 10° | yes | outside | no | candidate |
| GB3 | +15 | rotated 15° | yes | outside | no | candidate |
| GB4 | +20 | rotated 20° | yes | outside | no | candidate |
| GB5 | +25 | rotated 25° | yes | outside | **= legacy G2 bearing term** | **no (legacy)** |

Note: the legacy G2 was the COMBINATION GR4+GB5; P3-B keeps them as two
independent single-factor cells and excludes both legacy-exact terms from
primary eligibility.

### Spacing-only / rotation-only axes (GS / GRot) — optional, mirror of legacy G1

| id | param | value | legacy overlap | primary eligible |
|---|---|---|---|---|
| GS1 | blue_init_spacing_scale | 1.10 | no | candidate |
| GS2 | blue_init_spacing_scale | 1.20 | **= legacy G1 spacing term** | **no (legacy)** |
| GRot1 | blue_init_rotation_deg | +10 | no | candidate |
| GRot2 | blue_init_rotation_deg | +20 | **= legacy G1 rotation term** | **no (legacy)** |

---

## Table 2 — Maneuver candidate grid & underlying physical parameters

Target dynamics (verbatim): max_speed 255, max_turn_rate 0.046 rad/s,
max_gamma 0.28 rad, altitude band [1000, 9000].

### Presets expanded (what the names actually mean)

| policy | heading_amp (rad) | alt_amp (m) | heading_freq (rad/step) | alt_freq (rad/step) |
|---|---|---|---|---|
| weaving_tiny | 0.06 | 120 | 0.07 | 0.045 |
| weaving_mild | 0.20 | 350 | 0.07 | 0.045 |
| weaving (legacy M1) | 0.45 | 850 | 0.07 | 0.045 |
| break_turn (legacy M2) | LOS±90° step, side=sin(0.045·step+id), trigger <9000 m | | | |

Note: the three weaving presets change BOTH heading and altitude amplitude
together (two severity axes coupled) → NOT single-axis. They remain usable
as preset reference candidates but are not themselves single-axis grid points.

### Single-axis weaving grid (fixed frequency; only heading amplitude varies)

To be implemented as a parameterized target policy (env extension:
`target_policy="weaving_param"` with `target_heading_amp` config field;
altitude term frozen at the mild 350 m):

| id | heading_amp (rad) | alt_amp (m) | freq (both) | legacy overlap |
|---|---|---|---|---|
| W1 | 0.10 | 350 | 0.07 / 0.045 | no |
| W2 | 0.20 | 350 | 0.07 / 0.045 | = weaving_mild alt but heading 0.20 (≈ mild) |
| W3 | 0.30 | 350 | 0.07 / 0.045 | no |
| W4 | 0.45 | 350 | 0.07 / 0.045 | heading = legacy M1 heading, alt different |
| W5 | 0.60 | 350 | 0.07 / 0.045 | no |

### Single-axis break-turn grid (fixed trigger 9000 m; only step-phase severity varies)

Current break_turn alternates sides at phase 0.045·step; severity is the turn
amplitude (±90°) and the phase speed. Parameterized:
`target_policy="break_turn_param"`, `target_break_turn_amp_rad`:

| id | turn amp (rad) | trigger (m) | phase | legacy overlap |
|---|---|---|---|---|
| BT1 | 0.35π | 9000 | 0.045 | no |
| BT2 | 0.40π | 9000 | 0.045 | no |
| BT3 | 0.45π | 9000 | 0.045 | no |
| BT4 | 0.50π | 9000 | 0.045 | = legacy M2 amplitude |
| BT5 | 0.55π | 9000 | 0.045 | no |

Environment extension required (both W and BT grids): a small, additive
parameterization of `target_policy` with explicit config fields. This is a
**new env capability**, does not alter nominal/legacy behavior, and must be
smoke-tested before any calibration.

---

## Table 3 — C-family structural metrics (implemented; nominal qualification only)

Communication topology difficulty is NOT measured by the IC oracle (a hand-coded
controller does not do communication coordination). Instead, three structural
metrics over a fixed scripted trajectory:

| metric | definition | meaning |
|---|---|---|
| p_affected | fraction of timesteps the to-be-removed edge exists in the unperturbed graph | edge must really exist before removal |
| Δp_path | p_path^base − p_path^shift (fraction of timesteps a task-relevant directed path exists) | shift must actually change topology |
| p_alt | fraction of timesteps an alternate task-relevant directed path exists after perturbation | graceful degradation, not task destruction |

- Implemented as `scripts/p3b_c_structural.py` (to be written).
- Nominal qualification: compute all three on the LEGACY C1/C2 motifs under a
  fixed nominal trajectory (IC-oracle trajectory). Thresholds are NOT frozen
  yet; distributions are reported for review.
- Legacy C1/C2 (longest-pair symmetric / directed pruning) remain anchors;
  new motifs (e.g., transient directed loss, intermittent edge loss) are
  candidates. Primary-eligible C cells require p_affected high AND Δp_path
  non-trivial AND p_alt meaningful — exact numeric thresholds decided from the
  nominal distributions BEFORE any C candidate is selected.

---

## Table 4 — Frozen calibration / selection / RNG rules (proposed; to freeze at PRE-CALIBRATION FREEZE commit)

### Oracle and normalization

- IC-MPC oracle (implemented, nominal-qualified) only.
- q_c = P_success^IC(cell) / P_success^IC(nominal); nominal currently 1.0, but
  the ratio is retained for robustness.

### Severity bands (frozen)

| level | criterion |
|---|---|
| Mild | 0.80 ≤ q ≤ 1.00 |
| Moderate (primary eligible) | 0.50 ≤ q < 0.80 |
| Severe stress | 0.20 ≤ q < 0.50 |
| Failure boundary | q < 0.20 |

### Primary selection rule (frozen)

c* = argmin over Moderate of |q_c − 0.65|; tie → smaller shift magnitude.

### Calibration effort & RNG (frozen)

- 3 calibration seeds × 100 episodes / seed / candidate = 300 episodes/candidate;
  pooled success + per-seed report. SE(p=0.65) ≈ 0.028.
- Calibration seeds ≠ formal P3-B evaluation seeds (formal uses the P3-A
  evaluation schedule; calibration uses a new, disjoint seed set).

### Refinement (frozen, max once)

- Wide grid first (5–7 levels/family). If no candidate lands in Moderate,
  allow exactly ONE deterministic midpoint refinement between the nearest
  Mild and Severe parameter values. If still none: the family produces no
  P3-B primary cell.

### Hard constraints (frozen)

- Legacy P3-A exact cells are anchors; NEVER primary-eligible.
- J = G_mod + M_mod + C_mod ONLY; if J fails the IC/structural gate, it is
  demoted to a secondary severe-stress cell — no component substitution.
- Full / MAPPO / HAPPO / Wider are forbidden from any P3-B cell until the
  protocol is frozen.
- No post-hoc grid expansion, threshold change, or severity re-tuning.

---

## Current state

| step | status |
|---|---|
| 1. full-state MPC (kinematic) | done, nominal-qualified, 7 cells = 1.0 |
| 2. IC-MPC (information-constrained) | done, nominal-qualified |
| 3. audit memo amendment 1 | done |
| 4. candidate grid drafting | THIS DRAFT |
| 5. env parameterized target policy | PENDING (needs user OK) |
| 6. C structural metric + nominal qualification | PENDING |
| 7. PRE-CALIBRATION FREEZE | PENDING (after this draft is accepted) |
| 8. calibration → protocol freeze → formal run | BLOCKED until freeze |
