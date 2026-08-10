# TLI2 Continuous Policy Interface Design

## Status

`TLI2_CONTINUOUS_POLICY_INTERFACE_PASS__READY_FOR_DEVELOPMENT_AUTHORIZATION`

This stage implemented and tested only a reusable hybrid action distribution;
it did not connect the distribution to the formal PPO training entry point.

## Frozen interface

- continuous `turn_command` and `climb_command` in `[-1, 1]`;
- Bernoulli `engage_commit` with the existing physical semantics;
- `tanh`-squashed Gaussian for the continuous pair;
- exact inverse-tanh and Jacobian correction in `log_prob`;
- joint PPO log-probability is the sum of continuous and Bernoulli terms;
- deterministic evaluation uses `tanh(mean)` and commit probability threshold,
  not a fresh sample;
- fixed low-level controller remains responsible for 3DOF actuation.

## Synthetic gate

The following 8 checks passed:

1. sampled actions are finite and bounded;
2. saved sample log-probability equals recomputed log-probability;
3. joint PPO ratio is finite;
4. deterministic action uses the distribution centre;
5. commit output remains binary;
6. synthetic samples do not collapse to action boundaries;
7. one synthetic clipped PPO update has finite loss and gradients;
8. continuous and commit heads remain separate.

The earlier action-only validation also passed 4/4 and confirmed legal
observation provenance and fixed-controller decoding.

Artifacts:

- `results/tli2_continuous_policy_interface_validation/TLI2_CONTINUOUS_POLICY_INTERFACE.json`
- `results/tli2_continuous_guidance_action_validation/TLI2_CONTINUOUS_ACTION_VALIDATION.json`

The existing discrete actor-boundary regression remains `14/14 PASS`.

## Boundary

This is not a performance result and not a new method. The current categorical
RIGMAPPO actor is intentionally unchanged. A separate author authorization is
required before wiring this hybrid head into a development PPO run. L1, N3,
formal training, and OOD remain prohibited.
