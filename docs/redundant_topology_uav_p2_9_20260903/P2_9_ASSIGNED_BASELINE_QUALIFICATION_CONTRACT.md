# P2.9 assigned-observation baseline qualification contract

## Authorization

P2.9 authorizes exactly:

`Plain role-SG-MAPPO / UTR role-SG-MAPPO × seeds 66011–66015 × 1,000,192 environment steps`.

There are ten cloud-only trajectories. It is a new environment-interface
version after P2.5/P2.6 learner corrections and P2.7/P2.8 formulation work.
Historical P2 and P2-R results are retained but not pooled with P2.9.

## Frozen interface

- `RoleSharedSGMPPO`: role bodies are separate; sharing only occurs within role.
- Relay is a deterministic one-action PASS interface.
- `assignment_observation=True`: terminal lane-to-objective preference is
  appended to actor observation; all non-terminal preference entries are zero.
- Physics, reward, action masks, topology, fault groups, automatic relay
  forwarding, critic and PPO hyperparameters remain frozen.
- Plain is nominal-only. UTR samples uniformly over nominal plus six frozen
  failure groups. Training never reads the development tape.

## Seeds, milestones and evaluation

P2.9 matched training seeds are `66011–66015`. Reserved independent
replication and confirmation ranges are `66021–66025` and `66031–66035`.
Milestones are `0, 125k, 250k, 500k, 750k, 1M`. Development evaluation is
seven conditions × twelve episodes at each milestone. No best checkpoint,
early stop, rerun or seed replacement is permitted.

## Precommitted 1M gate

The independent unit is the training seed.

1. Plain nominal: at least `3/5` seeds have success `>=0.50`.
2. UTR nominal: median success `>=0.50`.
3. UTR Tier-R: at least `3/5` seeds have mean upstream/downstream success
   `>=0.50`, and each R group has mean success `>=0.10`.
4. Every trajectory and endpoint is retained.

All items yield `P2_9_BASELINE_LEARNABILITY_PASS`; otherwise the only terminal
states are `P2_9_NOMINAL_LEARNABILITY_ONLY` or
`P2_9_BASE_TASK_NOT_LEARNABLE`. P3 is not authorized automatically.
