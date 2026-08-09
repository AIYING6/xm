# v1.9 D1-R2 P0-B Delta Requalification Protocol

**Status: `AUTHORIZED_ENGINEERING_ONLY__PERFORMANCE_USE_PROHIBITED`.**

This is the author-authorized delta requalification after the P0-B repair that
excludes expired target claims from the R2 C source. It does not reopen R2
architecture, reward, physics, RMTE estimand, training budget, or comparator
definition. It is not D2 or performance evidence.

## Fixed scope

- methods: `pcrf_r2`, `single_r2`, and `matched_nongraph_r2`;
- one new non-evidentiary engineering seed per method: `9401`;
- 15 updates, 8 environments, 128 rollout steps, PPO epochs 4;
- validation/snapshot at updates 1, 5, 10, and 15;
- strict recipient-specific sensing, packet dropout 0.3, delay 2, radar
  dropout 0.1, and the existing failure schedule;
- output root distinct from both prior D1 roots;
- no resume test or third full 6x30 D1, because the unchanged CUDA, snapshot,
  resume, hash/provenance paths have already passed two full D1 gates.

## Required evidence

1. current P0-B deterministic cache-age suite passes before launch;
2. actor-boundary, D0-R2, and P0-A regressions pass before launch;
3. each run has four immutable snapshots, summaries, and episode event records;
4. train logs are complete and finite, stderr is empty, and the R2 actor
   encoder exists in every snapshot;
5. event-record and RMTE selector fields recompute from immutable records;
6. runtime/protocol/source-commit hashes are attested in an immutable manifest.

The resulting gate may only establish that the repaired age filter survives
the real rollout/training data path. It cannot compare methods or support a
scientific performance claim.
