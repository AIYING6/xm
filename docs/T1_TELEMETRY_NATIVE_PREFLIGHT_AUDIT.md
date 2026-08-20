# T1 Telemetry-Native Reference Preflight Audit

**Status:** `PASS — preflight and adapter only; no long training authorized`  
**Contract:** `T1-TELEMETRY-NATIVE-REFERENCE-RUN-V1`  
**Adapter:** `T1-TELEMETRY-NATIVE-CHECKPOINT-ADAPTER-V1`

## Scope

This audit validates that an unchanged matched Single-Graph checkpoint can be
evaluated through the T0 sole-source recorder.  It does not create the reserved
T1 tape, train a policy, load a historical trained policy as evidence, or make
any performance claim.

## Verified properties

| Gate | Evidence | Result |
|---|---|---|
| Architecture identity | Adapter instantiates the current Single-Graph actor/critic with graph-derived role cardinality and validates `116,728` trainable parameters. | PASS |
| Checkpoint adapter | A deterministic final-policy callback loads an unchanged checkpoint and emits valid three-agent actions. | PASS |
| Actor boundary | Callback signature is exactly `(obs, share_obs, graph)`; simulator diagnostics remain inside T0 `diagnostic_only` records. | PASS |
| Raw source closure | Checkpoint evaluation uses `write_evidence_bundle`, which rereads raw JSONL and canonical-compares derived aggregates before writing them. | PASS |
| Determinism | The same loaded checkpoint receives the same actor-legal state twice and emits identical actions. | PASS |
| Historical isolation | Technical test creates a local untrained checkpoint only; it does not read historical result CSVs, aggregates, or model evidence. | PASS |
| Append protection | The T0 writer still rejects a nonempty evidence root. | PASS |

## Executed validation

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe -m py_compile \
  scripts/telemetry_native_t1.py \
  tests/test_t1_telemetry_native_checkpoint_adapter.py

D:/Anaconda/envs/.conda/envs/cac/python.exe -m pytest -q \
  tests/test_t0_telemetry_native.py \
  tests/test_t1_telemetry_native_checkpoint_adapter.py

5 passed
```

## Parameter-count correction caught by the preflight

The first adapter draft assumed four roles and instantiated `116,605`
parameters.  The frozen matched SG uses the role cardinality present in the
frozen graph (`max(4, max(role)+1)`), which produces `116,728` parameters.
The adapter now derives that value from the actor-visible graph and rejects any
other count.  No historical result is affected.

## Boundary

The next action is a separately authorized T1 launch decision.  Before such a
launch, provenance must confirm that seeds `2201–2205` and tape namespace
`920000–920099` have not entered prior evidence, then create the tape manifest
before any final checkpoint evaluation.  No long training, held-out work,
canonical work, algorithm change, or checkpoint promotion has occurred here.
