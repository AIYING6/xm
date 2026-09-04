# TATG-MAPPO fresh-seed pilot P0 preregistration audit

**Verdict:** `TATG_PILOT_P0_PREREGISTRATION_READY`.

The first TATG performance experiment is defined before any policy training: three fresh matched training seeds, a fixed one-million-step endpoint, fixed UTR exposure, CETM, snapshot-actor UTR and two parameter-matched temporal controls. The existing fixed-UTR sampler requires four environment streams, so the frozen layout is four environments by 64 rollout steps; this preserves the 256-step update and exact one-million-step budget. The central critic, reward and environment semantics remain fixed. CETM actor epochs must replay complete rollouts chronologically; the snapshot baseline keeps ordinary PPO.

The offline development tape has five fixed conditions with 100 shared base episodes each. It is read only after every trajectory reaches update 3,907; no milestone is selected by return. The directional rule requires a positive mean paired CETM-versus-UTR primary metric, nonnegative paired gain for at least two of three seeds, no new zero-success seed, nominal retention within `-0.05`, and a CETM cohort mean no worse than either temporal control.

This audit executed zero environment steps, PPO updates and evaluation episodes. A pass does not start training or make a performance claim. It only makes the exact 12-trajectory pilot eligible for separate execution authorization. A failure closes CETM without tuning; a pass would require a separately authorized independent five-seed replication.
