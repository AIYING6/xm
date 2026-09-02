# P2-R formal corrected-learner requalification contract

## Authorization boundary

This contract authorizes exactly ten cloud-only trajectories:

`Plain SG-MAPPO / UTR SG-MAPPO × seeds 65011–65015 × 1,000,192 environment steps`.

It follows `P2_R_PREFLIGHT_PASS`. The historical P2 trajectories remain
forensic evidence only and must not be pooled with P2-R.

## Frozen implementation and data boundary

- Learner: P2.6 `RoleSharedSGMPPO` with independent Scout, Relay and Terminal
  policy bodies; sharing exists only between instances of the same role.
- Relay: deterministic PASS, one action, zero actor log-probability, entropy
  and gradient.
- Critic, PPO hyperparameters, environment, graph, reward, timing and failure
  semantics: unchanged from P2.
- Plain: nominal collection only. UTR: equal `1/7` collection from nominal and
  six frozen failure groups.
- Training has no access to the development tape. Development evaluation uses
  the frozen seven conditions and 12 episodes per condition/checkpoint.
- Checkpoints: `0, 125k, 250k, 500k, 750k, 1M`; no best-checkpoint promotion.

## Precommitted P2-R qualification gate

At 1M, with training seed as the only independent unit:

1. Plain nominal learnability: at least `3/5` seeds have nominal mission
   success `>= 0.50`.
2. UTR nominal retention: median nominal mission success is `>= 0.50`.
3. UTR Tier-R learnability: at least `3/5` seeds have mean upstream/downstream
   recovery success `>= 0.50`; both R classes have across-seed mean success
   `>= 0.10`.
4. Every completed seed, endpoint and milestone is reported. No failure is
   discarded or replaced.

`P2_R_BASELINE_LEARNABILITY_PASS` requires all four items. A pass qualifies a
separate P3 design review only; it does not start P3. Otherwise the terminal
states are `P2_R_NOMINAL_LEARNABILITY_ONLY` or
`P2_R_BASE_TASK_NOT_LEARNABLE`.

## Prohibitions

No seed replacement, rerun by performance, parameter search, reward or
environment change, source modification on A-line, held-out/OOD evaluation,
automatic continuation, or P3 execution is permitted.
