# Actor information contract v1.8 (R0)

**Status:** design freeze for review; no implementation authority yet.

## Deployment principle

For actor (i) at time (t), the legal actor input is the information that
one deployed UAV (i) could possess at that instant:

\[
I_i(t)=\{\text{self/local observation},\ \text{locally sensed environment},
\ \text{delivered packets to }i,\ \text{valid cached packets},\ \text{static metadata}\}.
\]

Centralized/vectorized software batching is allowed, but it must construct
recipient-specific views from (I_i(t)). Centralized simulator access must not
be copied into actor tensors merely because it is available in the environment.

## Allowed information

1. Self state and self-local observation: own position, velocity, heading,
   energy, sensor status and local attack-window state.
2. Target/environment information obtained by actor (i)'s own valid sensing.
3. Teammate information contained in a packet actually delivered to (i),
   including packet timestamp, age and confidence.
4. Historical teammate/target values retained in (i)'s cache, with explicit
   validity, age and confidence.
5. Relational quantities computed from the above values only.
6. Role identity and static platform/configuration metadata known at deployment.

## Forbidden information

- teammate true position, velocity, heading, energy or local status when not
  locally sensed or present in a delivered/cached packet;
- another UAV's `detected_by` or `local_attack_window` unless included in a
  delivered/cached packet;
- simulator-global target state or simulator-only pairwise geometry;
- a packet's future value before delivery, or a dropped/delayed packet's
  payload before its delivery step;
- critic shared state, aggregate state, failure labels, or terminal metrics;
- any unavailable raw feature embedded first and hidden only by attention.

## Availability semantics

Availability is resolved before node/edge embedding. Every non-self teammate
field has a validity bit and age/confidence metadata. When no valid sensed,
delivered or cached value exists, the value is encoded as zero (or a fixed
unavailable token) with validity=0. It must not be filled from simulator truth.

Relation/aggregation masks are applied only after this provenance step. They
answer whether a legal feature participates in perception, communication or
task-support aggregation; they do not grant access to an unavailable feature.

## Packet contract to freeze before implementation

The current environment's target-cache packet is the only existing delivered
payload. R4 must explicitly choose and implement any expanded sender packet.
Until then, no teammate physical state is assumed available merely because a
communication edge exists. A proposed auditable packet may contain:

- sender static role/id;
- sender self position, velocity, heading and energy at send time;
- sender local detection and attack-window flags;
- sender's target estimate, confidence, generation step and hop count;
- packet send/delivery step and validity.

Only fields explicitly included in a delivered packet may enter a receiver's
teammate view. Delayed packets enter only at delivery; stale values remain at
their last delivered value and carry increasing age.

## Scientific interpretation

The repaired claim, if later validated, is decentralized information
dependence with vectorized recipient-specific graph construction. It is not a
claim that each UAV independently executes a graph-building process, and it is
not a claim that simulator centralization implies actor information access.
