# Role-Graph Usage Diagnostics

- checkpoint: `results\paper_config_runs\dev_1m\runs\ea_rg_mappo\bc_ppo_seed1\actor_critic_update_1200.pt`
- episodes: `20`
- target policy: `straight`
- dropout: `0.3`
- delay: `2`
- failed blue agent: `1`

## Episode Means

| Group | Episodes | Success | Task-Support Attention | Communication Attention | Perception Attention | Global Attention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 20 | 0.7500 | 0.0543 | 0.7500 | 0.1285 | 0.7497 |
| success | 15 | 1.0000 | 0.0538 | 0.7500 | 0.1428 | 0.7499 |
| failure | 5 | 0.0000 | 0.0557 | 0.7500 | 0.0856 | 0.7493 |

## Gate Summary

- mean absolute gate deviation from 0.5: `0.000065`
- max absolute gate deviation from 0.5: `0.001462`

Interpretation hint: near-zero deviations mean the role-pair gates have not learned strong role differentiation.
