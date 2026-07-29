# Role-Graph Usage Diagnostics

- checkpoint: `results\paper_config_runs\smoke\ea_rg_mappo_gate_prior_smoke\actor_critic_update_0001.pt`
- episodes: `1`
- target policy: `straight`
- dropout: `0.3`
- delay: `2`
- failed blue agent: `1`

## Episode Means

| Group | Episodes | Success | Task-Support Attention | Communication Attention | Perception Attention | Global Attention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 1 | 0.0000 | 0.0369 | 0.7500 | 0.0308 | 0.7481 |
| success | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| failure | 1 | 0.0000 | 0.0369 | 0.7500 | 0.0308 | 0.7481 |

## Gate Summary

- mean absolute gate deviation from 0.5: `0.022371`
- max absolute gate deviation from 0.5: `0.098708`

Interpretation hint: near-zero deviations mean the role-pair gates have not learned strong role differentiation.
