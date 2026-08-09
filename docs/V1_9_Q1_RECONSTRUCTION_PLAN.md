# V1.9 Q1 Method Reconstruction Plan

**Status: D0 static audit and D1 engineering gate passed; D2 budget calibration
is prepared but not launched.** No v1.9 formal training, held-out evaluation,
OOD evaluation, or manuscript performance claim is authorized. This document
opens a new line without changing the in-progress v1.8 repair execution.

## 1. Decision

The v1.9 target is not an inflated claim that one method wins every metric.
The target is one falsifiable, high-value statement:

> Under recipient-specific partial observability, a policy that explicitly
> resolves legally measurable conflicts among local perception, delivered
> communication, and task demand can establish a stable task chain earlier
> than matched single-graph and non-graph policies; it has no claimed broad
> advantage when those evidence sources agree.

The candidate mechanism is PCRF, defined in the accompanying research-design
foundation package:
[scope](researchwrite/v1_9_q1_method_reconstruction/00_scope.md),
[canon](researchwrite/v1_9_q1_method_reconstruction/01_research_canon.md),
[evidence table](researchwrite/v1_9_q1_method_reconstruction/02_evidence_table.md),
and [argument map](researchwrite/v1_9_q1_method_reconstruction/03_argument_map.md).

## 2. What is removed from the headline

- Static Role-Pair gating: auxiliary only unless an independent future audit
  demonstrates nontrivial variation, representation influence, and necessity.
- Generic multi-relation naming: insufficient on its own because it is prior
  art and relations may be redundant.
- Unrestricted union residual: not the proposed explanation; a v1.9 method
  must make the conflict-conditioned fusion pathway auditable.
- “All metrics lead” as a success criterion: scientifically invalid and
  incompatible with pre-registration.

## 3. Required v1.9 gates before any formal run

| Gate | Requirement | Failure action |
|---|---|---|
| Legal-information gate | R5-style tests show identical lawful raw actor information for PCRF, wider single, and non-graph comparators. | Stop; repair boundary before pilots. |
| Conflict-exposure gate | Fixed rollouts show nontrivial, pre-specified relation conflict in the intended population and diagnostics. | Narrow/redefine the question; do not train a conflict method with no conflict. |
| Mechanism gate | PCRF gate/factor path responds to legal conflict descriptors and is neutral under agreement on fixed random batches. | Redesign or remove the mechanism. |
| Capacity gate | Wider single graph and non-graph are parameter/computation matched as closely as feasible. | Adjust comparator before performance work. |
| Protocol gate | New training seeds, validation seeds, confirmatory anchor, selector, endpoint, tau, and OOD grid are frozen. | Do not start formal training. |

## 4. Staged experimental investment

### Stage D0 — design and static audit (local CPU)

Implement no performance claim. Build PCRF feature/mask tests, conflict
descriptor unit tests, parameter-count comparison, and representation probes on
random batches. This stage must be inexpensive and produces no paper results.

### Stage D1 — engineering feasibility pilot (GPU; non-formal)

Use one or two engineering seeds and a short, fixed budget. Its sole purpose is
to detect NaN, incorrect actor boundary, inactive conflict gate, or grossly
inadequate compute budget. Do not pick architecture variants from final scores;
the decision criteria are correctness and feasibility.

**D0 capacity result:** PCRF at hidden width 128 has 196,856 actor parameters.
The closest single-graph actor is hidden width 168 with 195,837 parameters
(0.52% difference). This pairing is the D1 candidate; it remains subject to
the same input-contract and runtime audit before it can be frozen for formal
work.

### Stage D2 — budget calibration (GPU; non-formal; prepared, not launched)

After one candidate method is fixed, use a small PCRF-only pilot to measure
learning plateau, training-time variance, per-update runtime, validation
runtime, disk usage, and GPU-memory demand. This produces a budget proposal,
not a method comparison. The prepared D2 protocol fixes three engineering seeds
and a 100-update budget, but does not authorize the GPU launch.

### Stage F1 — frozen nominal core (formal)

Recommended target, subject to author approval after D2:

- PCRF: 5 independent training seeds;
- parameter-matched wider single graph: the same 5 seeds;
- matched-information non-graph: the same 5 seeds.

This is 15 full training runs. The primary test is PCRF vs wider single graph;
the non-graph test is secondary. All methods use the same legal raw actor
information, training budget, immutable validation snapshots, censoring-aware
selector, and a new held-out anchor.

### Stage F2 — confirmatory and mechanism evidence (formal evaluation)

Evaluate the selected checkpoints on a fresh deterministic confirmatory
population. Use hierarchical paired bootstrap with training seed → episode
resampling. Report all nominal primary outcomes, relation-conflict diagnostics,
and gate/factor measurements. The diagnostic suite cannot substitute for the
nominal primary test.

### Stage F3 — ablations and OOD (only after F1 supports the core claim)

Run the smallest necessary mechanism ablations, then the full pre-frozen graded
OOD grid. All severity levels and cells are reported. If F1 does not support
the primary claim, do not spend compute trying to rescue Role Gate or OOD.

## 5. Formal success and stopping criteria

PCRF can make its main claim only if all hold for PCRF vs wider single graph:

1. the pre-specified primary endpoint has the same favorable direction across
   all formal training seeds;
2. the hierarchical paired-bootstrap interval supports earlier establishment;
3. establishment probability has no material adverse tradeoff;
4. raw actor information, validation selection, and checkpoint provenance pass
   audit;
5. the conflict-conditioned pathway is active in its designated conditions;
6. the result is replicated on the untouched confirmatory population.

Failure of any of points 1–4 stops the architecture-superiority claim. Failure
of point 5 downgrades the explanation. Failure of point 6 prevents a
confirmatory conclusion. No criterion may be relaxed after results are seen.

## 6. Compute and AutoDL plan

AutoDL is appropriate for D1 onward because the current local run is CPU-bound.
Before any formal allocation, run a GPU smoke on one paid instance and record:

- CUDA/PyTorch versions and exact git commit;
- 8-environment rollout throughput and validation throughput;
- GPU memory, CPU utilization, and peak disk consumption;
- snapshot/event-record SHA256 persistence;
- cost per update, per validation, and projected cost per formal run.

Use the same managed output convention for every run. Back up completed
snapshots, validation records, manifests, and logs outside the instance because
local instance storage is not the only durable record. The exact GPU type,
worker count, final budget, and projected monetary cost remain author decisions
after D2 measurement.

## 7. Immediate actions now authorized by this design draft

1. Retain and monitor v1.8 repair without changing it.
2. Conduct D0 only after an explicit implementation authorization: PCRF design
   specification, actor-boundary tests, conflict-descriptor tests, and
   comparator-capacity audit.
3. Prepare an AutoDL reproducible environment and smoke checklist; do not rent
   an instance or start a GPU run without author approval.

No v1.9 full training, held-out evaluation, OOD evaluation, or manuscript
claim is authorized by this document.
