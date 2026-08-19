# UTR One-Shot Telemetry Terminal Technical-Validity Outcome

## Final status

```text
UTR-ONE-SHOT-MECHANISM-TELEMETRY-V1
TECHNICAL_INVALID — archived aggregate replay is not stable within the
prospectively frozen V2 float32 compatibility envelope.
```

This is a terminal outcome for this one-shot telemetry acquisition.  It is
not a model-performance result and does not alter any historical Phase-D,
DRTP, TCR, SPC, or UTR conclusion.

## Immutable execution record

The final attempt used the five frozen UTR 2M checkpoints, the historical
Phase-D tape descriptors, and the first 50 existing tape IDs per selected
condition.  The 35-cell semantic logger-invariance gate passed before any
full acquisition.

The acquisition stopped after writing 779 of the planned 1,750 diagnostic
episode summaries.  The stopping cell was:

```text
checkpoint seed: 2102
condition: f0_seen_44_80
episode ID: 440029
field: traveled_distance
logger aggregate: 157837.9797668457
archived aggregate: 157838.00662231445
absolute error: 0.02685546875
relative error: 1.70145767326e-07
```

The value exceeds the V2 archived-aggregate comparator
`abs_tol=1e-5, rel_tol=1e-7`.  V2 explicitly prohibits a third tolerance
increase after such a failure.

## Consequences

- The partial raw telemetry directory is retained for provenance only and
  must not be analysed as a completed Good-vs-Weak evidence set.
- No `UTR_GOOD_VS_WEAK_MECHANISM_DISCOVERY_V2` or mechanism decision is
  produced from these partial data.
- No new training, checkpoint replay variant, evaluator modification,
  numerical-threshold adjustment, or algorithm design is authorized by this
  outcome.
- The earlier aggregate-only conclusion
  `DATA_INSUFFICIENT_FOR_MECHANISM_DISCOVERY` remains the last valid
  scientific conclusion about the Good-vs-Weak mechanism.

## Rationale

The evaluator-versus-logger semantic check passed, so there is no evidence
that passive telemetry altered a trajectory.  However, the legacy archived
aggregate cannot be reconciled with the passive logger under the final
prospectively frozen numeric envelope across the requested full diagnostic
set.  The contract therefore requires technical invalidation rather than
post-hoc relaxation or selective analysis.
