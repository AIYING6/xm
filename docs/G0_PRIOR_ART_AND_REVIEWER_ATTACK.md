# G0 prior-art and reviewer-attack review

## Focused literature position

| Work | Relevant lesson | Boundary for G0 |
|---|---|---|
| Agarwal, Kumar and Sycara, *Learning Transferable Cooperative Behavior in Multi-Agent Teams* (2019) | Transferable cooperative behavior requires an explicit transfer/generalization question rather than a single in-distribution score. | G0 defines a frozen structural topology family and reports seed-level transfer evidence, but does not claim universal transfer. |
| Weil et al., *Towards Generalizability of Multi-Agent Reinforcement Learning in Graphs with Recurrent Message Passing* (2024) | Graph-structured MARL generalization is sensitive to graph structure and message-passing design. | G0 tests topology structure changes without changing the actor or adding recurrence. |
| Anil et al., *MOHITO* (UAI 2025) | Hypergraph/task-open formulations make relational structure explicit for changing multi-agent systems. | G0 is a fixed-size communication/task benchmark and does not claim task-open or variable-size generalization. |
| Li et al., *Disentangled Graph Self-supervised Learning for OOD Generalization* (ICML 2024) | OOD graph generalization requires careful separation of structural and nuisance shifts. | G0 separates timing/duration parameter OOD from structural topology OOD and does not infer mechanism from return alone. |

## Reviewer attacks and responses

1. **“The suite is just another failure-timing sweep.”** Response: timing/duration are explicitly the parameter-OOD comparator; U1–U5 alter node/edge structure or directionality.
2. **“U6 is an impossible graph.”** Response: U6 is retained only as diagnostic-only and is excluded from primary inference by the frozen feasibility audit.
3. **“You pooled episodes as repetitions.”** Response: the decision unit is training seed; pooled episodes are used only to estimate within-cell policy performance.
4. **“The actor saw the topology label.”** Response: topology modes configure the environment only; no topology descriptor or global route label is supplied to the actor. Actor-boundary and graph-legality checks are part of the audit.
5. **“This proves arbitrary topology generalization.”** Response: it does not. The claim is limited to the fixed-size, legal, pre-registered U1–U5 family.
6. **“The Relay is a unique information mediator.”** Response: that claim is explicitly outside the evidence boundary; direct legal paths and path reconfiguration are retained.

## Sources

- https://arxiv.org/abs/1906.09347
- https://arxiv.org/abs/2402.05027
- https://proceedings.mlr.press/v286/anil25a.html
- https://proceedings.mlr.press/v235/li24br.html
