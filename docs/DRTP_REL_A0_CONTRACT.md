# DRTP REL-A0 — Multi-Tape Reliability Audit Contract

## Status

`FROZEN AFTER REL-A0-R ASSET RECOVERY PASS`  
Protocol: `DRTP-REL-A0-MULTI-TAPE-V1`

This is a zero-training post-hoc reliability audit. The historical Phase-S1-A
`F_TECHNICAL_INVALID` conclusion is retained unchanged. The recovered
checkpoint inventory is a separate provenance result and does not rewrite that
history.

## Checkpoint population

Five complete paired mature UTR/DRTP seeds are frozen: `1901, 1902, 2001,
2002, 2003`. Each method/seed uses its archived 10M final checkpoint and
runtime-state manifest. No checkpoint promotion, retraining, seed substitution,
or reconstruction from summary CSV is permitted.

The exact inventory and SHA256 values are in
`artifacts/drtp_reliability_a0/checkpoint_recovery_manifest.json`.

## Frozen methods and information boundary

- UTR-SG-MAPPO and DRTP-SG-MAPPO only;
- SG backbone and 116,728-parameter architecture unchanged;
- archived PPO, S2 environment, reward, failure semantics, and actor boundary;
- DRTP evaluation is post-hoc only; no sampler state is updated;
- deterministic policy evaluation; no training or optimizer step.

## Tapes and conditions

T0–T4 are fixed development-only tapes:

| tape | namespace | conditions |
|---|---|---|
| T0 | 440000–440099 | nominal, f0, timing, duration, compound |
| T1 | 450000–450099 | nominal, f0, timing, duration, compound |
| T2 | 460000–460099 | nominal, f0, timing, duration, compound |
| T3 | 470000–470099 | nominal, f0, timing, duration, compound |
| T4 | 480000–480099 | nominal, f0, timing, duration, compound |

Each tape reuses the frozen S1-A condition definitions and has 100 paired
episode IDs per condition. Tape manifests and hashes are frozen in
`artifacts/drtp_reliability_a0/tapes/`.

The resulting raw-record cardinality is **25,000**:
`5 tapes × 5 conditions × 5 seeds × 2 methods × 100 episodes`. Any earlier
30,000 figure is an arithmetic mismatch with the frozen five-condition,
five-tape design and is not used as an implicit extra experiment.

## Evaluation rules

For every method × seed × tape × condition, retain episode-level records.
Nominal and each perturbation condition use the same base episode IDs within a
tape. Report absolute returns, paired degradation, safety, exposure, and
topology/path telemetry. Training seed is the independent statistical unit;
episodes and tapes are repeated evaluation draws, not independent training
replicates.

## Stop rules

No new training, new algorithm, canonical training, held-out training, or
result-dependent tape/condition changes are allowed. After the audit report is
written, stop and wait for a separately authorized next phase.
