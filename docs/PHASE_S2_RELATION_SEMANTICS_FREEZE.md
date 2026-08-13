# Phase S2 Relation Semantics Freeze

## Perception

`A[receiver, sender]` is the graph convention. A perception edge from blue
receiver `i` to target sender `j` is legal only when the environment's sensing
model marks `detected_by[i]` true. Strict sensing and the target-information
bottleneck prevent hidden target state from entering actor-visible graph data.
Information is fresh only under the frozen cache age and confidence rules.

## Communication

A communication edge `A[i, j]` means receiver `i` may receive a message from
sender `j`. It requires the physical communication range, valid sender and
receiver status, and the frozen dropout/delay realization. Relay failure
removes both directed edges incident to Relay 1. The direct `Scout→Attacker`
edge (`A[2, 0]`) remains legal whenever the physical rules permit it.

## Task-support

Task-support edges are derived from legally delivered communication and active
task-support state, not from ground-truth target state. They identify the
current support provider/path and may switch when the communication path
changes. They do not open an independent hidden information channel; the graph
union only includes relations explicitly exposed by the environment.

## Frozen implementation convention

The environment and graph encoder use `A[receiver, sender]`; invalid edges are
zero in the corresponding relation adjacency. Edge features are metadata and
do not override relation masks.
