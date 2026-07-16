# 3DOF Break-Turn Node-Failure Pilot

Generated: 2026-07-16T11:00:49

This is a zero-shot scenario-depth pilot. Existing straight-target topology-curriculum checkpoints are evaluated under `target_policy=break_turn` plus relay/scout node failure. It tests whether the current evidence chain has room for a harder maneuvering-target extension; it is not yet a retrained main result.

| Scenario | N | Success single/multi | Success delta [95% CI] | Recovery single/multi | Recovery delta [95% CI] | Steps delta [95% CI] | Timeout delta [95% CI] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| relay_failure | 90 | 0.000 / 0.244 | 0.244 [0.156, 0.333] | 0.000 / 0.244 | 0.244 [0.156, 0.333] | -45.000 [-60.344, -30.255] | -0.278 [-0.367, -0.189] |
| scout_failure | 90 | 0.000 / 0.144 | 0.144 [0.078, 0.222] | 0.000 / 0.144 | 0.144 [0.078, 0.222] | -26.489 [-39.856, -14.878] | -0.156 [-0.233, -0.089] |

## Interpretation

```text
break_turn is substantially harder than the straight-target setting: single-graph times out in every tested episode, while multi-relation preserves nonzero success and shorter episodes.
This is useful scenario-depth evidence, but the absolute success rate is too low for a main-table result without break-turn curriculum fine-tuning.
Recommended next step: train/fine-tune multi-relation and single-graph under a mild break-turn curriculum, then evaluate relay/scout failure again.
```
