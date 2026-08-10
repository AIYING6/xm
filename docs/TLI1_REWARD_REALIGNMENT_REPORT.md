# TLI1 Reward Realignment

## Status

`TLI1_REWARD_VALIDATION_PASS__NO_TRAINING_AUTHORIZED`

This stage changes only an opt-in evaluator-side reward potential. It does not
change N0 mission physics, the four-step hold, `engage_commit`, observation,
guidance actions, control timescale, horizon, or terminal precedence.

## Frozen reward semantics

When `mission_reward_alignment_v1_enabled=true` and the existing
`mission_progress_shaping_enabled=true`, the potential is bounded in `[0, 1]`
and higher is better. It is a weighted physical score composed of:

- distance inside the legal attack range (with a smooth penalty for both
  undershoot and overshoot);
- line-of-sight heading alignment;
- vertical separation;
- relative closing speed;
- the existing physical commit-hold progress.

The shaping term remains the standard potential difference
`gamma * Phi(s_{t+1}) - Phi(s_t)`. It uses only true evaluator-side relative
kinematics and the existing physical hold counter. It does not read graph,
communication, cache, sensing, `chain_closed`, or any actor-only proxy.

`NEUTRALIZED` remains the only mission success outcome. Terminal success and
failure bonuses are unchanged. Repeated `engage_commit` outside the physical
envelope cannot increase the potential.

The switch is opt-in so all prior N2/L0 evidence remains reproducible.

## Deterministic validation

`scripts/test_tli1_reward_realignment.py` passed 7/7 checks:

1. legal geometry scores above far-range state;
2. legal geometry scores above near-range overshoot;
3. legal heading scores above heading-reversed state;
4. legal altitude scores above excessive vertical separation;
5. legal closing motion scores above divergent motion;
6. potential remains bounded in `[0, 1]`;
7. out-of-envelope repeated commit does not change potential.

Raw output:

`results/tli1_reward_realignment_validation/TLI1_REWARD_VALIDATION.json`

## Decision boundary

This is a reward-definition validation only. No PPO training or performance
claim is authorized by this report. If development training is later
authorized, it must use the same L0 observation, action, timescale, horizon,
and seeds, with only this reward switch changed.
