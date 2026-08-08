# Matched-information non-graph baseline v1.8

## Purpose

This baseline is the R6 capacity-controlled comparator for corrected EA-RG and
corrected wider single-graph. It receives the same recipient-specific raw actor
view and the same packet/cache validity semantics, but has no graph message
passing or relation-conditioned aggregation.

## Actor input contract

For each receiver, the actor pools only legal fields from that receiver's view:

- receiver node features;
- mean of valid teammate nodes (validity is the final node provenance field);
- target node features;
- mean of legal edge features.

Invalid or unavailable nodes/edges contribute zero and are excluded from the
validity-weighted pool. Pending, dropped, failed-endpoint, or simulator-global
state is never read by this actor. The implementation is exposed as
`graph_encoder=matched_nongraph`; it uses the same hidden width and optimizer
family as the graph pilots, while removing graph message passing.

Standard MAPPO/HAPPO remain unchanged local-observation baselines. This
comparator is therefore a corrected EA-RG-side matched-information control,
not a replacement for the legacy baselines.

## Freeze and interpretation

The protocol is frozen for the R6 engineering pilot only. Short pilot outputs
are feasibility diagnostics, not performance evidence. No v1.6 checkpoint or
legacy numerical result is silently reinterpreted as evidence for this actor
contract.
