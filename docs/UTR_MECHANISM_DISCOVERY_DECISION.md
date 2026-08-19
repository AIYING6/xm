# UTR Mechanism Discovery Decision

**Final status:** `DATA_INSUFFICIENT_FOR_MECHANISM_DISCOVERY`
**Protocol:** UTR Good-vs-Weak Seed Mechanism Discovery
**Scope:** zero-training, existing-assets-only review of Phase-D 2M UTR seeds 2002/2101/2102/2103/2104

## Decision

The available Phase-D UTR assets establish cross-seed performance dispersion and timeout-heavy weak cells, but they do not preserve the time-aligned behavioral evidence required to identify a reproducible failure mechanism. In particular, existing records have no per-agent action/position history, no step-level role/task progression, no time-indexed path/support sequence, and no recoverable terminal windows.

The existing evaluator constructed transient path/support trace entries during historical evaluation, then reduced them to episode aggregates and did not save the trace. Aggregate path fraction, path-switch count, traveled distance, control effort, terminal step, and timeout cannot establish temporal ordering or distinguish a behavioral precursor from a terminal consequence.

Therefore the required chain cannot be evaluated from existing evidence:

```text
topology transition → behavioral precursor → task/support degradation → timeout.
```

This is neither `MECHANISM_IDENTIFIED` nor `NO_REPRODUCIBLE_MECHANISM_FOUND`: the mandatory behavioral-data gate fails before those analyses are permissible.

## Immutable constraints honored

- No new training, continuation, evaluator run, rollout, replay, environment stepping, tape, held-out seed, or canonical seed was used.
- No checkpoint was loaded to execute a policy.
- No model, environment, reward, PPO, actor boundary, sampler, or algorithm was changed.
- No pre-trigger collision or other episode was deleted or reclassified.
- Historical DRTP, TCR, EDR, and R1 decisions were not altered.

## Permanent route disposition

Under the protocol’s stop rule, the current new-algorithm search is permanently closed. It must not be revived by designing another graph module, loss, recurrence, gate, predictor, sampler, or other architecture from the same aggregate evidence.

R1 remains the sole active paper route:

```text
R1 — Freeze the validated topology-robustness problem and build the system-robustness paper.
```

This decision authorizes no canonical training, new formal OOD, formal baseline retraining, scalability study, held-out run, or paper experiment. Those actions require separate author authorization and a separate frozen protocol.
