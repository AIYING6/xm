# EDR-Q2 — Result-Free Paper Contribution Simulation

## Provisional title

**Deletion-Local Graph Policies for Robust Heterogeneous UAV Coordination under Relay-Node Failures**

## Result-free abstract

Relay-node failures can reorganize legal communication and task-support paths without causing a total information blackout. We formulate heterogeneous UAV coordination with an exogenous Relay failure that removes legal graph edges while direct compensation can remain available. We show that neighbour-softmax graph policies redistribute surviving incoming message weights after a deleted relay edge. We propose EDR-SG-MAPPO, a deletion-local fixed-normalized gated aggregation that restricts this denominator-induced redistribution while preserving legal topology-dependent replanning. Under matched exposure and legal decentralized inputs, future evaluation will cover nominal, canonical, OOD, safety, seed stability, topology/path mechanisms, scalability, and property-specific ablations.

## Contribution bundle

1. A legally specified heterogeneous Relay-failure topology-robustness task, without false unique-Relay or information-restoration claims.
2. Paired failure evidence for topology/path reconfiguration and mission degradation.
3. EDR, a deletion-local policy encoder aimed at a measured softmax redistribution pathway.
4. Matched F0/timing/duration/compound OOD, safety, seed, and ablation tests.
5. Mechanism, compute, and scalability analysis.

## Q2 plausibility

If EDR obtains stable 10–20% robustness improvement, at least 4/5 favorable seed directions, lower timeout, nominal retention, safety retention, and a property-specific ablation, this remains a credible Q2 paper. The paper does not need a performance doubling, but inconsistent gains or irrelevant ablations would invalidate the EDR method claim.
