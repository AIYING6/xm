# Chain Auxiliary Dev100 Warm-Up Training Summary

Last updated: 2026-07-28

## Protocol

Second Stage-A development comparison completed for:

- EA-RG-MAPPO + Chain Auxiliary;
- `chain_aux_coef=0.02`;
- `chain_aux_warmup_updates=20`;
- seeds: 0, 1, 2;
- updates: 100;
- num envs: 8;
- rollout steps: 128;
- eval interval: 20;
- eval episodes per online evaluation: 5;
- strict target sensing: enabled;
- actor target information bottleneck: enabled;
- communication dropout: 0.30;
- message delay: 2;
- relay failure: blue agent 1;
- failure start sampled from [25, 70];
- failure duration: 80.

The original EA-RG-MAPPO 100-update run from
`docs/chain_aux_dev100_training_summary.md` is used as the development reference.

## Completion Check

All three warm-up auxiliary runs reached update 100.

No non-finite training values were found in the inspected logs.

The warm-up behaved as intended:

- `chain_aux_effective_coef=0.0` through update 20;
- `chain_aux_effective_coef=0.02` from update 40 onward.

## Online Evaluation Summary

| Method | Last Success by Seed | Mean Last Success | Best Success by Seed | Mean Best Success |
| --- | --- | ---: | --- | ---: |
| EA-RG-MAPPO | 0.00 / 0.00 / 1.00 | 0.3333 | 0.20 / 0.00 / 1.00 | 0.4000 |
| EA-RG-MAPPO + Aux, coef 0.05 | 0.00 / 0.00 / 0.00 | 0.0000 | 0.00 / 0.20 / 0.00 | 0.0667 |
| EA-RG-MAPPO + Aux, coef 0.02, warm-up 20 | 0.00 / 0.00 / 0.00 | 0.0000 | 0.20 / 0.00 / 0.20 | 0.1333 |

## Auxiliary Diagnostics

| Seed | Last `chain_aux_loss` | Last `chain_aux_acc` | Last Effective Coef |
| ---: | ---: | ---: | ---: |
| 0 | 0.2360 | 0.9000 | 0.0200 |
| 1 | 0.2472 | 0.8854 | 0.0200 |
| 2 | 0.1805 | 0.9327 | 0.0200 |

Mean final auxiliary accuracy is approximately `0.9060`.

## Interpretation

The warm-up and lower coefficient reduce the auxiliary objective's strength, but
they still do not recover the original EA-RG-MAPPO short-horizon policy
performance. The auxiliary head remains learnable, but current auxiliary
supervision does not yet translate into better control.

This suggests the issue is not only coefficient size. More likely:

- the auxiliary targets are too easy or too static;
- predicting current graph state does not directly teach recovery actions;
- attaching the head to the policy graph representation still competes with PPO;
- a better next step is to improve relation/gate learning directly rather than
  continuing to tune this auxiliary loss.

## Decision

Do not launch a 1M run with the current chain auxiliary implementation.

Keep original EA-RG-MAPPO as the current main method.

Next method-improvement route:

1. Inspect role-pair gate parameters and task-support attention behavior.
2. Add diagnostics for relation-level attention mass and role-pair gate usage.
3. Consider a lower-risk regularization or initialization change for role-pair
   gates before any full 1M/2M run.

