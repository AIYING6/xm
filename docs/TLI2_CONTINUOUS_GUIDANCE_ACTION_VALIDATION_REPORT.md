# TLI2 Continuous Guidance Action Validation

## Status

`TLI2_CONTINUOUS_ACTION_VALIDATION_PASS__NO_TRAINING_AUTHORIZED`

This is an action-only, no-training diagnostic. It does not alter the PPO
network, environment transition, reward, observation, timescale, or mission
physics. It samples the same legal L0 observation trajectories and maps a
normalized continuous command `[turn, climb, engage_commit]` through the fixed
low-level controller interface.

## Validation

Across eight fixed L0 evaluation seeds and up to 64 legal observation states
per seed, the following deterministic checks passed:

- all continuous commands and reconstruction errors were finite;
- each command was bounded and representable by the existing fixed controller;
- commands did not spend most states at maximum turn/climb boundaries;
- the command was computed from the legal observation row only, and the fixed
  controller did not read target truth or communication state.

The validation artifact is:

`results/tli2_continuous_guidance_action_validation/TLI2_CONTINUOUS_ACTION_VALIDATION.json`

## Important boundary

This pass establishes only that a continuous guidance interface can be formed
without information leakage and can be decoded by the fixed controller. The
current PPO implementation still has a categorical action head; no continuous
PPO training was performed or authorized by this stage. A later development
test would require a separately reviewed continuous-action policy interface,
while keeping all other L0 settings fixed.

No L1, N3, formal training, or performance claim is authorized.
