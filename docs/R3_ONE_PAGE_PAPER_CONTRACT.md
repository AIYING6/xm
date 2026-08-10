# R3 one-page paper contract: one bounded restart

**Project objective:** produce one rigorous algorithmic paper in the existing
3DOF heterogeneous-UAV, limited-communication coordination line. This is not
a new topic, an endless R4/R5 sequence, or a repair of the v1.9 F2 result.

## The one question worth testing

> Under a recipient-specific information contract, can a policy that maintains
> a time-aware, source-specific target belief from local perception (P) and
> delivered/cache-valid communication (C) coordinate more effectively than a
> source-aware unified temporal representation when the two legal sources are
> asynchronous or disagree?

This is a **candidate** question, not an established novelty claim. R3-0 must
first determine whether the required task states, independent physical outcome,
and literature distinction exist. If any is absent, do not implement it.

## Candidate core mechanism (one only)

The candidate mechanism is a **source-specific temporal belief update**:

- retain legal P and C provenance rather than merge them into one raw feature;
- track each source's timestamp, availability and uncertainty over time;
- update a target belief only from recipient-legal evidence;
- expose uncertainty to the actor as a decision-relevant state, rather than
  treating a learned graph gate as the innovation.

This is intentionally not a third relation, a union residual, a Role-Pair
module, or a post-hoc PCRF-R2 modification. Its novelty and precise equations
remain placeholders until a targeted prior-art audit is complete.

## Non-negotiable scientific controls

| Item | R3 decision |
|---|---|
| Actor information | Retain recipient-specific P/C contract; expired/pending/dropped/invalid packets are absent from C. |
| Primary comparator | A source-aware unified **temporal** representation receiving exactly the same legal raw P/C fields and temporal information. |
| Secondary comparator | Matched-information temporal non-graph policy. |
| Capacity/training | Match parameter capacity, optimizer, budget, seeds and selection rule. |
| Endpoint semantics | Retain terminal-outcome-safe restricted time-to-event semantics; no ordinary censoring of absorbing terminal failures. |
| Confirmatory evidence | Freeze F1/F2 separation, selected-checkpoint provenance, shared paired episode bank and hierarchical paired bootstrap. |

## R3 gates and hard stop rules

| Gate | Low-cost question | STOP if failed |
|---|---|---|
| R3-0: paper viability | Is there a defensible novelty distinction and a real physical/task outcome? | No new method or training. End this method-paper route. |
| R3-1: task feasibility | In method-blind development rollouts, does the pre-specified primary event have non-saturated incidence in its proposed horizon, and do P/C conflict states occur? | Do not tune a policy; redesign the task once or stop. |
| R3-D0/D1 | Does implementation preserve legal information and produce complete artifacts? | Repair implementation only. |
| R3-D2 | Can all comparators train stably under one shared budget? | Change only a common engineering budget; do not favor the candidate method. |
| R3-F2 | Does the untouched primary comparison meet its pre-frozen direction, SESOI, seed-stability and safety conditions? | Stop the R3 method line. No extra updates, seeds, endpoint changes or rerun. |

**Budget rule:** there is at most one new formal F1/F2 cycle after the R3-0,
R3-1 and D2 gates pass. A failed R3 F2 ends this algorithmic paper attempt;
it does not authorize R4.

## Evidence needed for a paper claim

| Intended claim | Required evidence | Forbidden shortcut |
|---|---|---|
| The mechanism is novel and needed | Targeted prior-art distinction plus R3-0 construct audit | Renaming a standard gate or graph encoder |
| The mechanism improves coordination | Untouched R3 F2 against the strong source-aware temporal comparator | Using only MAPPO/HAPPO or F1 validation |
| The benefit concerns source conflict | Pre-frozen intervention/common-onset diagnostic after a supported F2 | Inferring mechanism solely from aggregate return |
| The behavior matters physically | Independently defined physical/task outcome | Calling a graph predicate or readiness score capture success |

## Immediate next action

Run **R3-0 only**: a short, method-free viability check answering four binary
questions: (1) can the candidate mechanism be distinguished from prior work;
(2) can the simulator support an independent task-level outcome; (3) can a
primary event window be frozen before method performance is observed; and (4)
can the strong temporal comparator receive the same legal information. No code
for the candidate policy and no GPU training is authorized before four PASS
answers.

## Terminology ledger

| Canonical term | Meaning in R3 planning | Status |
|---|---|---|
| P | recipient's direct local target perception | retained |
| C | delivered and cache-valid communication evidence | retained |
| source-specific temporal belief | candidate R3 mechanism; no acronym assigned | provisional |
| source-aware unified temporal comparator | primary R3 comparator; same legal raw P/C and temporal fields | planned |
| R3-F2 | a future untouched confirmatory evaluation, if authorized | planned |

## Explicit boundary

v1.6 and v1.9 are retained as engineering/audit history and negative evidence;
they are not evidence for an R3 superiority claim. R3 may reuse the verified
information-boundary and reproducibility infrastructure, but it must train and
evaluate a fresh method population under a fresh frozen protocol.
