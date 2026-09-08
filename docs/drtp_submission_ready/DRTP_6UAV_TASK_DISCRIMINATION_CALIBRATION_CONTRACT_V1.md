# 6-UAV task-discrimination calibration contract (V1)

## Purpose

This diagnostic asks whether a prospective 6-UAV topology-fault task is capable
of distinguishing nominal and faulted execution before a new UTR-versus-DRTP
training study is authorized. It is deliberately separate from algorithm
evaluation.

## Fixed scope

- Load completed frozen UTR endpoints only.
- Do not train a policy, update a sampler, modify source checkpoints, or run a
  DRTP comparison.
- Preserve the role order, observation/action dimensions, reward computation,
  graph interface, failure-family definitions, and fault step.
- Examine only a small predeclared set of geometry and cache-freshness
  candidates.

## Eligibility rule

A candidate is eligible for later protocol review only if all of the following
hold under the diagnostic replay:

1. Fault injection is effective before episode completion.
2. Nominal success is at least 0.60.
3. Aggregate perturbed success is strictly between 0.10 and 0.90.
4. Nominal-minus-perturbed success is at least 0.10 in at least two fault
   groups.
5. The median number of post-fault steps is at least three.

Passing this calibration does not establish DRTP superiority or authorize
training. Failing it means the candidate must not be used for a cross-scale
performance claim.

## V2 fault-step=3 implication

The audited v2 endpoint has effective faults but a success ceiling in all
groups. Its single-edge and single-relay degradations retain enough redundant
routes and cached support for the frozen UTR policy to complete every episode.
Thus, changing fault timing alone does not make the current 6-UAV task a
discriminative test of topology-aware training. Any later protocol needs a
separate, predeclared task-dependence design review rather than another blind
10M rerun.
