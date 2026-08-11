# NP0B capability-overlap and responsibility-feasibility redesign

Status: `NP0B_PASS__OVERLAP_AND_RESPONSIBILITY_FEASIBILITY_ESTABLISHED__READY_FOR_NP1`

This was a no-training, no-algorithm task-concept calibration.  It does not
reuse NP1/NP1C performance as evidence and does not modify the legacy
environment.

## Frozen capability structure

The capability requirements are `S` (target sensing), `I` (information
maintenance/relay), `A` (approach), and `E` (terminal execution).

Pre-transition capabilities:

| role | S | I | A | E |
|---|---:|---:|---:|---:|
| Scout | 1 | 1 | 1 | 0 |
| Relay | 1 | 1 | 1 | 0 |
| Attacker | 0 | 1 | 1 | 1 |

The nominal assignment is `R0 = {S: Scout, I: Relay, A: Attacker, E:
Attacker}`.  After Scout sensing loss, Scout's `S` capability becomes zero.
Therefore `R0` is infeasible by the capability matrix itself.  The alternative
assignment `R1 = {S: Relay, I: Relay, A: Attacker, E: Attacker}` remains
feasible because Relay has overlapping sensing capability.

## Physical check

Using four pre-registered seeds (9121--9124), a transparent oracle controller
completed the nominal no-transition task in 4/4 episodes.  Under the same
physics with the Scout sensing transition, the alternative path also completed
4/4 episodes, and Relay produced local sensing after the transition in all
four runs.  No global failure flag or privileged target truth was used.

The old assignment's post-transition infeasibility is a capability-level fact;
it is not inferred from a deliberately weakened controller.  This is the
intended separation between task construct validation and later algorithmic
performance.

## Verdict and next gate

NP0B passes the required construct gate:

`pre-transition feasible -> old assignment infeasible -> alternative assignment feasible`

The next authorized step is a new NP1 protocol built on this capability-overlap
matrix, still no algorithm and no training.  CTRR is not yet authorized; a
vanilla-baseline learnability check follows only after the new NP1 protocol is
frozen and passes.

Artifacts:

* `results/np0b_capability_responsibility_feasibility/NP0B_FEASIBILITY_REPORT.json`
* `results/np0b_capability_responsibility_feasibility/NP0B_FEASIBILITY_MANIFEST.json`
* `scripts/run_np0b_capability_responsibility_feasibility.py`

