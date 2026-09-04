# Current Project State

## Deliverable

This repository is the focused EA-RG-MAPPO-S 3DOF heterogeneous UAV interception project.

- Environment: lightweight 3DOF, 3v1 scout-relay-attacker interception.
- Main result: early post-relay-failure recovery under the locked nominal held-out protocol.
- Manuscript: `paper_latex_3d_en/`.
- Selected evidence: `results/`.

## Scope boundary

The project does not claim complete 6DOF combat, JSBSim/LAG validation, radar/missile closure, universal baseline superiority, or unrestricted OOD generalization.

## Validation

The active checks are:

```text
scripts/smoke_test_env.py
scripts/smoke_test_intercept_3d_env.py
tests/test_gate1_communication_feasibility.py
tests/test_happo_policy_loss.py
```

Failed alternative algorithm lines, old manuscript routes, raw development runs, and migration experiments have been removed from the deliverable repository.

## Research-line update — 2026-09-04

- The A-line Original DRTP manuscript/evidence remains frozen; the new work does not rewrite its claims or results.
- EGTR's fresh 10M double-cohort programme ended `EGTR_DOUBLE_COHORT_REPLICATION_NO_GO`: it improved Original DRTP broadly but did not establish repeatable superiority/reliability versus UTR in both cohorts.
- PVF is an engineering fallback only, not the primary algorithm line.
- The current single-model research candidate is **TGTR-PPO** (Topology-Group Trust-Region PPO): fixed synchronized topology exposure, ordinary-PPO anchor, minimal active-group actor correction, held-stream training certificate, and per-group full-policy KL.
- P0 status: `TGTR_P0_FEASIBLE_FOR_C1`.
- The separately authorized C1 implementation and five-state exact same-rollout audit completed with `TGTR_C1_NO_GO`. Ordinary PPO exposed group harm in 4/5 source states, but the frozen design/certificate rule rejected every TGTR actor epoch (20/20 zero steps), and overall surrogate retention passed in only 1/5 states.
- TGTR fresh-seed development and cloud repetition are not authorized. The frozen candidate is closed; see `docs/tgtr_ppo_c1_20260904/TGTR_C1_FINAL_RESULT.md`.
- Post-TGTR design work now targets **RACG-PPO** (Reliability-Adaptive Cross-fitted Group-Gradient PPO): fixed synchronized exposure, cross-fitted training-only group-gradient agreement, a soft average-oriented conflict correction, and an exact ordinary-PPO fallback. P0 mechanically verified the non-freezing bound and interface design as `RACG_P0_FEASIBLE_FOR_C1_DESIGN_ONLY`; it authorizes no implementation, rollout, update, cloud run, or fresh-seed training. See `docs/racg_ppo_p0_20260904/`.
