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
- Zero-training status: `TGTR_P0_FEASIBLE_FOR_C1`. No TGTR implementation, rollout, PPO update, evaluation, or fresh-seed training has been authorized by P0.
- The only proposed next action is a separately authorized TGTR C1 implementation and exact same-rollout mechanism/cost audit. See `docs/tgtr_ppo_p0_20260904/`.
