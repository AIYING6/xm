# Role-Graph Usage Diagnostics

- checkpoint: `results\paper_config_runs\chain_aux_dev100\runs\ea_rg_mappo\bc_ppo_seed2\actor_critic_update_0100.pt`
- episodes: `2`
- target policy: `straight`
- dropout: `0.3`
- delay: `2`
- failed blue agent: `1`

## Episode Means

| Group | Episodes | Success | Task-Support Attention | Communication Attention | Perception Attention | Global Attention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 2 | 0.0000 | 0.0376 | 0.7500 | 0.0314 | 0.7497 |
| success | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| failure | 2 | 0.0000 | 0.0376 | 0.7500 | 0.0314 | 0.7497 |

## Gate Summary

- mean absolute gate deviation from 0.5: `0.000098`
- max absolute gate deviation from 0.5: `0.001106`

Interpretation hint: near-zero deviations mean the role-pair gates have not learned strong role differentiation.
