# Role-Graph Usage Diagnostics

- checkpoint: `results\paper_config_runs\dev_1m\runs\ea_rg_mappo\bc_ppo_seed0\actor_critic_update_0100.pt`
- episodes: `20`
- target policy: `straight`
- dropout: `0.3`
- delay: `2`
- failed blue agent: `1`

## Episode Means

| Group | Episodes | Success | Task-Support Attention | Communication Attention | Perception Attention | Global Attention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 20 | 0.3500 | 0.0376 | 0.7500 | 0.0679 | 0.7500 |
| success | 7 | 1.0000 | 0.0536 | 0.7500 | 0.1330 | 0.7500 |
| failure | 13 | 0.0000 | 0.0290 | 0.7500 | 0.0328 | 0.7500 |

## Gate Summary

- mean absolute gate deviation from 0.5: `0.000004`
- max absolute gate deviation from 0.5: `0.000063`

Interpretation hint: near-zero deviations mean the role-pair gates have not learned strong role differentiation.
