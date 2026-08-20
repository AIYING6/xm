# T3 — Final Method Design Review

## Candidate tested concept

The only T3-consistent candidate before this review was an attacker-side, path-agnostic **Task-Support Continuity Belief**:

\[
b_A^t=F(b_A^{t-1},o_A^t,G_A^t),\qquad \hat Y_A^t=P(Y_A^t(16)\mid\mathcal H_A^t).
\]

It would retain the 116,728-parameter SG backbone and augment the actor with `b_A^t` under an auxiliary continuity loss.

## Decision tests

| Required design test | Result | Consequence |
|---|---|---|
| actor-local, path-agnostic, reproducible target | PASS | `Y_A^t(16)` is valid only as a training-only diagnostic target. |
| instantaneous legal predictability | PASS | Current local state has signal. |
| meaningful history gain | **FAIL** | Best gain is +0.0083 AUC at `L=4`; longer windows decline. |
| graph-history incremental value | **FAIL** | Legal graph history does not improve prediction. |
| topology-switch specificity sufficient for a temporal method | **FAIL** | The same current-observation signal is present in nominal/pre periods; no history-specific switch effect was established. |
| stronger-than-GRU structural distinction | **FAIL** | Prior art plus absent history gain reduce the candidate to generic recurrent MAPPO with an auxiliary classifier. |
| clean role-supervision coverage | **FAIL** | Only attacker has a directly grounded label; Scout/Relay targets would be invented. |
| modest/fair complexity | not evaluated | No eligible method remains to estimate. |

## Rejected implementation outline

No continuity-state module, recurrent state, graph-temporal encoder, auxiliary loss, parameter-matched control, or ablation contract is frozen. Implementing one would violate the T3 principle that a method must arise from an identified capability gap rather than from a plausible architecture story.

## Comparator implications

The T2 comparator contract remains historical and unchanged: MAPPO, matched SG-MAPPO, UTR-SG-MAPPO, one future final method if justified, and exactly one fair external structural comparator. T3 selects no final method, so it authorizes no new tape, development run, held-out run, or canonical run.

## Review result

The scientifically correct T3 design outcome is **no eligible architecture**. This does not invalidate the frozen task, S2 boundary, T1 reference, or T2 M2 observation. It rejects only the proposed temporal-continuity algorithmic route.
