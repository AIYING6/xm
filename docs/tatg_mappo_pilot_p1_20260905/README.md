# TATG-MAPPO pilot P1 execution-interface preflight

This source-only audit connects the frozen pilot contract to existing,
already-audited execution interfaces:

- baseline: existing fixed-UTR snapshot PPO runner;
- temporal arms: isolated TATG outer collection and chronological actor replay;
- all temporal mutable state: actor, critic, optimizer, environment, action RNG
  and the three-tensor topology-memory payload;
- evaluation: a separate fixed-endpoint offline phase.

It performs no rollout, PPO update or evaluation. A pass permits the next
implementation/packaging step but never starts the 12 pilot trajectories.
