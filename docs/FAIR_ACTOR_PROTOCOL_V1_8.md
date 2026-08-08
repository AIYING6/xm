# FAIR_ACTOR_PROTOCOL_V1_8

**Status: PRE-FLIGHT REVISION REQUIRED.** Comparator hierarchy and selection
rules are frozen below; failure-duration alignment remains unresolved pending
author choice. No formal training result is included, and no Stage 5 or
manuscript rewrite is authorized.

## 1. Frozen actor and packet contract

The sender-status packet is the schema in
[PACKET_SCHEMA_V1_8.md](PACKET_SCHEMA_V1_8.md): sender id/role, send-time
position/velocity/heading/energy, sender-local detection and attack-window
flags, target estimate and its confidence/generation/hop metadata, send and
delivery step, and validity. A receiver can use a packet only after delivery;
the newest valid delivered record is retained with explicit age and confidence.
Dropped, pending, failed-endpoint, expired, or invalid records do not enter the
actor view.

Each receiver gets an independent legal view `G_i`. Self state and local target
sensing are direct; teammate fields and teammate-local status are present only
when sourced from a delivered/cache-valid packet. Unavailable values are zeroed
before embedding and carry provenance validity. Edge geometry is computed only
from legal endpoints. Perception, communication, and task-support masks are
relation masks after provenance construction; they cannot create information.
Critic shared state and simulator-global values are excluded from actor input.

## 2. Frozen methods and architectures

| Method | Frozen actor input | Frozen representation |
|---|---|---|
| corrected EA-RG Full | recipient-specific `G_i` | three relation channels, edge-aware attention, role-pair gates, task-support relation, union/residual path |
| corrected wider single-graph | identical `G_i` and raw dimensions | single graph encoder over the same legal view |
| matched-information non-graph | identical `G_i` and raw dimensions | deterministic legal pooling (self, valid teammate mean, target, legal edge mean) followed by MLP; no graph message passing |
| MAPPO/HAPPO | legacy local observation only | unchanged no-graph actor; reusable only after R7.5 invariance PASS |

No Gate Prior, Task-Support, or Role-Pair ablations are in the minimal formal
matrix.

## 3. Frozen formal training budget and seeds

The minimal matrix is exactly three methods × three independent seeds:
`{0, 1, 2}`. Each run uses the same deterministic budget: 8 parallel
environments, 128 rollout steps per update, 300 updates, hidden width 128,
role/intent width 8, PPO epochs 4, learning rate 3e-4, clip coefficient 0.2,
entropy coefficient 0.01, max gradient norm 0.5, and the same strict sensing,
packet, delay/dropout, failure, and environment parameters. No resume,
mid-run protocol change, or post hoc budget extension is allowed.

The matrix contains 9 runs and 2,764,800 training environment transitions
before validation. Planning estimate (not a measured result) is approximately
18–36 wall-clock GPU-hours for training plus validation on the configured
hardware. This estimate must be replaced by measured per-run timing in the
formal run manifest; it is not a reason to alter the budget or seed count.

Validation runs every 10 updates on a fixed 20-episode validation population
whose seeds are `10000 + 100*training_seed + episode_index`. The checkpoint is
selected once per run using a censoring-aware validation estimand: (1) RMST at
`tau=80`, (2) establishment probability with its censoring rate reported
jointly, (3) RMST at `tau=220`, then (4) earlier checkpoint on ties. No
uncensored-only endpoint is used as a selection gate. The validation population
is never used for confirmatory estimates.

## 4. Frozen confirmatory endpoint and analysis

Primary endpoint: **time from failure onset to first stable task-chain
establishment**. “Recovery” and “true recovery” are not endpoint labels. A
chain is established when the legal task-chain predicate is true for `K=4`
consecutive environment steps. Failure onset is the fixed configured relay
failure start step. Episodes without establishment are right-censored at the
episode horizon (260 steps) or earlier terminal event.

Report RMST at `tau=80` and `tau=220`, with the endpoint origin at failure onset.
The primary architecture comparator is corrected EA-RG Full versus corrected
wider single-graph. The matched-information non-graph comparison is secondary;
MAPPO/HAPPO remain system-level comparators and may reuse frozen checkpoints
only under the expanded no-graph invariance audit.

Bootstrap is hierarchical: resample training seeds with replacement, then
episodes within each selected seed with replacement, preserving the seed as the
unit of independent training; use 10,000 replicates and percentile 95% CIs.
Report seed-level values and episode counts. Do not pool episodes as if they
were independent training replicates.

## 5. Frozen stopping and change-control rules

Stop without interpretation if any actor-boundary test fails, any method uses a
different legal raw-information set, a checkpoint is selected using confirmatory
episodes, a training seed is duplicated, a NaN/shape/provenance violation occurs,
or the held-out population is inspected before lock. After formal results are
seen, the following are immutable: packet fields, cache age/confidence rules,
mask ordering, architectures, budgets, seeds, validation rule, failure onset,
`K=4`, tau values, bootstrap hierarchy, censoring horizon, confirmatory anchor,
and primary comparator. Any change requires a new protocol version and cannot
be folded into v1.8 results.

## 6. Formal comparator hierarchy

1. Corrected EA-RG Full vs corrected wider single-graph (primary architecture).
2. Corrected EA-RG Full vs matched-information non-graph (secondary matched-information).
3. Corrected methods vs frozen MAPPO/HAPPO only as a system-level comparison,
   conditional on the trajectory-level invariance audit.

The old v1.6 measurements remain labelled legacy implemented-policy evidence;
they are not silently promoted to v1.8 corrected evidence.
