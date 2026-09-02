# No-leakage audit

Allowed inputs in this P0 audit were the frozen group member schedule, role identities, maximum episode length, and source-code semantics. No environment was instantiated.

Forbidden and unused inputs: training/evaluation returns, formal or held-out tapes, checkpoints, trajectories, policy actions, dynamic communication adjacency, target-cache states, attack-window states, completed-episode difficulty, and historical method rankings.

Dynamic route redundancy and mission-support reachability are intentionally excluded because the environment computes them from geometry, dropout RNG, sensing/cache state, and policy-dependent trajectory state. Treating them as fixed topology would silently introduce a policy/rollout dependency.
