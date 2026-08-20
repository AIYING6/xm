# T1 Telemetry-Native UTR-SG Reference Report

**Status:** `DESCRIPTIVE DEVELOPMENT REFERENCE ONLY`
**Protocol:** `T1-TELEMETRY-NATIVE-REFERENCE-AGGREGATE-V1`

This report is derived only from the new T1 per-seed
`raw_step_telemetry.jsonl -> episode_aggregates.jsonl` chain.  It does not
reuse a historical aggregate, promote a checkpoint, establish algorithmic
superiority, or serve as held-out/canonical evidence.

| Training seed | J nominal | J F0 | J OOD mean | J OOD worst | Collision | Timeout |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2201 | 84.409 | 60.938 | 61.909 | 53.845 | 0.000 | 1.000 |
| 2202 | 188.756 | 165.788 | 164.521 | 152.470 | 0.061 | 0.666 |
| 2203 | 98.946 | 57.777 | 58.979 | 49.154 | 0.083 | 0.917 |
| 2204 | 121.801 | 116.938 | 116.834 | 109.139 | 0.021 | 0.973 |
| 2205 | 61.882 | 44.521 | 45.089 | 38.109 | 0.000 | 1.000 |
| Pooled seed mean | 111.159 | 89.192 | 89.466 | 80.543 | 0.033 | 0.911 |

## Technical validity and safety diagnostics

- pooled survival to onset: `0.9927`;
- pooled trigger success in the alive-at-onset risk set: `1.0000`;
- pooled pre-trigger collision rate: `0.0073`;
- all pre-trigger terminations remain in unconditional return and safety metrics.

## Boundary

T1 is a new telemetry-native reference line.  It does not authorize a new
algorithm, a training extension, held-out or canonical evaluation, or a paper
superiority claim.  Any next comparison requires a separately frozen contract.
