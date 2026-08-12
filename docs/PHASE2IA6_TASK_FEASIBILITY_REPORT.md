# Phase 2IA6 task-feasibility report

## Scope

Phase 2IA6 tested whether the unchanged nominal 3DOF task can produce the
prerequisite sustained cooperative chain before a recovery experiment is even
meaningful. It used no learned policy, checkpoint, optimizer, training update,
canonical seed, canonical result, or recovery/survival analysis.

The suite comprised 600 deterministic DEVELOPMENT_ONLY episodes:

- controllers: `structural_oracle` and `legal_observation`;
- seeds: 601, 602, 603;
- 100 episodes per controller × seed;
- frozen environment: straight target, range scale 1.0, communication dropout
  0.30, delay 2, strict sensing and target-information bottleneck enabled;
- feasibility endpoint: four consecutive `chain_closed` observations by step
  220.

`structural_oracle` is explicitly a diagnostic controller using simulator
target truth only to test geometry/dynamics. `legal_observation` uses the
legal per-agent observation vector only; static audit confirmed that its
action-selection function has no simulator target-state access.

## Evidence integrity

All 600 raw records have a matching timestep trace across six trace files.
Independent trace reconstruction reproduced the feasibility endpoint for every
episode (0 mismatches). The Gate F outcome therefore does not depend on a
summary-only counter or learned-controller logging.

## Gate F result

| Controller | Episodes | Seed 601 | Seed 602 | Seed 603 | Four-step chain total | Gate F |
|---|---:|---:|---:|---:|---:|---|
| structural_oracle | 300 | 0 | 0 | 0 | 0 | FAIL |
| legal_observation | 300 | 0 | 0 | 0 | 0 | FAIL |

The required total of 40 endpoint episodes, two represented seeds, and two
seeds with at least 10 endpoint episodes all fail. The trace consistency
condition passes.

## Interpretation

**TASK-FEASIBILITY GATE F: INVALIDATED BY PHASE2IA7 TERMINAL-SEMANTICS AUDIT**  
**CURRENT NOMINAL TASK FORMULATION: UNRESOLVED (NOT CLOSED)**  
**ROLE-GATE RETENTION: UNRESOLVED**  
**ARCHITECTURE FREEZE: NO-GO**  
**PHASE 3A: NO-GO**

This Gate F result was later invalidated: `chain_closed` is terminal on its
first true timestep, so four consecutive `chain_closed` observations cannot
occur. The zero count must not be interpreted as evidence that the task lacks
a usable sustained-support population. See
`PHASE2IA7_TERMINAL_SEMANTICS_AUDIT.md`.

## Required stopping rule

Do not expand seeds, choose a more favorable controller, weaken the endpoint,
or launch a larger learning run. The only permitted continuation is the
separate Phase2IA7 semantic correction path.
