# Recipient-specific actor graph design v1.8 (R1)

**Status:** design only; implementation deferred.

## View definition

For each environment batch element and receiver (i), construct a separate
logical graph view (G_i(t)). Software may batch it as

```text
[batch, receiver_i, node_j, feature]
[batch, receiver_i, receiver_node, sender_j, edge_feature]
[batch, receiver_i, relation, receiver_node, sender_node]
```

The actor action is `action_i = pi(obs_i, G_i)`. No `G_i` may contain a raw
simulator value unavailable to receiver (i).

## Nodes

### Receiver/self node

Use the actor's current self observation and self state. Self position,
velocity, heading, energy, sensor flags and local attack-window state are valid
without communication. Self target fields use local sensing or the actor's own
valid target cache.

### Teammate node (j\ne i)

Populate only from the newest valid packet/cache held by receiver (i):

- static role/id (always valid deployment metadata);
- sender state fields explicitly present in the packet;
- sender local detection/attack-window fields only if explicitly transmitted;
- sender target estimate only if delivered or retained in cache;
- age, confidence, hop count and a validity bit.

If no valid packet/cache exists, sender dynamic fields are zero/unavailable and
validity=0. The simulator's `blue_pos[j]`, `blue_speed[j]`, `detected_by[j]`
and `local_attack_window[j]` must not be used as fallback values.

### Target node

Avoid one global target node shared by all actors. In (G_i), the target node
is populated from receiver (i)'s own detection or valid target cache only. If
no valid target information exists, use zero/unavailable features and a validity
bit.

## Edges and relations

### Pairwise geometry

For receiver (i) and sender (j), compute relative position, relative
velocity, distance and LOS only from receiver (i)'s self state and the valid
sender packet/cache in (G_i). If sender state is unavailable, geometry is
zero/unavailable; do not calculate it from `blue_pos[j]` in the simulator.

For receiver-target edges, use receiver-local target estimate/cache only. A
global simulator target position is forbidden.

### Perception relation

Set the relation bit only when receiver (i) has valid local target sensing or
an explicitly defined valid target estimate for the corresponding node. The
relation bit cannot create target features that provenance construction denied.

### Communication relation

Set the directed relation only when a packet from sender (j) has been
delivered to receiver (i) and remains valid under the frozen age/confidence
rule. A pending, delayed or dropped packet is not visible before delivery.

### Task-support relation

Compute task-support from legal receiver-view fields: static role metadata,
valid target/task fields, delivered sender packet and local attack-window
state. It is an aggregation label over legal features, not a source of hidden
state. If the source packet is unavailable, the support relation is zero.

## Mask ordering

1. Resolve packet delivery and cache state at the current simulator step.
2. Construct recipient-specific legal node fields and validity tokens.
3. Derive legal edge geometry/features from those fields.
4. Construct provenance masks and zero/unavailable values.
5. Construct perception, communication and task-support relation masks.
6. Apply graph encoder attention/aggregation.

No unavailable raw feature may enter the embedding at step 5 or earlier. A
relation mask is never a substitute for steps 1–4.

## Architecture compatibility

The existing EA-RG relation encoder can be retained conceptually: three
relation channels, role-conditioned gates, edge-aware attention and a union
residual. The input tensors become receiver-specific; the network need not
become multi-process or distributed. Input dimensions may remain unchanged if
validity/unavailable values are encoded within the existing feature budget; if
new validity channels are added, all matched graph baselines must receive the
same dimensions and semantics.

The wider single-graph baseline must consume the same (G_i) views and raw
feature contract, changing only its encoder/representation. Standard MAPPO and
HAPPO remain system-level local-observation baselines unless a matched-input
non-graph baseline is separately authorized.
