# P2.8 assignment-observation implementation contract

## Scope

P2.8 implements only the P2.7-feasible lane-derived terminal preference
observation. It is an independent, opt-in extension of
`redundant_topology_uav`; default P1/P2 environment semantics remain intact.
No learner, optimizer, reward, action mask, failure group, topology, graph
edge, critic or evaluation tape is changed.

## Exact interface

`RedundantTopologyConfig.assignment_observation` defaults to `False`.

When `True`, `K` values are appended to each actor observation. For a terminal,
the appended block is a one-hot preference derived by matching the rank of its
initial y-lane with the rank of objective y-lanes. Scout and Relay appended
blocks are all zero. The terminal may still choose every action allowed by the
existing token-based mask; the cue is not an action constraint.

## Required validations

1. Default observation shape and values stay unchanged.
2. Enabled preference is one-hot, role-local, stable across a trajectory and
   bijective at small/main/large scales.
3. With identical actions and RNG domains, enabled and default environments
   have identical transitions, rewards, done flags, masks, routes and graph
   signatures.
4. Enabled runtime checkpoint reload is exact.

## Status boundary

P2.8 performs deterministic interface validation only. It does not allocate
new seeds, train PPO, evaluate a learned policy, rerun P2-R, or authorize P2.9.
