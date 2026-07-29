# Role-Graph Usage Diagnostics

- checkpoint: `results\paper_config_runs\relation_bottleneck_dev\bc_ppo_seed0_dev100\actor_critic_latest.pt`
- episodes: `10`
- target policy: `straight`
- dropout: `0.3`
- delay: `2`
- failed blue agent: `1`
- multi-relation global residual weight: `0.0`

## Episode Means

| Group | Episodes | Success | Task-Support Attention | Communication Attention | Perception Attention | Global Attention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 10 | 0.0000 | 0.0082 | 0.7500 | 0.0043 | 0.0000 |
| success | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| failure | 10 | 0.0000 | 0.0082 | 0.7500 | 0.0043 | 0.0000 |

## Gate Summary

- mean absolute gate deviation from 0.5: `0.001640`
- max absolute gate deviation from 0.5: `0.015268`

Interpretation hint: near-zero deviations mean the role-pair gates have not learned strong role differentiation.
