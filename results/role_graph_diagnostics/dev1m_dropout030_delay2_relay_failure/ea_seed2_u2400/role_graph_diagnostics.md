# Role-Graph Usage Diagnostics

- checkpoint: `results\paper_config_runs\dev_1m\runs\ea_rg_mappo\bc_ppo_seed2\actor_critic_update_2400.pt`
- episodes: `5`
- target policy: `straight`
- dropout: `0.3`
- delay: `2`
- failed blue agent: `1`

## Episode Means

| Group | Episodes | Success | Task-Support Attention | Communication Attention | Perception Attention | Global Attention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 5 | 0.6000 | 0.0789 | 0.7500 | 0.1274 | 0.7498 |
| success | 3 | 1.0000 | 0.0745 | 0.7500 | 0.1529 | 0.7500 |
| failure | 2 | 0.0000 | 0.0854 | 0.7500 | 0.0891 | 0.7494 |

## Gate Summary

- mean absolute gate deviation from 0.5: `0.000229`
- max absolute gate deviation from 0.5: `0.003581`

Interpretation hint: near-zero deviations mean the role-pair gates have not learned strong role differentiation.
