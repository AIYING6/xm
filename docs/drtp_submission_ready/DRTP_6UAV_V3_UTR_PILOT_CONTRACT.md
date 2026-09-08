# DRTP 6-UAV V3 UTR-only learnability pilot contract

## Scope

This is an isolated qualification study for the V3 sustained-support task. It
trains **UTR only** on the seven equal-probability topology groups using three
fresh seeds: 94011, 94012 and 94013. It does not instantiate DRTP, tune a
sampler, compare methods, or provide manuscript performance evidence.

## Fixed protocol

- 1,000,192 environment transitions per seed (3,907 updates × 4 environments
  × 64 rollout steps);
- same final endpoint for every seed; no early stopping, checkpoint promotion
  or seed replacement;
- 40 deterministic episodes per seed and group at the fixed endpoint;
- training and evaluation use separate random-number namespaces.

## Qualification criterion

The pilot may proceed to a later, independently reviewed formal protocol only
when at least two of three UTR seeds have nominal success at least 0.50, and
mean perturbed success is neither saturated (>= 0.90) nor globally collapsed
(<= 0.10). This is a learnability gate, not a DRTP result.
