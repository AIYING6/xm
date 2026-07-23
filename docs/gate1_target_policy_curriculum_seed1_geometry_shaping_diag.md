# Seed-1 Geometry-Shaping Diagnostic

Date: 2026-07-22

## Purpose

Seed 1 remained at zero success under zero-shot `weaving_tiny`, direct `weaving_mild` fine-tuning, and the `weaving_tiny -> weaving_mild` curriculum. This diagnostic tested whether an opt-in attack-geometry shaping term can unstick seed 1.

## Implementation

Added opt-in environment/training parameter:

```text
attack_geometry_reward_weight
```

Default is `0.0`, so all existing experiments are unchanged unless the parameter is explicitly enabled.

The geometry score rewards continuous proximity to the attacker-side attack envelope:

- distance close to attack range;
- heading aligned with line of sight;
- altitude difference within attack-window tolerance;
- closing geometry.

This is a training auxiliary, not a method contribution.

## Validation

Gate 1 tests now include:

- near attack geometry scores higher than far geometry;
- reward is unchanged unless `attack_geometry_reward_weight` is enabled.

## Protocol

- Method: `multi_relation`
- Seed: `1`
- Stage policies: `weaving_tiny`, `weaving_mild`
- Stage updates: `30, 30`
- `attack_geometry_reward_weight=0.15`
- Hidden dimension: `64`
- Learning rate: `1e-5`
- Final fixed evaluation: 30 episodes on `weaving_mild`

Outputs:

- `results/gate1_target_policy_curriculum_seed1_geom015_dev30x2/`

## Result

The diagnostic did not unstick seed 1.

Final fixed 30-episode evaluation:

| Metric | Value |
|---|---:|
| Success | 0.0% |
| Chain closed | 0.0% |
| Attack window formed | 0.0% |
| Timeout | 100.0% |
| Collision | 0.0% |
| Mean steps | 260.0 |
| Tracking rate | 21.3% |
| Communication connectivity | 34.4% |

Online evaluation during both stages also stayed at `0.0%` success.

## Interpretation

The failure is not fixed by a small continuous attack-geometry reward alone. Seed 1 appears to fail before it reaches a useful attack-window formation regime.

The next diagnostic should focus on trajectories and initial-geometry reachability:

- Does seed 1 ever reduce range enough?
- Is it losing target tracking too early?
- Is the attacker heading/altitude alignment impossible from its learned source behavior?
- Would an easier initial target offset or smaller target drift produce nonzero seed-1 success?

## Decision

Keep `attack_geometry_reward_weight` as an available opt-in training auxiliary, but do not use it as a paper claim. Do not scale this diagnostic to five seeds until seed 1 has a clear nonzero pathway.
