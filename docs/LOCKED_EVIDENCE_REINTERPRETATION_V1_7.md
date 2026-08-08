# Locked evidence reinterpretation v1.7

**Status:** Stage 1 scientific reframe; no numerical recomputation.

**Base:** `f0c7f57` / branch `scientific_reframe_v1_7`.

## 1. Decision

The v1.6 locked evidence is retained as legacy locked evidence. The paper's
primary question is redefined as stable task-chain establishment under relay
failure exposure. It no longer claims recovery of an already-established chain
after an observed disruption. A true `Established -> Lost -> Recovered` study
is deferred to a future benchmark.

## 2. Evidence disposition

The following remain numerically admissible unless a later code or statistical
audit identifies a concrete error: EA-RG versus MAPPO RMST80 and RMST220;
three-seed directions and hierarchical paired-bootstrap intervals; HAPPO and
wider single-graph comparisons; component ablations (Gate Prior, Task-Support,
and Role-Pair); robustness, OOD, efficiency, and mechanism traces.

No endpoint, comparator, time horizon, stability-window length, seed, or raw
episode is changed merely because the scientific interpretation changes.

## 3. Interpretation changes

The locked event is interpreted as the first stable task-chain establishment
after failure exposure. The time origin remains the evaluator's failure onset;
the exact event, window, termination, follow-up, and censoring definitions are
to be copied from the evaluator in Stage 2 rather than inferred from the old
manuscript wording.

| Legacy wording | v1.7 admissible wording |
|---|---|
| recovery event | stable-task-chain establishment event |
| recovery probability / Recovery | stable-task-chain establishment probability |
| `t_rec` | `t_est` / time to first stable-task-chain establishment |
| recovery KM | time-to-establishment KM curve |
| recovery RMST | restricted mean time to stable-task-chain establishment |
| faster recovery after disruption | earlier establishment after failure exposure |

RMST remains a valid restricted-mean time-to-event summary. Smaller RMST means
earlier stable task-chain establishment within the specified horizon; it does
not mean faster post-disruption recovery.

## 4. Claims to remove or weaken

The following claims are not supported by the locked event data and must be
deleted or rewritten: restoration of coordination; recovery of an interrupted
chain; post-disruption recovery; resilient reconfiguration; recovery
robustness; universal superiority across baselines, horizons, or shifted
distributions.

The phrase “decentralized execution” is retained only conditionally pending the
Stage 4 actor information-boundary audit. “Distributed per-UAV graph
construction” and “each UAV independently constructs its own graph” are not
admissible unless explicit implementation evidence is found.

## 5. Results that require relabelling or table notes

All captions, axes, table headers, supplementary labels, and response notes
using recovery terminology must be routed through the new estimand audit.
Table 1 must expose denominators and analysis populations separately when it
mixes establishment probability, conditional event time, RMST80, RMST220,
success, or other diagnostics. The numerical values are preserved unless a
specific statistical defect is demonstrated.

The pre-specified `tau=80` window is described as the active relay-failure
window, not as a guaranteed recovery window. OOD results are described as
shift-family-dependent early-establishment evidence, not recovery robustness.

## 6. Component and comparator claims

- **EA-RG versus MAPPO:** may support an earlier stable-task-chain
  establishment advantage under matched relay-failure exposure, especially in
  the pre-specified early window, with seed and scope qualifications.
- **HAPPO and wider single graph:** remain competitive-boundary comparators;
  no blanket ranking claim is allowed.
- **Gate Prior:** structured initialization / optimization prior only; not
  online fault adaptation or dynamic reconfiguration.
- **Task-Support:** empirical supporting evidence with seed heterogeneity; not
  an independently established causal mechanism.
- **Role-Pair:** auxiliary design; no independently validated contribution is
  claimed when its ablation does not show stable independent benefit.

## 7. Explicitly unresolved at this stage

This document does not decide the exact evaluator formula for `K`, failure
onset, censoring, or follow-up; those are Stage 2 audit outputs. It does not
decide whether CTDE or decentralized actor execution can remain; that requires
the actor information-boundary audit. It does not modify the manuscript,
figures, tables, code, or v1.6 artifacts.

## 8. Preservation rule

All v1.6 raw data and generated assets remain untouched and are referenced as
legacy locked evidence. v1.7 audit and manuscript assets must use separate
paths and must not be mixed into historical formal-evidence directories.
