# 3DOF Formal Role-Pair Gate Ablation

Generated: 2026-07-16T21:05:11

This table compares the full multi-relation role graph against `no_role_pair_gate` on matched node-failure evaluation seeds.

| Scenario | N | Success full/no-gate | Success delta [95% CI] | Recovery full/no-gate | Recovery delta [95% CI] | Recovery-step delta [95% CI] | Steps delta [95% CI] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| relay_failure | 90 | 1.000 / 0.956 | +0.044 [+0.011, +0.089] | 1.000 / 0.956 | +0.044 [+0.011, +0.089] | -9.800 [-19.200, -2.656] | -9.800 [-19.189, -2.655] |
| scout_failure | 90 | 0.967 / 0.933 | +0.033 [-0.011, +0.089] | 0.967 / 0.933 | +0.033 [-0.011, +0.078] | -7.478 [-18.967, +2.000] | -7.478 [-19.144, +2.000] |
