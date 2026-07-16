# 3DOF Formal Role-Pair Gate Ablation

Generated: 2026-07-16T15:03:45

This table compares the full multi-relation role graph against `no_role_pair_gate` on matched node-failure evaluation seeds.

| Scenario | N | Success full/no-gate | Success delta [95% CI] | Recovery full/no-gate | Recovery delta [95% CI] | Recovery-step delta [95% CI] | Steps delta [95% CI] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| relay_failure | 30 | 1.000 / 1.000 | +0.000 [+0.000, +0.000] | 1.000 / 1.000 | +0.000 [+0.000, +0.000] | -1.633 [-2.067, -1.233] | -1.633 [-2.067, -1.233] |
| scout_failure | 30 | 0.967 / 0.933 | +0.067 [+0.000, +0.167] | 0.967 / 0.933 | +0.067 [+0.000, +0.167] | -15.800 [-37.000, -1.467] | -15.800 [-37.067, -1.467] |
