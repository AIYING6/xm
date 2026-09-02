# P2 frozen contract

Protocol: `P2-BASELINE-LEARNABILITY-TRAINING-SYSTEM-QUALIFICATION-V1`.

P2 contains exactly two main-scale, role-graph MAPPO baseline arms: Plain
(nominal only) and UTR (nominal plus the six P1-frozen R/C support classes).
The one allowed P2 contract supplement freezes the nominal anchor at **1/7**;
the six non-nominal groups are each also sampled at 1/7. This is derived from
the seven fixed training groups, before observing any P2 result.

Training seeds are `6201, 6202, 6203`, matched across arms.  The budget is
3,907 updates × 8 environments × 32 rollout steps = 1,000,192 environment
interactions per trajectory. Fixed checkpoints are updates 0/488/977/1953/
2930/3907 (0/125k/250k/500k/750k/1M labels). No best checkpoint is written or
promoted. Tier-I, held-out, structural OOD, adaptive distributions, reward
changes, PPO sweeps and all P3 candidates are excluded.

Formal P2 training is cloud-only. The local Q0 smoke is technical only.
