# TATG-MAPPO P1.5 — exact CETM formula audit

**Status:** `ZERO_TRAINING_FORMULA_FAIRNESS_AND_SERIALIZATION_AUDIT`.

P1 established a narrow but repeatable fact: a current structural topology
snapshot, even with current edge age, can be ambiguous about whether a graph
is stable or has just transitioned. P1.5 freezes the only candidate permitted
to test whether that fact matters for control.

## Frozen CETM update

For agent *i*, form the actor-legal local topology vector

\[
x_{i,t}=\operatorname{concat}(R^{\mathrm{comm}}_{t}[i,:],
R^{\mathrm{support}}_{t}[i,:],\operatorname{age}_{t}[i,:]).
\]

Only the receiver row for blue-blue edges is retained. The module receives no
failure identity, failure clock, group label, global share observation, critic
input, reward or return. With \(\Delta x_{i,t}=x_{i,t}-x_{i,t-1}\),

\[
\eta_{i,t}=1-\exp\left(-\operatorname{mean}|\Delta x_{i,t}|\right),\qquad
z_{i,t}=\operatorname{GRUCell}([\Delta x_{i,t},a_{i,t-1}],m_{i,t-1}),
\]
\[
m_{i,t}=(1-\eta_{i,t})m_{i,t-1}+\eta_{i,t}z_{i,t}.
\]

The existing snapshot graph encoder provides \(h_{i,t}\), and the policy head
uses \([h_{i,t},m_{i,t}]\). When the legal topology residual is exactly zero,
the memory is exactly unchanged. This is the defining difference from a
generic graph-plus-GRU history encoder.

## Fair controls

The snapshot baseline is unchanged. The generic GNN+GRU comparator receives
the same current local topology vector and previous own action, and has an
identical GRUCell and policy-head size; it simply updates every step from
\([x_{i,t},a_{i,t-1}]\). Thus any later CETM advantage cannot be attributed to
added recurrent parameter count. A third ablation forces \(\Delta x=0\) in
CETM, directly removing transition information while retaining its parameters.

UTR collection, PPO objective, optimizer, reward, environment and centralized
critic are unchanged. Each rollout environment must serialize and restore the
memory, previous topology vector and previous own action exactly.

## Gate

P1.5 may only confirm that the formula is legal, capacity-matched and
serializable in principle. A pass permits a C1 implementation/serialization
audit. It does not permit PPO training, parameter tuning or a performance
claim.
