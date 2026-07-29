# Chain Auxiliary Dev100 Training Summary

Last updated: 2026-07-28

## Protocol

Stage-A development comparison completed for:

- EA-RG-MAPPO, `chain_aux_coef=0.0`;
- EA-RG-MAPPO + Chain Auxiliary, `chain_aux_coef=0.05`;
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

This is a development diagnostic only. The online evaluation uses 5 episodes,
so the numbers are too noisy for paper claims.

## Completion Check

All six runs reached update 100.

No non-finite training values were found in the inspected training logs.

## Online Evaluation Summary

| Method | Last Success by Seed | Mean Last Success | Best Success by Seed | Mean Best Success |
| --- | --- | ---: | --- | ---: |
| EA-RG-MAPPO | 0.00 / 0.00 / 1.00 | 0.3333 | 0.20 / 0.00 / 1.00 | 0.4000 |
| EA-RG-MAPPO + Chain Auxiliary | 0.00 / 0.00 / 0.00 | 0.0000 | 0.00 / 0.20 / 0.00 | 0.0667 |

## Auxiliary Head Diagnostics

For `EA-RG-MAPPO + Chain Auxiliary`, the auxiliary labels are learnable:

| Seed | Last `chain_aux_loss` | Last `chain_aux_acc` |
| ---: | ---: | ---: |
| 0 | 0.1962 | 0.9268 |
| 1 | 0.1773 | 0.9403 |
| 2 | 0.1832 | 0.9347 |

Mean last auxiliary accuracy is approximately `0.9339`.

## Interpretation

The auxiliary head is technically working: it learns the graph-observable
kill-chain labels quickly and remains numerically stable.

However, the current configuration does not justify launching a 1M run. At
100 updates, `chain_aux_coef=0.05` appears to suppress or distract policy
learning relative to the original EA-RG-MAPPO. The most likely causes are:

- auxiliary loss is too strong early in training;
- the head is attached directly to the policy graph representation;
- labels are class-imbalanced and easy to predict, so high auxiliary accuracy
does not necessarily improve control;
- 100 updates is short, but the direction is negative enough to require a safer
development adjustment before long training.

## Decision

Do not launch 1M training with `chain_aux_coef=0.05`.

Next development step:

1. Reduce the coefficient to `0.01` or `0.02`.
2. Prefer a delayed warm-up schedule before applying the auxiliary loss.
3. Keep the original EA-RG-MAPPO as the current main method until an auxiliary
   variant shows neutral or positive recovery performance.

## Follow-Up Implementation

Implemented a safer auxiliary candidate after this result:

- added `--chain-aux-warmup-updates`;
- updated `configs/paper/ea_rg_mappo_chain_aux.yaml` to
  `chain_aux_coef=0.02` and `chain_aux_warmup_updates=20`;
- added `chain_aux_effective_coef` to the training log;
- updated the paper command generator so warm-up is passed only to
  RI-GMAPPO/MAPPO-family training scripts.

Verification:

- command-line help exposes `--chain-aux-warmup-updates`;
- config audit passed: 12 configs;
- 1-update warm-up smoke passed with `chain_aux_effective_coef=0.0`;
- Gate 1 information-boundary tests passed: `24 passed`.

Next run should compare:

- original EA-RG-MAPPO;
- EA-RG-MAPPO + Chain Auxiliary, `chain_aux_coef=0.02`,
  `chain_aux_warmup_updates=20`.
