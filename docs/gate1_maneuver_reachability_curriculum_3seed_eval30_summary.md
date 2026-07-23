# Gate 1 Maneuvering-Target Reachability Diagnostic

Last updated: 2026-07-22

## Purpose

This diagnostic checks why the nominal `weaving_mild` target-policy curriculum is still weak after the `weaving_tiny -> weaving_mild` adaptation route. The goal is to determine whether the failure is caused mainly by:

- inability to approach the maneuvering target;
- intermittent tracking collapse;
- inability to convert approach into attack geometry;
- collision or safety termination.

This is a scenario-depth screening step, not paper-facing formal evidence.

## Protocol

Policies were replayed step-by-step using the validation-selected checkpoints from:

`results/gate1_target_policy_curriculum_multi_3seed_dev30x2/`

Evaluation setting:

- method: `multi_relation`
- target policy: `weaving_mild`
- graph encoder hidden dimension: `64`
- episodes per training seed: `30`
- evaluation base seed: `409000`
- strict sensing: off
- relay failure: off
- target-information bottleneck: off

Output artifacts:

- `results/gate1_maneuver_reachability_curriculum_3seed_eval30/summary.csv`
- `results/gate1_maneuver_reachability_curriculum_3seed_eval30/step_trace.csv`
- `results/gate1_maneuver_reachability_curriculum_3seed_eval30/reachability_curves.png`
- `results/gate1_maneuver_reachability_curriculum_3seed_eval30/summary.md`

## Results

| Case | Train seed | Success | Timeout | Collision | Min range | Range reduction | Tracking | Max geometry | Geometry > 0.25 | Attack-window episodes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `seed0` | 0 | 0.533 | 0.467 | 0.000 | 12047.9 | 12652.1 | 0.285 | 0.165 | 0.367 | 0.533 |
| `seed1` | 1 | 0.000 | 1.000 | 0.000 | 12761.0 | 11939.2 | 0.193 | 0.031 | 0.000 | 0.000 |
| `seed2` | 2 | 0.267 | 0.733 | 0.000 | 12998.3 | 11701.6 | 0.234 | 0.223 | 0.467 | 0.267 |

## Interpretation

The seed-1 failure is not a pure approach failure. Seed 1 reduces range by about `11.9 km`, which is close to seed 0 and seed 2, and reaches a similar minimum range band around `12.8 km`.

The decisive failure is attack-geometry conversion:

- seed 1 has `0.000` attack-window episodes;
- seed 1 never reaches geometry score `> 0.25`;
- its maximum attack-geometry score is only `0.031`, far below seed 0 and seed 2;
- all seed-1 episodes terminate by timeout, with no collisions.

This means additional generic PPO updates are unlikely to be the best next step. The project first needs to verify whether the `weaving_mild` scenario is geometrically reachable under the current target motion, attack-window definition, and high-level action interface.

## Decision

Do not promote maneuvering-target experiments to strict sensing, relay failure, or five-seed formal training yet.

The next experiment should be a rule/geometric oracle reachability check on the same `weaving_mild` and `weaving_tiny` episode seeds:

- if the oracle can reliably form attack windows, the environment is feasible and the learning curriculum should be redesigned around approach-to-geometry behavior;
- if the oracle cannot reliably form attack windows, the scenario or attack-window constraints are too hard or ill-posed for the current paper stage.

## Recommended Next Step

Implement `scripts/analyze_3d_geometric_oracle_reachability.py` to run a deterministic non-learning policy that:

- points the attacker toward an offset pursuit/intercept point rather than directly chasing the target center;
- uses scout and relay as simple support agents;
- records the same metrics as the learned-policy reachability script;
- evaluates `weaving_tiny` and `weaving_mild` on matched episode seeds.

Acceptance gate before more learning:

- no collision-dominated behavior;
- nonzero attack-window episode rate under `weaving_mild`;
- clear evidence whether the current scenario is reachable by a simple geometric policy.
