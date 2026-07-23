# Frozen Protocol: Nominal `weaving_mild` Scenario-Depth Experiment

Last updated: 2026-07-22

## Purpose

This protocol upgrades the current nominal `weaving_mild` development evidence into a formal scenario-depth experiment after Gate 1 package closure.

The purpose is not to create a new main contribution. The purpose is to show that the same multi-relation role-graph mechanism remains useful when the target performs mild maneuvering, even without strict sensing or relay failure.

## Current Development Evidence

Existing validation-selected development result:

| Method | Success | Attack-window formed | Collision | Tracking | Connectivity |
|---|---:|---:|---:|---:|---:|
| `multi_relation` | 0.633 | 0.667 | 0.000 | 0.466 | 0.744 |
| `single` | 0.111 | 0.156 | 0.000 | 0.223 | 0.550 |
| `no_graph` | 0.000 | 0.000 | 0.000 | 0.055 | 0.404 |

Existing limitations:

- only three training seeds;
- validation uses only 10 episodes per checkpoint;
- test uses only 30 episodes per selected checkpoint;
- no seed-aware hierarchical bootstrap has been generated for the three-method nominal `weaving_mild` result;
- it is nominal maneuvering-target evidence only, not strict-sensing relay-failure evidence.

## Claim Boundary

Allowed claim if the formal result passes:

> Under a nominal mild-maneuvering target, the multi-relation role-graph policy retains a stronger attack-window formation and interception capability than no-graph and single-graph baselines under the same oracle-assisted training route.

Not allowed:

- do not claim relay-failure recovery in `weaving_mild`;
- do not claim strict intermittent sensing in `weaving_mild`;
- do not claim online missile or radar validation;
- do not claim 6DOF/JSBSim validation;
- do not claim that oracle demonstrations are a contribution.

## Methods

Required methods:

- `no_graph`;
- `single`;
- `multi_relation`.

Optional method if runtime permits:

- parameter-matched `single` with the previously planned hidden dimension, clearly labeled as capacity-control scenario-depth evidence.

All required methods must use:

- the same source-policy family;
- the same offset geometric-oracle BC route;
- the same number of demonstration episodes;
- the same BC epochs;
- the same attacker action weight;
- the same PPO update budget;
- the same checkpoint-selection rule;
- the same validation and test episode seeds.

## Training Protocol

Recommended formal budget:

- training seeds: `0, 1, 2, 3, 4`;
- target policy: `weaving_mild`;
- strict target sensing: disabled;
- node failure: disabled;
- target-information bottleneck: disabled;
- oracle BC mode: `offset`;
- BC demonstration episodes: `30`;
- BC epochs: `12`;
- attacker action weight: `4.0`;
- PPO updates: `30`;
- learning rate: `1e-5`;
- save interval: `5`;
- evaluation batch size: use batching only if metric equivalence is already validated.

Fallback budget if runtime is tight:

- keep training seeds `0, 1, 2`;
- increase validation/test episode budgets;
- label the result as development scenario-depth evidence, not formal Q1-scale evidence.

## Checkpoint Selection

Validation split:

- base seed: `509000`;
- episodes per checkpoint: `30` minimum, preferably `50`;
- selection candidates: `actor_critic_update_*.pt`;
- max validation collision rate: `0.0`.

Selection score:

```text
1000 * success + 100 * attack_window_formed + 10 * tracking
```

Rationale:

- success remains primary;
- attack-window formation captures near-success maneuvering behavior;
- tracking breaks ties;
- collision-free validation is mandatory.

## Final Test

Final test split:

- base seed: choose a new seed not used by current development test if a new formal run is launched;
- recommended new formal base seed: `609000`;
- episodes per selected checkpoint: `100`;
- do not inspect or tune on this split before freezing the protocol and selected checkpoints.

The existing `409000` split can remain as development evidence, but it should not be used again for formal tuning decisions.

## Metrics

Main metrics:

- success rate;
- attack-window formation rate;
- collision rate;
- timeout rate;
- episode length;
- target tracking rate;
- communication connectivity rate.

Safety/diagnostic metrics:

- minimum blue-red distance;
- minimum blue-blue distance;
- constraint violation rate.

Statistical reporting:

- per-seed scatter;
- mean across training seeds;
- seed-aware hierarchical bootstrap;
- full-minus-baseline paired deltas.

## Acceptance Gate

Promote the result to paper-facing scenario-depth evidence only if:

- `multi_relation` success is at least roughly 60%;
- `multi_relation` collision is near zero;
- `multi_relation` exceeds both `single` and `no_graph` on success and attack-window formation;
- seed-aware intervals are favorable, even if not every secondary metric separates;
- all methods use the same oracle-assisted protocol.

If these conditions fail:

- do not hide the result;
- keep it as development evidence;
- submit the Gate 1 paper as the main Q2/Q1-borderline package or redesign Stage 2.

## Recommended Execution Order

1. Write a small orchestration script for the formal nominal `weaving_mild` protocol if existing scripts cannot express all settings cleanly.
2. Run a smoke protocol with one seed, one checkpoint, and two validation/test episodes.
3. Run three required methods on seeds `0, 1, 2`.
4. Inspect validation-selected checkpoints and test metrics.
5. If the signal remains similar to the current development result, expand to seeds `3, 4`.
6. Generate seed-aware statistics and paper-facing tables.
7. Integrate as a scenario-depth section after the Gate 1 main result, not before it.
