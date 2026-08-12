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
