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

- preparation freeze: `ba3b3104ce39f80efb0f59d502b9861f7106ab6ad1fd75e321ca5a0d420a34a3`;
- provenance-audit source: `6da2b8002483d7a44704f43d83007030443aba189625c0e988f583b5e6397d1a`;
- provenance CSV: `b8e50407557db044622ac4be69ec8c9a89aa787545f1746fb0b9452d6fd25eb3`.

Preparation and P1-A technical isolation are complete, but execution remains
**not authorized**. The CPU-only audit at
`results/development/sr_drtp_p1_branch_isolation_audit_20260831_r2/`
returned `P1_BRANCH_ISOLATION_PASS`: A exactly reproduced the uninterrupted
Original-DRTP continuation; B changed only the sampler q vector through the
frozen anchor at intervention time; and C restored actor parameters plus their
Adam slots while retaining the critic step. No candidate P1 seed, formal or
held-out tape, official development trajectory, or SR-DRTP algorithm training
was used. The standard runtime-continuation regression also passed after the
default-off extension.

The next permitted state is `P1_EXECUTION_READY_FOR_AUTHORIZATION`, not a
launch. A separate human authorization must still specify the prospective
matched-shadow run. This preparation produces neither a risk signal nor a
scientific mechanism claim.

Before execution, implementation must additionally prove that branch B applies
only its temporary sampler anchor and branch C rolls back only the next actor
update while retaining the critic. Neither branch may mutate the official
Original DRTP trajectory. This report is not a P1 scientific result.
