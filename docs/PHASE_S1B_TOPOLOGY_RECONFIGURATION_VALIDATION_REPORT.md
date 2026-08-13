# Phase S1-B Topology-Reconfiguration Mechanism Validation

**Protocol:** `PHASE-S1B-TRM-V1`  
**Source:** frozen paired S1 traces (`PHASE-S1-RV-V1`)  
**Status:** PASS TO S2 METRIC FREEZE; MARL training remains NO-GO until S2 gates pass

## Decision

S1-B supports a bounded robustness mechanism based on communication-path
reconfiguration, not information disappearance:

```text
Relay-node failure -> relay-edge removal -> path/source reconfiguration -> mission-score degradation
```

The analysis does not claim that Relay is the unique information intermediary,
and it does not require binary legal-information availability to decrease.

## Evidence

Among exposed failure-window traces, both Relay communication edges are zero,
while the direct `Scout -> Attacker` edge is unchanged from the paired nominal
trace. The attacker cache path changes from `0-1-2` in nominal traces to `0-2`
in the failure window. This is a reproducible route reconfiguration.

In the exposed failure window, the paired failure-minus-nominal deltas are:

- `Scout -> Relay`: approximately −0.18;
- `Relay -> Attacker`: approximately −0.21;
- `Scout -> Attacker`: 0.0000;
- legal information: +0.013--+0.107, not a decrease;
- task-chain support: 0.0000--+0.0052, effectively unchanged under the
  current flag;
- cache age: approximately −3.85 to −8.07 steps, indicating fresher
  direct-path information after reconfiguration rather than information loss.

The existing mission-score diagnostic remains lower under failure by roughly
3.9%–9.6%, depending on controller and seed. This establishes a useful
outcome signal but does not identify whether the cost is maneuvering,
coordination, geometry, reward, or another task component.

## Gate outcome

| Gate | Decision | Reason |
|---|---|---|
| Communication topology changes | PASS | Both Relay edges disappear in the failure window. |
| Path/source reconfiguration | PASS | `0-1-2` is replaced by `0-2`. |
| Mission degradation co-occurs | PASS as diagnostic | Existing paired `D_J` is positive in all six cells. |
| Information availability degradation | NOT REQUIRED / NOT SUPPORTED | `D_I` is negative in all six cells. |
| Causal mechanism beyond topology/path | UNRESOLVED | No frozen coordination-cost proxy yet. |

## Claim boundary

The project may now study whether relation-aware models handle communication
topology shifts and path composition changes more robustly than the matched
Single-Graph and MAPPO baselines. It may not claim that the Full model restores
lost information, preserves Relay-mediated information, or improves a strict
recovery endpoint.

## S2 entry requirements

S2 must freeze, before any MARL smoke:

1. primary mission estimand `D_J` and robustness ratio `R_J = J_failure / J_nominal`;
2. communication-edge and cache-path provenance fields;
3. a task-support-source definition that is not the current nearly invariant
   `chain_support_t` flag;
4. whether coordination/maneuver cost is a secondary diagnostic or omitted;
5. paired nominal/failure evaluation tape and exposure reporting;
6. legal-observation and hidden-state boundary audit.

S3 three-method MARL smoke is permitted only after S2 is separately frozen and
its artifact checks pass. Phase 3A canonical training remains NO-GO at this
stage.

## Artifacts

- Script: `scripts/run_phase_s1b_topology_reconfiguration_audit.py`
- Exposed topology summary: `results/development/phase_s1b_topology_reconfiguration/exposed_topology_summary.csv`
- Path counts: `results/development/phase_s1b_topology_reconfiguration/path_type_counts.csv`
- Paired deltas: `results/development/phase_s1b_topology_reconfiguration/paired_topology_deltas.csv`
- Manifest: `results/development/phase_s1b_topology_reconfiguration/manifest.json`
