# Redundant task-path graph design

## Frozen design direction

For main scale B, use the directed layered support graph:

```text
S1 ----> R1 ----> T1
 |        |        |
 |        v        v
 +------> R2 ----> T2
S2 ----> R1/R2 ----> T1/T2
```

Every `S_i -> R_j -> T_k` route is a candidate legal support path. The semantic design must require: (i) a scout observation not reconstructible by terminals alone, (ii) a relay-carried support message, and (iii) terminal action conditioned on legal, age-bounded support. Nominal B has eight directed routes, four relay-edge-disjoint branch pairs from the Scout layer to the terminal layer, and two internally relay-node-disjoint branches for a fixed source-terminal pair.

**Critical distinction:** this is not an approval to add graph edges. P1 must prove active use through actor observations, message provenance, cache-age legality and action/attack gating. Dynamic radio connectivity, dropout and policy behavior are secondary realizations of a frozen static task-support mask, never substitutes for the mask.
