# Role-Graph Usage Diagnostics

- checkpoint: `results\paper_config_runs\dev_1m\runs\ea_rg_mappo\bc_ppo_seed0\actor_critic_update_1700.pt`
- episodes: `5`
- target policy: `straight`
- dropout: `0.3`
- delay: `2`
- failed blue agent: `1`

## Episode Means

| Group | Episodes | Success | Task-Support Attention | Communication Attention | Perception Attention | Global Attention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 5 | 0.8000 | 0.0925 | 0.7500 | 0.1974 | 0.7494 |
| success | 4 | 1.0000 | 0.1042 | 0.7500 | 0.2069 | 0.7497 |
| failure | 1 | 0.0000 | 0.0457 | 0.7500 | 0.1593 | 0.7480 |

## Gate Summary

- mean absolute gate deviation from 0.5: `0.000087`
- max absolute gate deviation from 0.5: `0.001331`

Interpretation hint: near-zero deviations mean the role-pair gates have not learned strong role differentiation.
