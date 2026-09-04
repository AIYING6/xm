# TATG-MAPPO P0 — new problem, not DRTP stabilization

**Status:** `ZERO_TRAINING_SEMANTIC_AND_NOVELTY_AUDIT_ONLY`.

## New scientific question

Under dynamic relay-topology failure, does a decentralized agent need a short
history of its own **legal** graph observations to infer transition context that
is not recoverable from one current graph snapshot?

This is an environment-and-information question. It does not ask why a DRTP
seed failed, whether an old training signal predicts return, or how to repair
an adaptive sampler.

## Candidate, conditional on P1

The conditional candidate is **Topology-Transition-Aware Temporal Graph MAPPO
(TATG-MAPPO)**: a single decentralized policy that combines the existing legal
graph encoding with a short recurrent state updated from local topology-change
residuals. The residual may use only a present and previous legal node/edge
feature, local message age, local cache age and the agent's own prior action.

It cannot use failure identity, failure timing, group metadata, central critic
inputs, a global graph, reward, selector, teacher, ensemble or evaluation
information. Collection remains the fixed UTR exposure schedule.

## Novelty boundary

GNN-based MARL for attrition and communication disturbance already exists, as
do generic graph-recurrent policies under partial observability. See Goeckner
et al., *Graph Neural Network-based Multi-agent Reinforcement Learning for
Resilient Distributed Coordination of Multi-Robot Systems* (2024), Ye et al.,
*Soft Hierarchical Graph Recurrent Networks* (2021), Wang et al., *R-MADDPG*
(2020), and Weil et al., *Towards Generalizability of MARL in Graphs with
Recurrent Message Passing* (2024).

Consequently, “SG-MAPPO plus a GRU” is explicitly **not** publishable novelty.
The later method must establish all three of the following:

1. a topology-transition information gap on the frozen legal interface;
2. a causal local transition residual, rather than generic recurrence alone;
3. improvement over both capacity-matched snapshot SG-MAPPO and a
   capacity-matched generic GNN+GRU control.

## Frozen route discipline

P0 does not implement or train a model. P1, if separately authorized, is a
two-cohort, policy-neutral information-gap diagnostic. It has no episode-return
or final-policy label. If it does not show that legal history adds repeatable
information beyond a current snapshot, TATG closes before implementation.

If P1 passes, the next action is only an exact formula, fairness and
serialization audit. Any performance experiment must then be limited to one
fixed formula, followed by a five-seed mature development cohort and one
disjoint five-seed mature confirmation cohort. No candidate revision is allowed
between the two cohorts.
