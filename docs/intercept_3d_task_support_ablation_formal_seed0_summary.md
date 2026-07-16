# 3DOF Formal Task-Support Ablation

Generated: 2026-07-16T13:59:07

This table compares the full multi-relation role graph against the `no_task_support` ablation on matched node-failure evaluation seeds. Positive deltas favor the full model, except for steps and recovery steps where negative deltas favor the full model.

| Scenario | N | Success full/no-task | Success delta [95% CI] | Recovery full/no-task | Recovery delta [95% CI] | Recovery steps full/no-task | Recovery-step delta [95% CI] | Steps delta [95% CI] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| relay_failure | 30 | 1.000 / 0.900 | +0.100 [+0.000, +0.200] | 1.000 / 0.900 | +0.100 [+0.000, +0.233] | 5.6 / 26.7 | -21.267 [-49.401, -0.033] | -21.267 [-42.767, +0.000] |
| scout_failure | 30 | 0.967 / 0.867 | +0.133 [+0.033, +0.267] | 0.967 / 0.867 | +0.133 [+0.033, +0.267] | 12.7 / 33.8 | -28.267 [-56.567, -6.967] | -28.267 [-56.567, -6.933] |

## Boundary

Use this as a manuscript-level ablation only when the ablated CSV was produced by the formal protocol with matched seeds and 30 evaluation episodes per scenario.
