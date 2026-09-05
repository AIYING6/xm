# B-line P0R native-freshness counterexample contract

## Question

Can two legal histories in an unmodified UAV environment reach the same current physical state while native information freshness alone changes the feasible service/action set?

## Frozen construction

The P0R harness uses the existing six-UAV `main` scale and its default `tau_max=5`. Both histories have seven steps, no failures, no terminal motion, identical geometry, physical topology, mission progress, roles, and frozen assignments. The only history difference is whether scouts legally sense objective 0 at step 1 or step 7.

The current physical snapshot excludes cache freshness. Cache freshness and the action mask are expected to differ because the existing environment invalidates a token after its native `tau_max` age limit.

## Prohibitions

No environment change, threshold override, reward/termination/failure-semantic change, new action, solver, checkpoint, training, PPO update, parameter tuning, evaluation tape, or formal benchmark is permitted.

## Decision

- `B_P0R_GO`: the physical state is identical, cache freshness is the only permitted difference, and native action/service feasibility differs.
- `B_P0R_CONDITIONAL`: the paired physical state is valid and freshness differs, but feasibility does not.
- `B_P0R_NO_GO`: the pair cannot be constructed under existing semantics or has an impermissible difference.

Even `B_P0R_GO` does not authorize P1 automatically.
