# Role-Graph Usage Diagnostics

- checkpoint: `results\paper_config_runs\dev_1m\runs\ea_rg_mappo\bc_ppo_seed2\actor_critic_update_2900.pt`
- episodes: `20`
- target policy: `straight`
- dropout: `0.3`
- delay: `2`
- failed blue agent: `1`

## Episode Means

| Group | Episodes | Success | Task-Support Attention | Communication Attention | Perception Attention | Global Attention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 20 | 0.3500 | 0.0520 | 0.7500 | 0.1112 | 0.7477 |
| success | 7 | 1.0000 | 0.0715 | 0.7500 | 0.1593 | 0.7454 |
| failure | 13 | 0.0000 | 0.0414 | 0.7500 | 0.0854 | 0.7490 |

## Gate Summary

- mean absolute gate deviation from 0.5: `0.000252`
- max absolute gate deviation from 0.5: `0.004309`

Interpretation hint: near-zero deviations mean the role-pair gates have not learned strong role differentiation.
