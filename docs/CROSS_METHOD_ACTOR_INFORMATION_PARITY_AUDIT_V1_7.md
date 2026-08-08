# Cross-method actor information parity audit v1.7

**Scope:** Stage 4.5 only. Static code/provenance audit; no algorithm change,
training, re-evaluation, or manuscript edit.

**Overall disposition:** `NEW_P0_INFORMATION_ASYMMETRY`.

EA-RG uses graph-conditioned actor inputs that are not used by the formal
no-graph MAPPO and HAPPO actors. These graph inputs contain centrally populated
teammate physical state, per-agent local status, pairwise geometry, and
relation/communication features. The target-state bottleneck is real, but it
does not establish parity for teammate-state provenance. The main EA-RG versus
MAPPO RMST80 comparison therefore mixes representation architecture with a
possible privileged-information advantage.

## Audited data flow

```text
simulator state
  -> UAVIntercept3DEnv._get_obs / _get_share_obs / _get_graph_obs
  -> stack_graphs (whole graph tensor)
  -> relation_adj and union adj
  -> RIGMAPPOActor.forward
       node_feat + role embedding -> relation GATs and union residual GAT
       obs -> obs_encoder
       target intent -> mean context
       concatenate -> policy_head -> action logits
```

`_get_graph_obs()` constructs every blue node row from simulator blue position,
speed, heading, velocity, detection flag, local attack-window flag and energy.
It constructs every pairwise edge from relative position/velocity, distance,
line-of-sight, team indicator, sensing, delivered communication, support,
message age and confidence. These values are constructed before graph masks are
applied. Under strict target sensing plus the target-information bottleneck,
the target node's physical state and target detection flag are zeroed; the
teammate rows are not equivalently provenance-masked.

## Feature-level parity matrix

Legend: **E** = EA-RG actor-visible; **M** = no-graph MAPPO actor-visible;
**H** = no-graph HAPPO actor-visible; **S** = single-graph actor-visible;
**C** = critic-only; **P** = possible provenance/privacy asymmetry.

| Information item | EA-RG | MAPPO | HAPPO | wider single-graph | Provenance finding |
|---|---:|---:|---:|---:|---|
| Self physical state | E | M | H | S | Same local self fields through `obs`; EA also has its self graph row |
| Teammate physical state | E/P | — | — | S/P | Centrally populated blue node rows; no per-UAV availability mask before graph encoding |
| Teammate internal/local state (`detected_by`, local attack window, energy) | E/P | — | — | S/P | Other agents' local flags are present in graph node rows |
| Target state | Zero-masked under strict bottleneck | — | — | Zero-masked under same env | Target mask controls target node, not teammate rows |
| Locally sensed target information | E through per-agent `obs`/cache | M | H | S | Acting agent target fields are zeroed when unavailable |
| Delivered communication | E | — | — | S | `comm_adj`, relation masks, message age and edge features are available to graph actors |
| Cached/stale communication | E/P | — | — | S/P | Age/confidence and cache-derived local fields are available; teammate cache provenance is not recipient-scoped |
| Message age/confidence | E | — | — | S | Edge features are built for all pairs; attention restricts aggregation only |
| Perception relation | E | — | — | S | Relation adjacency from `detected_by` |
| Communication relation | E | — | — | S | Relation adjacency from delivered `comm_adj` |
| Task-support relation | E | — | — | S | Active support requires role compatibility, delivered comm and source information |
| Edge geometry/features | E/P | — | — | S/P | Relative geometry is centrally computed for all pairs before masking |
| Relay-failure state | E indirect | M indirect via local obs only | H indirect via local obs only | S indirect | No explicit local failure scalar; graph actors receive failure-conditioned adjacency/age and node status |
| Attack-window state | E/P | M local only | H local only | S/P | EA/single graph see all blue `local_attack_window` node fields |
| Simulator-global information | E/P through graph construction | C only via `share_obs` | C only via `share_obs` | S/P through graph construction | Actor graph contains global simulator-derived teammate rows/edges |
| Critic-only shared state | C | C | C | C | `_get_share_obs()` contains all blue states, target state and aggregate status; not passed to no-graph actor |

## Mask and aggregation audit

1. **Feature construction precedes masking.** Node rows and pairwise edge
   features are populated from simulator state before `adj` or `relation_adj`
   is used by attention.
2. **A zero attention edge is not an availability proof.** The attention layer
   masks scores after computing projections and edge scores. The mask limits
   weighted message aggregation, but it does not demonstrate that the sender
   node or edge feature was legitimately available to the receiving UAV.
3. **Self-loops are always added.** `GraphAttentionLayer` and
   `RoleConditionedGraphAttentionLayer` use `adj + eye`, so each actor always
   retains its own node feature. This is appropriate for self state but does
   not repair teammate provenance.
4. **Union residual is a second aggregation path.** EA-RG's multi-relation
   encoder has perception, communication and task-support channels plus a
   union-graph residual path. The union path uses `adj`, which is the union of
   sensing, delivered communication and active support. It does not bypass a
   zero union edge, but it broadens message propagation beyond one named
   relation and therefore must be included in parity analysis.
5. **Pooling/context.** The target intent context is averaged and broadcast to
   blue actors; the chain-auxiliary head pools graph features for an auxiliary
   training target. These do not make MAPPO/HAPPO graph actors equivalent and
   do not convert critic-only state into actor input.

## Pairwise comparison decisions

| Comparison | Status | Reason |
|---|---|---|
| EA-RG vs MAPPO | `PRIVILEGED_INFORMATION_ASYMMETRY` | MAPPO formal actor is `graph_encoder=no_graph`; its policy uses only per-agent `obs`, while EA-RG uses graph node/edge/relation inputs containing teammate/global-derived fields |
| EA-RG vs HAPPO | `PRIVILEGED_INFORMATION_ASYMMETRY` | HAPPO wraps separate no-graph actors; centralized critics do not remove the EA-RG actor-side graph advantage |
| EA-RG vs wider single-graph | `MATCHED_INFORMATION` | Both use the same environment graph node/edge tensors, union adjacency and graph-conditioned actor path; difference is relation decomposition/capacity, not the underlying information set |
| Full vs w/o Gate Prior | `MATCHED_INFORMATION` | Same actor inputs and graph path; only initialization prior differs |
| Full vs w/o Task-Support | `PARTIALLY_MATCHED` | Same self/teammate node and most edge inputs, but support edge feature and task-support relation are explicitly removed in the ablation; this is a controlled representation removal, not a parity failure with external baselines |
| Full vs w/o Role-Pair | `MATCHED_INFORMATION` | Same node, edge and relation tensors; role-pair gate is replaced by a constant gate in the encoder |

## Direct answers

1. **Does EA-RG use simulator-global or otherwise unavailable teammate
   information?** It uses centrally constructed teammate node rows and pairwise
   geometry/local-status fields. Their legitimate per-UAV availability is not
   established; this is a potential privileged actor information path.
2. **Do these fields persist after packet loss/delay/failure?** The node rows
   remain populated. Delivered communication, age, confidence and adjacency
   change, but no general feature-construction mask removes teammate physical
   state or local-status fields when packets are not delivered.
3. **Do relation masks prevent leakage?** They restrict attention-weighted
   message aggregation. They do not prove feature provenance or erase globally
   populated node/edge tensors before the encoder.
4. **Do MAPPO/HAPPO receive the same information?** No. Their formal actor
   paths use no graph; their critics receive shared state, but critic-only state
   is not actor information.
5. **Is wider single-graph matched?** Yes at the actor information-set level;
   it uses the same graph construction and graph inputs, with a different
   encoder/capacity.
6. **Are ablations matched?** Gate Prior and Role-Pair are matched-input
   ablations. No-Task-Support is intentionally partial because the support
   relation/edge channel is removed. No-role-identity is also a deliberate
   input-removal ablation and should be treated as partial information parity,
   not as an external baseline.
7. **Can RMST80 be attributed purely to architecture?** Not against MAPPO or
   HAPPO under the current actor paths. The contrast may mix architecture with
   privileged graph information.
8. **Which comparisons remain scientifically fair?** EA-RG versus wider
   single-graph; Full versus Gate Prior; Full versus Role-Pair. Full versus
   Task-Support remains a controlled component ablation with an explicit
   representation removal.
9. **Which numerical evidence can remain unchanged?** Raw v1.6 numbers remain
   numerically valid as measurements of their implemented policies. The EA-RG vs
   wider-single and internal ablation numbers can remain as controlled
   representation comparisons. EA-RG vs MAPPO/HAPPO must not be presented as
   architecture-only or decentralized-fair comparisons.
10. **Which evidence must be downgraded?** EA-RG vs MAPPO/HAPPO RMST80,
    RMST220, establishment rates, and mechanism comparisons must be labelled
    descriptive under unequal actor information, pending a parity repair or a
    formally accepted centralized-information protocol.
11. **New P0?** Yes: `unfair actor information advantage` for EA-RG versus
    the no-graph MAPPO and HAPPO actors.

## Final recommendation

**C — `NEW_P0_INFORMATION_ASYMMETRY`.** Stop. Do not enter Stage 5, alter the
algorithm, retrain, re-evaluate, or rewrite the paper. Await the author's
decision on actor-boundary repair versus an explicitly centralized comparison
protocol.
