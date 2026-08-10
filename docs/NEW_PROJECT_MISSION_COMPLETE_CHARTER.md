# New project charter: heterogeneous-UAV mission completion under intermittent information

**Status:** `NEW_PROJECT_CHARTER_FROZEN__NO_ALGORITHM_OR_TRAINING_AUTHORIZED`.

## Separation from the completed line

This is a new project, not a repair, extension, or relabelling of v1.6/v1.8/v1.9.
Those versions may supply reusable engineering assets only: 3DOF vehicle
kinematics, recipient-specific information boundary tests, packet provenance,
complete-follow-up event records, and reproducibility tooling.  Their training
curves, checkpoints, numerical comparisons, and conclusions are not evidence
for this project.

## Task to establish before choosing an algorithm

Build a 3DOF heterogeneous UAV mission in which a scout, relay and interceptor
must operate under intermittent local sensing and delayed/lossy communication,
and in which the evaluator can observe an independent **mission-completion
transition**.  The target must become neutralized/captured only through a
specified physical interaction model; a graph predicate, cached message,
`chain_closed`, or engagement-readiness counter may not itself define success.

The future simulator specification must explicitly define:

1. the target state and evasive dynamics;
2. the interceptor's legal physical engagement action or interaction process;
3. the physical geometry, timing and safety conditions for a successful
   neutralization/capture transition;
4. terminal failures and their consequences; and
5. which quantities are visible to each actor versus the evaluator only.

## One-sentence paper argument (provisional)

> In a 3DOF heterogeneous-UAV mission with intermittent sensing and constrained
> communication, we will test whether a yet-to-be-selected decentralized
> coordination method improves independently defined mission completion under
> an execution-legal information contract, relative to equally informed strong
> comparators.

This is a task-level objective, **not** a claim that any network or mechanism
already works.

## Non-negotiable gates

| Gate | Required pass condition | Stop condition |
|---|---|---|
| N0: mission physics | Deterministic tests demonstrate both valid completion and valid non-completion using only physical/task state. | Completion is reconstructed from internal coordination or communication predicates. |
| N1: information legality | Every actor feature has recipient-specific execution provenance; evaluator-only state cannot affect an actor counterfactually. | Any privileged actor path remains. |
| N2: question selection | One mechanism has a literature-supported gap, a same-information/same-capacity strong comparator, and a falsifiable mechanism test. | Candidate is a renamed standard module or cannot be isolated. |
| N3: task feasibility | Method-blind development rollouts show a pre-specified, non-saturated mission-completion endpoint and meaningful intermittent-information states. | The endpoint is saturated/unobservable or the task is not feasible. |
| N4: engineering | D0/D1 artifact gates pass under one frozen protocol. | Repair engineering only; no performance interpretation. |
| N5: formal evidence | One fresh F1/F2 cycle supports the pre-frozen primary comparison and safety conditions. | End the algorithmic claim; no extra seeds, horizon changes, or rescue reruns. |

## Primary evidence hierarchy

The eventual primary endpoint must be an independently evaluator-defined
mission-completion incidence/time outcome with terminal outcomes represented
explicitly.  Task-chain establishment and physical-engagement readiness may be
reported only as secondary explanatory outcomes.  Every primary comparator must
receive identical legal raw information, matched capacity/training budget, and
the same frozen evaluation episodes.

## Bounded execution rule

No method name, architecture diagram, reward shaping, training script, cloud
instance, or formal experiment is authorized at charter stage.  First complete
N0 and N1 as simulator/information specifications, then run a targeted
literature-and-comparator decision for N2.  Only one candidate that passes
N0--N3 may receive a single formal F1/F2 cycle.  A failed N5 ends this new
project's algorithmic route rather than creating another version number.

## Terminology ledger

| Canonical term | Meaning | Explicit non-equivalent |
|---|---|---|
| mission completion | physical/task transition defined by the future simulator and evaluator | task-chain establishment; engagement readiness |
| target neutralization/capture | a future, physically specified terminal target state | being within an attack cone alone |
| actor information contract | recipient-specific data legally available at execution | critic shared state or simulator truth |
| evaluator | procedure allowed to read true task state for scoring only | policy input |

## Immediate next action

The N0 draft is recorded in
[NEW_PROJECT_N0_MISSION_PHYSICS_SPEC.md](NEW_PROJECT_N0_MISSION_PHYSICS_SPEC.md).
It proposes an abstract standoff-neutralization transition that uses an
attacker `engage_commit` action and evaluator-only true kinematics, while
explicitly excluding high-fidelity weapon claims.  Until that specification is
author-approved, no algorithm design or training begins.
