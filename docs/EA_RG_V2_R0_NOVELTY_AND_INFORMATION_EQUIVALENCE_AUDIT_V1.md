# EA-RG v2 R0 novelty and information-equivalence audit

## Question audited

Can “recipient-specific provenance-aware relational aggregation of multiple
legal target-evidence replicas” support a defensible new EA-RG v2 method claim
rather than a generic relation-aware GNN or a representation-capacity effect?

## Literature red team

The search covered relation-aware / temporal GNNs, communication GNNs in MARL,
uncertainty/confidence-aware evidence fusion, and permutation-invariant set
encoders. This is a qualification review, not an exhaustive systematic review.

| Adjacent line | What is already established | Consequence for EA-RG v2 |
| --- | --- | --- |
| GNN-assisted MARL communication | Graph encoders and attention-based selective message aggregation are established design patterns. | A relation-specific GNN alone is not novel. |
| Communication-aware GNNs under lossy links | Directed, time-varying lossy communication graphs have already been explicitly modeled. | Age/loss-aware edge features alone cannot be headline novelty. |
| Provenance/confidence-aware evidence fusion | Multi-source provenance and confidence-weighted fusion are established outside this exact UAV setting. | Merely preserving source/confidence does not establish a new mechanism. |
| Set / unified encoders | A sufficiently expressive invariant set encoder can represent functions of a complete evidence multiset. | Full cannot claim extra information if unified receives the identical multiset. |

Representative sources: [Deep Sets (Zaheer et al., NeurIPS 2017)](https://proceedings.neurips.cc/paper/2017/file/f22e4747da1aa27e363d86d40ff442fe-Paper.pdf), [universal representation of multiset functions (Tabaghi & Wang, ALT 2024)](https://proceedings.mlr.press/v237/tabaghi24a.html), [GNNs in MARL survey](https://arxiv.org/abs/2404.04898), and [communication-aware GNN for MARL with lossy links](https://doi.org/10.1109/access.2025.3554736).

## Information-equivalence result

Let `X_r` be the complete recipient-visible multiset of evidence replicas,
where each replica includes values plus every legal provenance, path, age,
confidence, availability, and cache-validity field. A strong unified baseline
that consumes `X_r` as replica-level nodes or a permutation-invariant set has
access to the same information as Full. Universal set-representation results
therefore prevent the claim that late relation-consistent aggregation has an
information-theoretic advantage over that comparator.

The only remaining possible EA-RG v2 claim would be an **inductive-bias or
sample-efficiency claim**: a specified routing constraint learns more reliably
under fixed data/budget. That is a much weaker and more crowded innovation
position. It requires a pre-specified structural theorem/constraint or a
controlled generalization setting; ordinary nominal performance cannot turn it
into an information-preservation contribution.

## Current schema audit

`_make_sender_status_packet()` currently includes target values, confidence,
generation step, hop count, and immediate sender identity. It does **not** carry
the target claim’s original detector/source or its ordered delivery path. The
selected recipient cache has those fields, but that cache is already a
selection/collapse, so it cannot retroactively annotate each independently
delivered sender-status replica.

Consequently, the current strict packet contract cannot instantiate the R0
requirement that Full and unified receive the same complete per-replica
origin/path metadata. Adding those packet fields would be a communication
schema/protocol change, not a harmless EA-RG encoder implementation.

## Provisional R0 decision rule

R0 can be a full PASS only if all three conditions hold:

1. the read-only prevalence audit clears its frozen multi-replica gate;
2. a separately authorized packet-schema specification makes complete
   per-replica provenance/path legal and identical for Full/unified; and
3. a mechanism is found that is structurally more specific than generic
   relation-aware routing and remains distinguishable from a strong unified set
   encoder.

Absent (2) or (3), the appropriate outcome is
`R0_PARTIAL__SCIENTIFIC_PROBLEM_VALID_BUT_MECHANISM_NOT_DISTINCT`, not a claim
that EA-RG v2 has been qualified for implementation.

## Executed read-only prevalence audit

The audit replayed strict-contract frozen L4 checkpoints `8901` and `8902` on
the 32 pre-frozen episode seeds `890000`–`890031`. It observed 3,599 and 3,596
pre-first-attack-range decision states, respectively. In both checkpoints,
the rate of two or more simultaneous legal target-evidence replicas was
**0.0%**, and no episode contained such a state. Immediate-sender, age, and
confidence disagreement rates were therefore also 0.0%.

This fails the pre-frozen 20% state and 20% episode prevalence gates before
any EA-RG v2 method is implemented. Together with the sender-status schema
gap and the information-equivalence finding, the R0 verdict is:

> `R0_NO_GO__EA_RG_V2_ALGORITHM_LINE_CLOSED`

This is not a reason to enlarge the task or add a v2.1 mechanism. It means the
current L4 task does not instantiate the candidate multi-replica aggregation
problem often enough to justify an EA-RG v2 algorithm line.
