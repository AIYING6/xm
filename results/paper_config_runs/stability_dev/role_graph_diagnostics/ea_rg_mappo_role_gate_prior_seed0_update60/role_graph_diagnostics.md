# Role-Graph Usage Diagnostics

- checkpoint: `results\paper_config_runs\stability_dev\ea_rg_mappo_role_gate_prior_strong_offset_balanced_recovery_bc_safety05\ppo_seed0\actor_critic_update_0060.pt`
- episodes: `10`
- target policy: `straight`
- dropout: `0.3`
- delay: `2`
- failed blue agent: `1`
- multi-relation global residual weight: `1.0`

## Episode Means

| Group | Episodes | Success | Task-Support Attention | Communication Attention | Perception Attention | Global Attention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 10 | 1.0000 | 0.0224 | 0.7500 | 0.0633 | 0.7500 |
| success | 10 | 1.0000 | 0.0224 | 0.7500 | 0.0633 | 0.7500 |
| failure | 0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Gate Summary

- mean absolute gate deviation from 0.5: `0.025573`
- max absolute gate deviation from 0.5: `0.121487`

Interpretation hint: near-zero deviations mean the role-pair gates have not learned strong role differentiation.
