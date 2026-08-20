# T0 Telemetry-Native Implementation Audit

**Status:** `PASS — zero-training technical evidence chain only`  
**Protocol:** `T0-TELEMETRY-NATIVE-V1`

## Implemented artifacts

- `scripts/telemetry_native_t0.py` — environment adapter, passive raw-step
  recorder, sole-source aggregate reducer, manifest/hash writer, and an
  independent no-raw-logger comparator.
- `scripts/run_t0_telemetry_native_smoke.py` — bounded four-episode technical
  smoke using IDs `910000–910001`; these IDs are not development, held-out,
  or canonical evidence.
- `tests/test_t0_telemetry_native.py` — repeatable T0 gates.

## Technical evidence

The smoke executed two paired technical IDs under nominal and F0 (onset 44,
duration 80): four episodes and 1,040 logged transitions.  Its manifest
reported:

```text
source_closure_pass = true
historical_aggregate_reuse = false
raw_step_telemetry_sha256 = 377e901c3deeff5c532bc823e584a22bf8a48f142f48909c0f0e12e83f8e6f38
episode_aggregates_sha256 = 050ed18646edd2b86a2782e4f81789f12957f279cb00b1763023dcde6f70ca0f
```

## Required gates

| Gate | Evidence | Status |
|---|---|---|
| Raw source closure | Aggregates are regenerated from `raw_step_telemetry.jsonl` and canonical-compared before write. | PASS |
| Deterministic replay | Same ID/F0/zero policy gives equal raw records and aggregate. | PASS |
| Logger noninterference | An independent no-raw-logger rollout produces the same aggregate. | PASS |
| Actor boundary | Callback receives only `(obs, share_obs, graph)`; simulator state is only `diagnostic_only`. | PASS |
| Aggregate provenance | Manifest hashes both raw and derived files; historical aggregate reuse is explicitly false. | PASS |
| Append protection | A nonempty evidence root raises `FileExistsError`. | PASS |
| Frozen task semantics | Technical nominal/F0 use the S2 3DOF sensing, bottleneck, geometry and 260-step contract. | PASS |

## Boundary

T0 does not validate an algorithm, train a policy, create a development tape,
or authorize any development/held-out/canonical seed.  A separately frozen
telemetry-native reference-run protocol is required before the next training
decision.
