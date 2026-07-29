# Role-Graph Usage Diagnostics

- checkpoint: `results\paper_config_runs\dev_1m\runs\ea_rg_mappo\bc_ppo_seed1\actor_critic_update_2200.pt`
- episodes: `5`
- target policy: `straight`
- dropout: `0.3`
- delay: `2`
- failed blue agent: `1`

## Episode Means

| Group | Episodes | Success | Task-Support Attention | Communication Attention | Perception Attention | Global Attention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 5 | 0.4000 | 0.0707 | 0.7500 | 0.1397 | 0.7499 |
| success | 2 | 1.0000 | 0.0933 | 0.7500 | 0.2343 | 0.7500 |
| failure | 3 | 0.0000 | 0.0557 | 0.7500 | 0.0766 | 0.7498 |

## Gate Summary

- mean absolute gate deviation from 0.5: `0.000146`
- max absolute gate deviation from 0.5: `0.002733`

Interpretation hint: near-zero deviations mean the role-pair gates have not learned strong role differentiation.
