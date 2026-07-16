# 3DOF Task-Support Ablation Pilot

Generated: 2026-07-16T21:05:10

This is a one-seed diagnostic comparison. It is useful for deciding whether the task-support relation deserves formal ablation budget, but it is not a paper-level statistical result.

| Scenario | Episodes | Success full/no-task | Success delta | Recovery full/no-task | Recovery delta | Steps full/no-task | Steps delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| relay_failure | 10 | 1.000 / 0.300 | +0.700 | 1.000 / 0.300 | +0.700 | 45.9 / 195.5 | -149.6 |
| scout_failure | 10 | 1.000 / 0.300 | +0.700 | 1.000 / 0.300 | +0.700 | 45.9 / 195.5 | -149.6 |

## Interpretation

- The pilot supports keeping `no_task_support` as the first formal ablation.
- The current seed0 gap is large enough to justify spending formal budget, but it must be repeated with matched seeds and at least 30 evaluation episodes per scenario before being used as a manuscript claim.
