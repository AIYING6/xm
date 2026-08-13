# Phase S1-A Failure Exposure and Information-Mechanism Audit

**Protocol:** `PHASE-S1A-EM-V1`  
**Source protocol:** `PHASE-S1-RV-V1`  
**Status:** COMPLETE — ROBUSTNESS TRAINING NO-GO  
**Scope:** read-only audit of the existing 600 paired S1 episodes; no new training and no rerun of the environment.

## Executive decision

S1-A does not authorize S2 freeze or S3 MARL smoke. The current paired
experiment contains a reproducible mission-score degradation, but it does not
support the proposed causal chain

```text
Relay failure -> loss of legal information -> task-support degradation -> mission degradation
```

The decisive reason is that every episode that reached the frozen failure
trigger already had a direct `Scout -> Attacker` communication edge and a
`0-2` attacker cache path at the first failure-active observation. Thus Relay
was not a necessary information intermediary at failure onset.

The bounded conclusion supported by the evidence is:

```text
the paired relay-failure condition is associated with a 3.9%--9.6%
mission-score decrease under the tested transparent controllers;
the current telemetry does not establish Relay-mediated information loss.
```

## Evidence and provenance

The audit reads, without modification, the S1 artifacts under
`results/development/phase_s1_paired_robustness/`:

- 1,200 episode rows: 2 conditions × 2 controllers × 3 seeds × 100 episodes;
- six timestep-level provenance CSVs;
- development seeds `1401`, `1402`, `1403`;
- no canonical seeds, checkpoints, or MARL training.

The independent audit outputs are under
`results/development/phase_s1a_mechanism_audit/`.

## Gate-by-gate findings

### Exposure audit

Of 300 failure-condition episodes per controller, 278 reached the frozen
failure-active interval and 22 terminated before the trigger. The 22 episodes
were not removed, reweighted, or silently treated as exposed. Their common
classification is `terminated_before_failure_trigger`; no evidence of a
failure-guard race was found in the existing trace.

The exposure rate is therefore 278/300 = 92.7% for both controllers. This is
below the preregistered S1 adequacy rule and remains a blocker for the original
S1 claim.

### Failure-trigger dependency audit

Among the 278 exposed episodes for each controller:

- direct `Scout -> Attacker` communication at the first failure-active row:
  **278/278 (100%)**;
- direct target sensing at that row: **0/278**;
- attacker cache path at that row: **`0-2` in 278/278 (100%)**;
- legal attacker information at that row: **278/278 (100%)**;
- chain-support flag at that row: **0/278**.

This is not a post-failure recovery event. It is a pre-existing direct path at
failure onset. Consequently, the failure does not establish Relay dependency
under the frozen endpoint semantics.

### Information mechanism

The binary legal-information metric is not degraded by the failure condition.
It is slightly higher in the failure traces, yielding negative `D_I` in all six
controller × seed cells. The time-resolved audit shows the same pattern:

- pre-trigger legal-information rate: 1.000 in both conditions;
- during the failure-active window: failure 0.952--0.987, while the paired
  nominal traces are 0.885--0.933;
- post-trigger cache age is lower in failure traces than in nominal traces;
- later direct links and the `0-2` path are common and must not be labelled as
  bypass only after the fact.

The most defensible interpretation is path reorganization / compensatory
direct communication under the paired action tape, not information loss
mediated by Relay failure. The current data cannot distinguish whether the
mission-score decrease comes from geometry, coordination cost, reward-side
effects, or another task term; that mechanism must not be asserted.

### Mission degradation and dynamic range

The mission score decreases consistently in the existing paired diagnostic:

- `structural_oracle`: approximately 3.9%--4.0% per seed;
- `legal_observation`: approximately 9.1%--9.6% per seed.

This is a useful non-catastrophic robustness signal. It is not sufficient to
validate the intended Relay-mediated causal explanation because the failure
dependency audit fails.

## What is fixed versus what is not

### Fixed by this audit

- non-exposure is a pre-trigger termination category, not an analysis filter;
- trigger-time direct communication and post-trigger direct/recovery paths are
  separate quantities;
- `D_I < 0` is an observed result, not a numerical error;
- no canonical result, headline survival result, or training result was used;
- Phase 3A and all MARL training remain **NO-GO**.

### Not established

- Relay necessity at failure onset;
- Relay-failure-induced legal-information loss;
- mediation through task-support availability;
- superiority of Full, Single-Graph, or MAPPO;
- any Role-Gate retention conclusion.

## Minimum next protocol recommendation

Do not patch the current S1 data or redefine `D_I` after seeing the result.
There are only two scientifically valid options:

1. **Close the Relay-mediated claim** and retain the current 3.9%--9.6%
   mission degradation only as a bounded paired robustness diagnostic; or
2. Write and freeze one new task-design amendment that makes Relay necessity a
   pre-trigger invariant, explicitly separates exposure from estimand, and
   proves at the trigger that `Scout -> Attacker` is absent and the attacker
   information path includes Relay. Re-run transparent adequacy only after
   that amendment is independently reviewed.

No MARL training is justified before option 1 or 2 is frozen. The present
evidence is insufficient for a paper claim that relation-aware learning
improves robustness to Relay-mediated information degradation.

## Artifact index

- Audit script: `scripts/run_phase_s1a_mechanism_audit.py`
- Exposure classification: `results/development/phase_s1a_mechanism_audit/episode_exposure_audit.csv`
- Trigger audit: `results/development/phase_s1a_mechanism_audit/failure_trigger_audit.csv`
- Mechanism summary: `results/development/phase_s1a_mechanism_audit/exposed_mechanism_summary.csv`
- Paired timeline summary: `results/development/phase_s1a_mechanism_audit/paired_timeline_summary.csv`
- Audit manifest: `results/development/phase_s1a_mechanism_audit/manifest.json`
