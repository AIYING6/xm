# SR-DRTP P1 preparation report

The P0 result supplies exact update-boundary restore/replay. This preparation
freezes the prospective P1 question, candidate event grid, 16-update horizon,
three isolated branches, dual cohorts, and stop rules before any prospective
outcome is inspected.

The 16-update horizon is an engineering unit: 16 × 4 × 64 = 4,096 official
environment interactions per branch. It is deliberately shorter than the
32-update DRTP adaptation interval, so P1 measures immediate conditional
utility rather than a new long-horizon stabilization result.

## Provenance and execution boundary

The explicit seed-provenance audit reports `P1_SEEDS_CLEAN` for Cohort A
(`4401`–`4405`) and Cohort B (`4406`–`4410`): no candidate appeared in an
uncompressed explicit seed field, command-line seed argument, or seed-prefixed
name in the repository at preparation time. The audit deliberately does not
treat arbitrary numeric values in logs as seed use. Its machine-readable
record is `SR_DRTP_P1_SEED_PROVENANCE.json`.

Frozen artifact SHA-256 values:

- preparation freeze: `7fbbd645f7bc4ba85ca417c2690f2ecb7460981188151ed2f664e31cd60480a3`;
- provenance-audit source: `6da2b8002483d7a44704f43d83007030443aba189625c0e988f583b5e6397d1a`;
- provenance CSV: `b8e50407557db044622ac4be69ec8c9a89aa787545f1746fb0b9452d6fd25eb3`.

Preparation is complete, but execution is **not authorized**. Before a future
P1 authorization can launch anything, a new zero-training technical audit must
demonstrate branch-B sampler-only isolation, branch-C actor-only rollback with
critic retention, exact paired RNG/runtime restore, and non-mutation of the
official Original-DRTP trajectory. This preparation produces neither a risk
signal nor a scientific mechanism claim.

Before execution, implementation must additionally prove that branch B applies
only its temporary sampler anchor and branch C rolls back only the next actor
update while retaining the critic. Neither branch may mutate the official
Original DRTP trajectory. This report is not a P1 scientific result.
