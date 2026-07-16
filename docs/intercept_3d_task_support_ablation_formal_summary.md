# 3DOF Formal Task-Support Ablation

Generated: 2026-07-16T21:05:11

This table compares the full multi-relation role graph against the `no_task_support` ablation on matched node-failure evaluation seeds. Positive deltas favor the full model, except for steps and recovery steps where negative deltas favor the full model.

| Scenario | N | Success full/no-task | Success delta [95% CI] | Recovery full/no-task | Recovery delta [95% CI] | Recovery steps full/no-task | Recovery-step delta [95% CI] | Steps delta [95% CI] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| relay_failure | 90 | 1.000 / 0.889 | +0.111 [+0.056, +0.178] | 1.000 / 0.889 | +0.111 [+0.056, +0.178] | 5.6 / 29.2 | -23.522 [-37.689, -11.633] | -23.522 [-37.722, -11.622] |
| scout_failure | 90 | 0.967 / 0.878 | +0.089 [+0.033, +0.156] | 0.967 / 0.878 | +0.089 [+0.033, +0.156] | 12.7 / 31.5 | -18.822 [-32.889, -7.022] | -18.822 [-32.889, -7.056] |

## Boundary

Use this as a manuscript-level ablation only when the ablated CSV was produced by the formal protocol with matched seeds and 30 evaluation episodes per scenario.
