# Gate Prior Mechanism Report (v1.5)

- generated: 2026-08-07 12:31:47
- protocol: GATE_PRIOR_MECHANISM_PROTOCOL_V1_5 (+ Addendum A), freeze tag gate-prior-mechanism-protocol-freeze-v1.5.0
- problems: none

## Block 1 — optimization stability (final window {700,800,900}, n=3, ddof=1)

| method | final-window mean ± SD | AUC | first ≥0.9 (per seed) | first K=3 ≥0.9 (per seed) |
|---|---|---|---|---|
| full | 0.6889 ± 0.3791 | 0.5448 | [200, 200, 600] | [None, 900, None] |
| w_o_gate_prior | 0.5778 ± 0.3421 | 0.3964 | [600, 500, None] | [None, None, None] |

## Block 2 — gate evolution (150 aggregated gates; update=0 analytic)

| method | update | mean | SD | min | max | mean|drift| | sat<0.1/>0.9 | r0/r1/r2 mean | cross-seed pearson | cross-seed L2 |
|---|---|---|---|---|---|---|---|---|---|---|
| full | 100 | 0.5241 | 0.0407 | 0.448 | 0.628 | 0.0203 | 0.000 | 0.521/0.525/0.527 | 0.962 | 0.14 |
| full | 200 | 0.5241 | 0.0407 | 0.448 | 0.628 | 0.0203 | 0.000 | 0.521/0.525/0.527 | 0.962 | 0.14 |
| full | 300 | 0.5241 | 0.0407 | 0.447 | 0.628 | 0.0203 | 0.000 | 0.521/0.525/0.527 | 0.962 | 0.14 |
| full | 400 | 0.5241 | 0.0407 | 0.447 | 0.628 | 0.0203 | 0.000 | 0.521/0.525/0.527 | 0.962 | 0.14 |
| full | 500 | 0.5241 | 0.0407 | 0.447 | 0.628 | 0.0203 | 0.000 | 0.521/0.525/0.527 | 0.962 | 0.14 |
| full | 600 | 0.5241 | 0.0407 | 0.447 | 0.628 | 0.0203 | 0.000 | 0.521/0.525/0.526 | 0.962 | 0.14 |
| full | 700 | 0.5241 | 0.0407 | 0.447 | 0.628 | 0.0203 | 0.000 | 0.521/0.525/0.526 | 0.962 | 0.14 |
| full | 800 | 0.5241 | 0.0406 | 0.447 | 0.628 | 0.0203 | 0.000 | 0.521/0.525/0.526 | 0.962 | 0.14 |
| full | 900 | 0.5241 | 0.0407 | 0.447 | 0.627 | 0.0203 | 0.000 | 0.521/0.525/0.526 | 0.962 | 0.14 |
| full | 977 | 0.5241 | 0.0407 | 0.447 | 0.627 | 0.0203 | 0.000 | 0.521/0.525/0.526 | 0.962 | 0.14 |
| w_o_gate_prior | 100 | 0.5015 | 0.0164 | 0.419 | 0.555 | 0.0273 | 0.000 | 0.503/0.503/0.501 | 0.562 | 0.19 |
| w_o_gate_prior | 200 | 0.5015 | 0.0164 | 0.419 | 0.555 | 0.0273 | 0.000 | 0.503/0.503/0.501 | 0.561 | 0.19 |
| w_o_gate_prior | 300 | 0.5015 | 0.0164 | 0.419 | 0.555 | 0.0273 | 0.000 | 0.503/0.503/0.501 | 0.561 | 0.19 |
| w_o_gate_prior | 400 | 0.5015 | 0.0164 | 0.419 | 0.555 | 0.0273 | 0.000 | 0.503/0.503/0.501 | 0.561 | 0.19 |
| w_o_gate_prior | 500 | 0.5015 | 0.0164 | 0.419 | 0.555 | 0.0273 | 0.000 | 0.503/0.503/0.501 | 0.561 | 0.19 |
| w_o_gate_prior | 600 | 0.5015 | 0.0164 | 0.419 | 0.555 | 0.0273 | 0.000 | 0.503/0.503/0.501 | 0.561 | 0.19 |
| w_o_gate_prior | 700 | 0.5015 | 0.0164 | 0.419 | 0.555 | 0.0273 | 0.000 | 0.503/0.503/0.501 | 0.562 | 0.19 |
| w_o_gate_prior | 800 | 0.5015 | 0.0164 | 0.419 | 0.555 | 0.0273 | 0.000 | 0.503/0.503/0.501 | 0.563 | 0.19 |
| w_o_gate_prior | 900 | 0.5015 | 0.0164 | 0.419 | 0.555 | 0.0273 | 0.000 | 0.503/0.503/0.501 | 0.562 | 0.19 |
| w_o_gate_prior | 977 | 0.5015 | 0.0164 | 0.419 | 0.555 | 0.0273 | 0.000 | 0.503/0.503/0.501 | 0.563 | 0.19 |

## Association (descriptive only, n=3, no significance claims)

- full seed0: gate drift 150 = 0.0203, held-out recovery (pooled) = 0.9604
- full seed1: gate drift 150 = 0.0197, held-out recovery (pooled) = 0.9950
- full seed2: gate drift 150 = 0.0195, held-out recovery (pooled) = 0.9563
- w_o_gate_prior seed0: gate drift 150 = 0.0273, held-out recovery (pooled) = 0.8165
- w_o_gate_prior seed1: gate drift 150 = 0.0284, held-out recovery (pooled) = 0.9902
- w_o_gate_prior seed2: gate drift 150 = 0.0297, held-out recovery (pooled) = 0.5081

## Pre-registered verdict: SUPPORT (with qualification)

Evidence per protocol Section 7:

1. Full gate trajectory more consistent across seeds: pairwise Pearson 0.962 (all nodes)
   vs w/o Gate Prior 0.562. **OK**
2. Gate saturation: 0.000 for BOTH methods (gates stay mid-range 0.45-0.63; never strongly
   open/close). **NEUTRAL** — the prior acts as an initial-offset / regularization, not an
   extreme on-off gating mechanism.
3. Worst-seed training stability: Full reaches >=0.9 on the eval grid at seed-updates
   {200, 200, 600} (all 3 seeds eventually), w/o Gate Prior {600, 500, None} (seed2 never);
   final window 0.689±0.379 vs 0.578±0.342; AUC 0.545 vs 0.396. **OK**
4. Direction consistent with the locked held-out ablation: Full recovery 0.971 vs
   w/o Gate Prior 0.772 (3-seed, locked audit). **OK**

=> Claimable: **"Gate Prior improves optimization stability and cross-seed robustness."**

Mechanism reading (descriptive, no significance claims):
- role_pair_gate logits barely move after update 100 (max |d logit| < 0.02 on locked
  checkpoints, verified update_0100 vs update_0977); the learned gate is essentially a
  static per-pair bias whose initialization survives training.
- The prior starts all seeds from a shared structured point (34/150 channels at 0.5987),
  keeping the three seeds on highly correlated gate configurations (0.962) and away from
  divergent random drift (0.562).
- Per-seed gate drift vs held-out recovery (n=3, qualitative): Full drift ~0.020 ->
  recovery 0.960/0.995/0.956; w/o drift ~0.027-0.030 -> recovery 0.817/0.990/0.508, with
  the largest-drift w/o seed (seed2, 0.0297) having the worst recovery (0.508).

## Concept boundary (frozen, Section 0/5)

role_pair_gate is a learned STATIC role-pair embedding. Gate Prior is an
initialization/optimization prior over static role-pair modulation. It is NOT
failure-conditioned dynamic gating; do not claim runtime failure awareness for it.

## Provenance

- train logs: formal_budget_post_sixth_freeze_v1.4_formal_main_20260802 / formal_ablation_v1.5_ppo_977_20260804 (locked)
- checkpoints: locked seed-0/1/2 PPO runs, nodes 100..977 (public bilateral nodes)
- held-out per-seed: formal_held_out_v1_5_10800_20260807 (locked)