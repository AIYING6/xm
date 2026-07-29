# Role-Graph Usage Diagnostics

- checkpoint: `results\paper_config_runs\no_balanced_bc_dev\bc_ppo_seed0\ea_rg_mappo\actor_critic_update_0040.pt`
- episodes: `20`
- target policy: `straight`
- dropout: `0.3`
- delay: `2`
- failed blue agent: `1`
- multi-relation global residual weight: `1.0`

## Episode Means

| Group | Episodes | Success | Task-Support Attention | Communication Attention | Perception Attention | Global Attention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 20 | 0.4000 | 0.0020 | 0.7500 | 0.0571 | 0.7495 |
| success | 8 | 1.0000 | 0.0011 | 0.7500 | 0.1025 | 0.7491 |
| failure | 12 | 0.0000 | 0.0027 | 0.7500 | 0.0269 | 0.7497 |

## Gate Summary

- mean absolute gate deviation from 0.5: `0.002211`
- max absolute gate deviation from 0.5: `0.020170`

Interpretation hint: near-zero deviations mean the role-pair gates have not learned strong role differentiation.
