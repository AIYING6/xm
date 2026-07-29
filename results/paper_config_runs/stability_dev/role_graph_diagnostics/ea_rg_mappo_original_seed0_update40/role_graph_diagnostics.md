# Role-Graph Usage Diagnostics

- checkpoint: `results\paper_config_runs\stability_dev\ea_rg_mappo_seed0_strong_offset_balanced_recovery_bc_safety05_ppo_h64\actor_critic_update_0040.pt`
- episodes: `20`
- target policy: `straight`
- dropout: `0.3`
- delay: `2`
- failed blue agent: `1`
- multi-relation global residual weight: `1.0`

## Episode Means

| Group | Episodes | Success | Task-Support Attention | Communication Attention | Perception Attention | Global Attention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 20 | 0.6000 | 0.0111 | 0.7500 | 0.0382 | 0.7499 |
| success | 12 | 1.0000 | 0.0116 | 0.7500 | 0.0370 | 0.7499 |
| failure | 8 | 0.0000 | 0.0103 | 0.7500 | 0.0401 | 0.7499 |

## Gate Summary

- mean absolute gate deviation from 0.5: `0.005914`
- max absolute gate deviation from 0.5: `0.060720`

Interpretation hint: near-zero deviations mean the role-pair gates have not learned strong role differentiation.
