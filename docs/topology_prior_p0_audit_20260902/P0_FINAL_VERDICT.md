# P0 final verdict

`P0_PRIOR_UNDERDETERMINED`

The interface can implement a deterministic fixed sampler, and the bounded-simplex / `0.10` micro-residual geometry is feasible. However, the requested topology-informed fixed prior cannot be scientifically determined under the frozen no-rollout information boundary:

1. every failure group deletes the same Relay node, so static role-topology deletion does not distinguish groups;
2. the remaining distinguishers are timing and duration, which are schedule variables rather than topology;
3. dynamic connectivity, route redundancy, recoverability, and active support require trajectory state and cannot become a policy-independent p0.

Consequently no p0, implementation, training, P1, or novelty claim is authorized. The correct action is to preserve this negative design audit and stop this line at P0.
