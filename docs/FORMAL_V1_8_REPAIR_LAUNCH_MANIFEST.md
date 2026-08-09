# FORMAL_V1_8_REPAIR_LAUNCH_MANIFEST

**Status: FROZEN after pipeline smoke PASS; authorized repair rerun only.**

This manifest preserves the scientific v1.8 protocol exactly. The sole repair
is training-time persistence: immutable validation snapshots, complete
episode-level event/censor records, frozen selector fields, and provenance
hashes. The first `results/formal_v1_8` matrix remains intact and is labelled
an execution attempt with an unrecoverable checkpoint-selection deviation; it
is retained only for engineering diagnostics, runtime, learning diagnostics,
and audit trail.

## Fixed scientific protocol

- source/protocol repair commit: `fd89edfc84a8151eb7f3a87fb5eb32e03419e81b`
- protocol label: `V1_8_FORMAL_PROTOCOL_REPAIR`
- methods: corrected EA-RG (`multi_relation`), corrected wider single-graph
  (`single`), matched-information non-graph (`matched_nongraph`)
- training seeds: `0, 1, 2`; 9 runs total
- 8 environments; 128 rollout steps; 300 updates; hidden/role/intent 128/8/8;
  PPO epochs 4; all other optimizer/reward/actor/packet settings exactly as
  `FORMAL_V1_8_LAUNCH_MANIFEST.md`
- failure: relay 1, onset 40, duration 80; stable window `K=4`; min-success 80
- validation: fixed 20 episodes every 10 updates and update 1, using base seed
  `10000 + 100 * training_seed`; no confirmatory episode is accessed.

## Required repair artifacts per validation point

At update 1 and each update 10 through 300, each run creates before validation
an immutable `actor_critic_update_XXXX.pt` and metadata JSON. The metadata
contains method, seed, update, git commit, protocol version, output run id,
UTC creation time, and SHA256. Validation then creates one immutable CSV with:
episode seed, failure onset, event indicator, first stable establishment step,
event time, censor time, termination reason, and terminal step. Its summary
contains RMST80, establishment probability, censoring rate, and RMST220.

The append-only per-run snapshot manifest hashes the snapshot, event record,
and summary. The selection program reads only those artifacts, re-verifies all
hashes and provenance, then freezes one winner using the pre-existing rule:
lower RMST80; higher establishment probability; lower censoring; lower RMST220;
earlier update tie-break.

## Stop gate

After 9 completed runs, the repair workflow must verify R5 14/14, actor-boundary
consistency, all 279 expected snapshots (31 per run), event-log/hash integrity,
and one frozen selected checkpoint hash per run. It then writes
`FORMAL_V1_8_REPAIR_SELECTION_MANIFEST.md` and stops. Any implementation or
protocol failure stops the process; no third training attempt, confirmatory
evaluation, OOD, ablation, architecture change, or manuscript edit is allowed.
