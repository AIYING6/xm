# Role-Graph Usage Diagnostics

- checkpoint: `results\paper_config_runs\relation_bottleneck_dev\bc_ppo_seed0_smoke\actor_critic_latest.pt`
- episodes: `10`
- target policy: `straight`
- dropout: `0.3`
- delay: `2`
- failed blue agent: `1`
- multi-relation global residual weight: `0.0`

## Episode Means

| Group | Episodes | Success | Task-Support Attention | Communication Attention | Perception Attention | Global Attention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 10 | 0.0000 | 0.0174 | 0.7500 | 0.0111 | 0.0000 |
| success | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| failure | 10 | 0.0000 | 0.0174 | 0.7500 | 0.0111 | 0.0000 |

## Gate Summary

- mean absolute gate deviation from 0.5: `0.000113`
- max absolute gate deviation from 0.5: `0.000983`

Interpretation hint: near-zero deviations mean the role-pair gates have not learned strong role differentiation.
