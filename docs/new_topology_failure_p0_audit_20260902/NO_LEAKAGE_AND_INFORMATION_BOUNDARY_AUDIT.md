# No-leakage and information-boundary audit

Used: source-code semantics, roles, fixed legal paths, and deterministic fault-mask definitions.

Not used: trajectories, positions, communication realizations, dropout draws, policy actions, rewards, completed returns, training/evaluation/held-out tapes, checkpoints, seed performance, or historical method rankings.

A correct future mask must be an environment-side channel constraint and must be applied before message/cache propagation. The actor can observe only its resulting legal observations and graph, never a fault class label or an unmasked communication state.
