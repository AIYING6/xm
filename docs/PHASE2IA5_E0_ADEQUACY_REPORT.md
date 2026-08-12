# Phase 2IA5 E0 eligibility-triggered failure adequacy report

## Scope and boundary

This report evaluates only the development feasibility gate E0 defined in
`PHASE2IA5-ETF-V1`. It used six archived Phase 2IA4 fixed-final checkpoints,
not new training and not canonical seeds, tests, or results.

- arms: `full_gate`, `no_role_gate`;
- seeds: `101`, `202`, `303`;
- 100 deterministic paired episodes per arm × seed;
- total: 600 DEVELOPMENT_ONLY_E0 episodes;
- raw episode SHA256:
  `6a8ac4410771caf199c7ddd5584c1b293230074bb2f61c4ee2b0d5f1263cd51c`.

The E0 timing rule was frozen before execution: after four consecutive
`chain_closed` observations by step 220, fail relay agent 1 on the next step
for 80 steps. No episode reaching that condition is hidden or discarded.

## Evidence integrity

Six raw timestep trace files cover all 600 raw episode observations. The
independent reconstruction used `(arm, development_episode_id)` as the paired
observation key and found zero genuine trigger/endpoint/timing mismatches.

When no fault is injected, the historical endpoint API writes `-1` for some
failure-dependent fields; the trace auditor records this as *not applicable*,
not as a false endpoint mismatch. All true endpoint fields were consistent.

## E0 outcome

| Arm | Episodes | Eligible total | Seed 101 | Seed 202 | Seed 303 | Eligible with observed loss | E0 |
|---|---:|---:|---:|---:|---:|---:|---|
| full_gate | 300 | 0 | 0 | 0 | 0 | 0 | FAIL |
| no_role_gate | 300 | 0 | 0 | 0 | 0 | 0 | FAIL |

Both arms fail every pre-registered E0 adequacy condition: neither reaches the
minimum 40 eligible episodes, eligibility does not occur in two seeds, and no
eligible post-failure loss can be observed. This is not a recovery comparison,
not a success-rate comparison, and not evidence to retain or remove the
Role-Gate.

## Decision

**E0 ELIGIBILITY/OBSERVABILITY: FAIL**  
**ROLE-GATE RETENTION: UNRESOLVED**  
**ARCHITECTURE FREEZE: NO-GO**  
**PHASE 3A: NO-GO**

The prior Phase 2IA4 conclusion is strengthened: at this policy maturity and
under this development environment, the prerequisite chain is not a routinely
observable state. Merely moving the failure time cannot repair the evidence
gap.

## Recommended next action

Stop Role-Gate efficacy work under the present task formulation. Do not expand
seeds, weaken the endpoint, substitute operational closure/success, or launch
another larger training run solely to obtain a nonzero risk set.

Any future continuation requires a new, higher-level **task-feasibility design
protocol** that separately justifies and tests why an eligible pre-failure
chain should be reachable (including environment/task construction and a
non-performance feasibility criterion). Such a protocol would be a scientific
scope decision, not an automatic Phase 2IA5 follow-up, and must be approved
and committed before implementation. Until then, the scientifically correct
course is to retain this negative feasibility result and keep Phase 3A closed.
