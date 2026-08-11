# EA-RG v2 R0 scientific reconstruction protocol

## Status and scope

`EA_RG_V2_R0_SCIENTIFIC_RECONSTRUCTION_AND_NOVELTY_QUALIFICATION_AUTHORIZED__NO_IMPLEMENTATION__NO_TRAINING`

EA-RG v2 is a new candidate line, not a repair or continuation of v1.6. R0 is
read-only/design-only. It must not implement an EA-RG v2 actor, train, tune an
environment, use a held-out population, or reinterpret any v1.6/v1.9 result.

## Candidate scientific hypothesis

For a recipient, the same physical target can be represented by several legal
evidence replicas: local sensing, a delivered sender status packet, a forwarded
packet, and a cache-valid copy. Replicas may differ in immediate sender,
origin/path, age, confidence, and values. The candidate hypothesis is not that
multi-relational graphs are generally superior. It is the falsifiable claim
that **prematurely collapsing simultaneously legal, non-equivalent evidence
replicas into one target representation loses decision-relevant structure for
attack-range acquisition**.

## Non-negotiable information-equivalence contract

Any future Full and unified comparator must receive the *identical immutable
multiset* of legal evidence instances. Each instance must include exactly the
same target values, availability, age, confidence, immediate sender role/ID,
origin source, delivery path, and cache-validity fields in both methods.

The only intended difference is representational routing:

| Method | Permitted handling of the same raw evidence multiset |
| --- | --- |
| Full candidate | Preserve replica identity and relation labels through relation-consistent message passing; aggregate only at the stated late aggregation point. |
| Unified comparator | Consume the same replica nodes and metadata with a capacity-matched unified graph/set encoder, with one shared aggregation mechanism. |

Neither method may obtain an extra field, a privileged target truth, an
evaluator geometry label, a different cache, or a different action/critic
interface.

## Preimplementation definition: relation-consistent aggregation

An **evidence replica** is one immutable, recipient-visible target claim at one
decision time, identified by `(recipient, immediate_sender, generation_step,
delivery_instance)` and carrying its own values and metadata. It is not a
deduplicated entity state.

`origin_source` is the detector that generated the claim; `delivery_path` is
the ordered packet path from that detector to the recipient. A local sensing
claim has a one-element path. A direct/forwarded claim must retain the source
and full path in its delivered packet.

Allowed graph messages before aggregation are only between (i) a recipient and
its legal evidence replica, (ii) replicas of the same physical target, and
(iii) role/geometry nodes whose fields are already legal for that recipient.
Message eligibility is determined before feature construction by availability,
packet delivery, cache-validity, and age validity. Invalid, pending, dropped,
or expired claims create no target replica, edge, feature, or residual path.

Full must retain separate replica embeddings until one declared late operation:
`target_representation = A({h_replica}, relation labels)`. Provenance may be
used only as a declared relation label/routing key or as an identical raw feature
available to both Full and unified; it may not select hidden privileged
parameters or change the legal evidence set. The exact operator `A`, relation
classes, parameter sharing, and capacity match must be frozen before M2 code.

## R0 kill conditions

1. **Multi-evidence prevalence:** in *each* frozen L4 checkpoint, at least 20%
   of pre-first-attack-range decision states and at least 20% of episodes must
   contain two or more simultaneous legal target replicas. The audit must also
   report immediate-sender, age, and confidence disagreement. Otherwise:
   `MULTI_EVIDENCE_PREVALENCE_INSUFFICIENT`.
2. **Schema completeness:** every replica must carry its own origin source and
   delivery path in the legal packet, not infer them from simulator truth.
   Missing fields block a provenance/path mechanism specification.
3. **Information equivalence:** if a capacity-matched permutation-invariant
   set/unified encoder can consume the complete replica multiset losslessly,
   Full has no information advantage. A future comparison can at most test an
   inductive bias, not information preservation.
4. **Novelty:** relation-aware GNNs, graph communication MARL, uncertainty/
   confidence-aware evidence fusion, and set encoders must be red-teamed before
   code. “No identical combination” is not a novelty justification.

## Pre-frozen endpoints if and only if R0 passes

Mechanism: `P(attack-range acquisition | legal target evidence)`, evidence to
first attack-range latency, and the `NO_ATTACK_RANGE_ACQUISITION` fraction.
Task: neutralization rate and RMTN180. These would be defined before any
candidate method pilot; no endpoint is selected after results are observed.

## Non-inheritable v1.6 assets

The v1.6 recovery claim, global-ish actor graphs, Task-Support relation,
checkpoints, numerical comparisons, and formal results are excluded from v2
scientific evidence. The simulator, role infrastructure, packet/cache
semantics, strict actor contract, neutralization physics, and audit framework
may be reused as engineering assets only.

## R0 exit states

- `R0_PASS__MULTI_EVIDENCE_MECHANISM_AND_NOVELTY_DEFENSIBLE__READY_FOR_MINIMAL_IMPLEMENTATION`
- `R0_PARTIAL__SCIENTIFIC_PROBLEM_VALID_BUT_MECHANISM_NOT_DISTINCT`
- `R0_NO_GO__EA_RG_V2_ALGORITHM_LINE_CLOSED`

An R0 no-go closes the EA-RG v2 algorithm line; it does not authorize v2.1 or
another module substitution.
