# CHECKPOINT_SELECTION_PIPELINE_TEST_V1_8

**Status: PASS.** This is an engineering smoke test only; it is neither a
formal training run nor confirmatory evidence.

## Scope and immutable inputs

- implementation commit: `fd89edfc84a8151eb7f3a87fb5eb32e03419e81b`
- protocol label: `V1_8_FORMAL_PROTOCOL_REPAIR`
- method label: `corrected_ea_rg`
- non-formal engineering seed: `993`
- shortened engineering budget: 1 environment, 8 rollout steps, 10 updates,
  PPO epochs 4; validation at updates 1, 5, and 10 with one fixed episode
- retained formal environment semantics: strict recipient-specific actor view,
  drop probability 0.3, delay 2, radar dropout 0.1, failed relay 1, failure
  onset 40, duration 80, `K=4`, minimum success step 80

The shortened budget and single validation episode are deliberately outside the
formal matrix. They test persistence and selection plumbing only.

## Evidence

The immutable output root is
`results/formal_v1_8_repair/pipeline_smoke_ea_rg_seed993`. It contains three
separately created model snapshots, three snapshot metadata files, three
episode-event CSVs, three validation summaries, and an append-only
`snapshot_manifest.jsonl`.

| validation update | snapshot SHA256 | event record | RMST80 | establishment | censoring | RMST220 |
|---:|---|---|---:|---:|---:|---:|
| 1 | `ca3735ecf65dd12a54256f9d5a219a246a2b8d74449b48961b69097db26c4c6f` | seed 199300; censored at 220; timeout | 80 | 0 | 1 | 220 |
| 5 | `d106d3c16531810937d0fe638ec12ec6731838d37c13608027217ead5eb76910` | seed 199300; censored at 220; timeout | 80 | 0 | 1 | 220 |
| 10 | `6cd21bbf699297757ceea0dd975ce1988bd3e61d175eee0b309998935f459a7c` | seed 199300; censored at 220; timeout | 80 | 0 | 1 | 220 |

The selector independently re-hashed every snapshot, event CSV, and summary;
verified method/seed/update/protocol provenance; and applied the frozen order:
lower RMST80, higher establishment probability, lower censoring, lower
RMST220, then earlier update. All outcome fields tied, so the frozen earlier
update tie-break selected immutable update 1. The selected SHA256 is
`ca3735ecf65dd12a54256f9d5a219a246a2b8d74449b48961b69097db26c4c6f`.

## Result

The smoke proves that two or more genuine validation-time snapshots can be
persisted and selected from the corresponding immutable episode-level records.
It does not make any claim about learning quality or method performance.

An earlier seed-991 command was externally time-limited after it had persisted
only update 1; it is retained as an incomplete engineering trace under
`results/formal_v1_8_repair/pipeline_smoke_ea_rg_seed991` and is not used for
this PASS decision.
