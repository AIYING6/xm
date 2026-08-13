# Phase R2-A Final Decision Report

**Status:** CLOSED — `R2A-A1 INFEASIBLE`  
**Training:** NO-GO  
**Phase 3A:** NO-GO  
**Role-Gate:** UNRESOLVED

## Summary

R2-A separated the remaining problem into controller adequacy and failure
dependency. The earlier A1 replay showed that a legal recovery route is
physically reachable and that episodes with an actual strict loss recovered
in the observed sample. R2A-A1 then added a frozen formation controller and a
strict pre-fault guard to test the intended primary dependency.

The R2A-A1 replay produced zero eligible episodes in all six controller×seed
cells. Timestep inspection explains why: the formation rule moved Scout and
Attacker into an early direct-communication geometry, so the strict guard
correctly rejected the trigger. The guard did not miss a valid failure; the
controller made the pre-fault alternative path active.

## Gate status

| Gate | Status | Evidence |
| --- | --- | --- |
| Geometry feasibility | PASS | Initial direct link absent; optimistic closing-time margin positive. |
| Recovery after actual loss | PASS in observed A1 sample | Every recorded lost episode recovered through a legal post-fault route. |
| Stable pre-failure primary chain | FAIL | Legal controller had very low eligibility in the prior A1 replay. |
| Relay criticality at trigger | FAIL under R2A-A1 | Formation controller caused early Scout–Attacker direct connectivity; strict guard therefore produced 0 eligible episodes. |
| Full R2 adequacy | NO-GO | Frozen cell thresholds were not met. |

## Scientific conclusion

The redesigned task has a real recovery mechanism, but the current
transparent-controller protocol does not produce a stable window in which:

```text
Scout -> Relay -> Attacker is active
AND Scout -> Attacker is inactive
AND Attacker is outside terminal sensing range
```

The problem is now sharply localized to task-window/controller design. It is
not evidence against MAPPO, EA-RG-MAPPO, or Role-Gate. No MARL training result
can be scientifically interpreted until this window is stable.

## Final decision

- Do not start development or formal MARL training.
- Do not alter endpoint, TTL, communication radius, failure timing, or seed
  set to force a pass.
- Keep all R1/R2 raw artifacts as archival development evidence.
- If continuing, write a new R2B protocol from an explicit operational
  geometry that maintains relay necessity without pulling Scout and Attacker
  into direct range before failure.
- If that operational geometry cannot be justified independently of the
  desired result, terminate the relay-recovery claim and use the project for a
  bounded task-validity/graph-robustness study.
