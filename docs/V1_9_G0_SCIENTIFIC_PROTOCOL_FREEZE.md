# v1.9 G0 — Scientific and Protocol Freeze

**Status: G0-R1 CLOSED; G0-R2 literature and theory/comparator gates CLOSED.
Source-separated implementation/D0-R2 remain separately unauthorized.**

This document records the pre-GPU hard gate that terminated PCRF-R1.  The
author selected a narrower two-source successor; its current theory and
comparator authority is defined in [PCRF-R2 theory/protocol freeze](V1_9_PCRF_R2_THEORY_AND_PROTOCOL_FREEZE.md)
and [G0-R2 final freeze](V1_9_G0_R2_FINAL_THEORY_COMPARATOR_FREEZE.md).
It authorizes neither D1-R2, D2, F1, held-out evaluation, OOD, an ablation,
nor a manuscript superiority claim.

## 1. Immutable scope and execution routing

The project follows the author-approved order:

```text
finish v1.8 repair selection freeze
  -> G0 hard gate
  -> PCRF-R2 novelty kill-check and G0-R2 release
  -> source-separated PCRF-R2 D0 then D1-R2 engineering gate
  -> three-method D2
  -> F1 formal training
  -> untouched F2 confirmatory evaluation
  -> preregistered mechanism and graded external-validity studies
```

`v1.8` remains a separate fair-information repair track.  Its existing repair
runs must be allowed to finish, then receive snapshot inventory, SHA256,
event-record integrity checks, and a selector manifest.  It is not a PCRF-R1
optimization branch and cannot justify a v1.9 headline claim.  Earlier D2 and
D2-R1 outputs are retained only as engineering/provenance history because they
predate the PCRF-R1 semantic freeze.

## 2. Historical PCRF-R1 question and hypotheses

The following was the PCRF-R1 question before G0-R1 terminated it:

> Given the same legally available recipient-specific signals, does preserving
> distinct relation channels and conditioning their fusion on legal source
> disagreement yield earlier stable task-chain establishment than a strong
> single-graph encoder?

The only intended confirmatory hypotheses are:

| ID | Pre-result hypothesis | Required comparison | Failure consequence |
|---|---|---|---|
| H1 | PCRF-R1 establishes earlier than the strong single graph by the prespecified practical margin. | PCRF-R1 vs wider single graph | Stop the architecture-superiority headline. |
| H2 | The PCRF-R1 minus single-graph contrast becomes more favourable as independently occurring legal relation conflict increases. | preregistered low/high conflict strata | Stop the conflict-conditioned mechanism claim. |
| H3 | Full PCRF-R1 exceeds an otherwise identical `Delta=0` control in conflict-rich conditions. | Full vs `PCRF-Delta0` | Stop the deviation-necessity claim. |

MAPPO/HAPPO are system-level reference methods only.  They cannot establish H1.
The matched-information non-graph method is secondary: it tests whether graph
message passing adds value, but it is not the pure architecture comparator.

## 3. Historical PCRF-R1 equation and information partition

For receiver \(i\), PCRF-R1 is frozen as

\[
w_i=\operatorname{softmax}(\log\pi_0+\Delta(c_i)),\qquad
h_i=\sum_{r\in\{P,C,T\}}w_{ir}h_i^r,\qquad \Delta(0)=0.
\]

`X_base = {baseline_gate_logits}` consists only of three learned global scalar
logits.  It has no per-receiver input and therefore has an empty intersection
with the dynamic conflict-input set.  The allowed dynamic set is

\[
X_{conflict}=\{\text{masked P/C/T support, pairwise disagreement,
delivered-edge age, delivered-edge confidence}\}.
\]

The actor information boundary remains stricter than this notation: no critic
state, simulator-global state, unreceived/dropped payload, unavailable
teammate geometry, or unobserved target state may enter either factor inputs
or \(c_i\).  The 14 actor-boundary tests are a continuing hard requirement,
not novelty evidence.

## 4. Comparator contract

All primary methods receive the same recipient-specific `node_feat`,
`edge_feat`, provenance validity, role labels, and legal union adjacency from
one environment graph view.  In the current 18-field edge schema, fields
11/12/13 explicitly expose perception/communication/task-support relation
identity, and fields 15/16 expose message age/confidence.  Thus the intended
representation-only contrast is:

| Method | Permitted raw legal fields | Representation constraint |
|---|---|---|
| PCRF-R1 | all shared legal node/edge/provenance fields plus separate P/C/T masks | three factor encoders and baseline-plus-conflict fusion; no union residual |
| wider single graph | the same shared legal node/edge/provenance fields, including relation identity and age/confidence | one shared encoder on `P union C union T`; no separate factor path |
| matched-information non-graph | the same legal graph tensors before its deterministic pooling | no graph message passing |

The single graph already receives the conflict-relevant raw metadata through
its edge features.  It must not be deprived of those fields in a future
launcher.  A second `single+conflict-metadata` control is unnecessary only if
the pre-launch input-hash audit confirms this exact contract.

## 5. G0-A empirical audit result — relation identifiability failure

The read-only audit in
[`V1_9_G0_COMPARATOR_AUDIT_REPORT.json`](V1_9_G0_COMPARATOR_AUDIT_REPORT.json)
used five fixed environment seeds and 120 method-independent action steps per
seed, under the intended delay/dropout/failure configuration.  It saw 605
recipient graph states.  It found:

| Audit check | Result |
|---|---:|
| PCRF/single shared raw graph source | yes |
| relation identity present in shared edge fields | yes |
| edge relation flags mismatch their relation masks | 0 entries |
| union adjacency fails to contain any relation edge | 0 entries |
| communication/task-support mask mismatches | 0 entries |
| communication/task-support exact equality | 605/605 states (100%) |
| communication/task-support mean Jaccard | 1.000 |

The subsequent G0-R1 audit in
[`V1_9_G0_R1_TASK_SUPPORT_IDENTIFIABILITY_AUDIT.md`](V1_9_G0_R1_TASK_SUPPORT_IDENTIFIABILITY_AUDIT.md)
confirmed the same conclusion at support, feature, and intervention levels.
This confirms a critical structural limitation in the current frozen
environment implementation: `Task-Support` is a duplicate of `Communication`,
not an independently activated task-compatibility relation.  Consequently,
the current implementation cannot support a **three independently meaningful
relation** claim, H2 cannot distinguish C from T, and H3 would not establish
the claimed three-source mechanism.

This is a G0 **No-Go**, not a reason to tune an architecture or search for a
favourable metric.  The author subsequently selected option 3 below and
authorized PCRF-R2 in its separate theory/protocol freeze.  The options were:

1. terminate PCRF-R1 as a three-relation headline; or
2. approve a new, separately versioned information-contract/environment repair
   that makes task support independently legal and reruns boundary/static
   audits; or
3. approve a narrower two-source PCRF research question, with a new theory,
   comparator, and protocol version.

No R1 architecture repair is authorized by this historical document.

## 6. Endpoint and censoring contract for any future F1/F2

The endpoint origin is the fixed failure onset.  The event is the first
`K=4` consecutive-step legal task-chain establishment.  An episode horizon is
fixed before training and `tau=80`/`tau=220` are restricted follow-up horizons,
not descriptions of an active-failure window.

The environment ends on success, collision, constraint violation, or timeout.
For a future v1.9 estimand, collision and constraint violation are absorbing
mission failures in the implemented simulator: after either, establishment is
known to be impossible.  They must **not** be treated as ordinary early right
censoring.  The proposed frozen estimand is the restricted establishment time

\[
T^*=\begin{cases}
T_{est}, & \text{if stable establishment occurs by }\tau,\\
\tau, & \text{if timeout or absorbing mission failure occurs before establishment.}
\end{cases}
\]

Report establishment probability, absorbing-failure probability, timeout
probability, and `mean(T*)` (the restricted mean establishment time) together.
This avoids a non-identifiable Kaplan--Meier assumption after an absorbing
terminal event.  A formal v1.9 protocol must specify whether it calls this
restricted score “RMST”; it may not silently mix it with ordinary censoring.

Before F1 is unlocked, a method-blind D2 endpoint-adequacy audit must test
event fraction, absorbing-failure fraction, and precision/CI width.  It may
not use which method is ahead to change difficulty or \(\tau\).

## 7. Statistics and training change control

The historical intended primary contrast was PCRF-R1 minus wider single-graph restricted
mean time at \(\tau=80\), with lower being better.  Analysis must resample
training seeds first and evaluation episodes second; episode pooling never
substitutes for independent training replicates.

The following remain unresolved and are therefore a hard G0 block rather than
numbers to choose after outcomes: the practical margin \(\delta_{min}\), the
precision threshold `W_max`, the seed-contrast variance threshold `V_max`, and
the total F1 seed count.  The recommended statistically clean choice is either
eight seeds for *all* primary methods from the start, or a prewritten
direction-neutral `5 -> 8` expansion triggered only by CI width/variance.  It
must never depend on significance, winner identity, or whether a CI crosses
zero.

Any later D2 may adjust only engineering logistics before F1 is frozen (common
wall-clock budget, telemetry cadence, disk allocation, and a method-blind
endpoint adequacy range).  It may not modify the architecture, raw actor
information, packet/cache semantics, reward, optimiser, learning rate, hidden
width, failure protocol, primary comparator, endpoint definition, or the
confirmatory seed bank.

## 8. Novelty kill-check and formal release rule

The nearest-work search and paper-by-paper overlap table are maintained in
[`V1_9_G0_NOVELTY_KILLCHECK.md`](V1_9_G0_NOVELTY_KILLCHECK.md).  Its narrow-claim
status is now `NOVELTY_KILLCHECK_PASS_WITH_NARROWED_CLAIM`; the final G0-R2
theory/comparator release is recorded in
[`V1_9_G0_R2_FINAL_THEORY_COMPARATOR_FREEZE.md`](V1_9_G0_R2_FINAL_THEORY_COMPARATOR_FREEZE.md).

`G0_PASS` requires all of the following:

1. independent task-support activation or an author-approved narrower theory;
2. exact raw-input equality audit for PCRF, single graph, and non-graph;
3. literature kill-check of 8--15 verified nearest papers (completed for R2);
4. numerical \(\delta_{min}\), seed rule, and method-blind endpoint adequacy
   bounds written before D2/F1; and
5. a revised three-method D2 protocol consistent with these locks.

The historical R1 gate remains closed.  For R2, the current valid status is
`G0_R2_THEORY_AND_COMPARATOR_FROZEN__IMPLEMENTATION_NOT_AUTHORIZED`.
