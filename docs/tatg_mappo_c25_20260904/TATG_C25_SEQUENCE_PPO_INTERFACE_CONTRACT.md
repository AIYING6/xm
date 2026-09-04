# TATG-MAPPO C2.5 — sequence PPO interface contract

## Finding

The existing snapshot PPO runner correctly collects tensors as `[time, environment, ...]`, then flattens and randomly permutes time–environment rows. That is valid for a snapshot policy. It is not valid for CETM: replaying an isolated later graph does not reconstruct its legal preceding topology state.

This is an implementation-interface finding, not evidence for or against TATG's performance.

## Frozen resolution

For the initial qualification only, each PPO epoch must replay every complete vectorized-environment rollout sequence in chronological order from the exact `TATGRuntimeStateBank` payload saved before collection. At each time step:

1. compute the actor log-probability for the stored action from the current legal graph and current CETM state;
2. record the stored action as `a_previous`;
3. if the stored environment completion flag is true, reset only that slot from the following reset graph before the next actor call.

No temporal chunks, burn-in, truncated BPTT or random flattened graph minibatches are allowed in this first runner. The ordinary centralized snapshot critic and PPO value loss remain unchanged. Candidate CETM, generic current-snapshot GRU and delta-zero CETM ablation share the identical sequence runner.

## Decision boundary

`TATG_C25_SEQUENCE_PPO_RUNNER_REQUIRED` authorizes only a separately frozen sequence-runner implementation and same-rollout PPO correctness audit. It does not authorize a parameter update, environment rollout, evaluation, cloud run or performance claim.
