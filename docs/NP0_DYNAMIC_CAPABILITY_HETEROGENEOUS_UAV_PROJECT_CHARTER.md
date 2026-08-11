# NP0 dynamic-capability heterogeneous UAV project charter

**Status:** `NP0_DYNAMIC_CAPABILITY_HETEROGENEOUS_UAV_PROJECT_CHARTER_AUTHORIZED__NO_ALGORITHM__NO_TRAINING`

## Scientific question

When an agent's physically available capability changes during an episode,
while the change is immediately known only to that agent, can a heterogeneous
team reallocate responsibility and continue a physical mission under strict
recipient-specific information?

The initial transition is deliberately limited to **Scout sensing-capability
loss**. Relay failure, actuator degradation, agent removal, and multiple
simultaneous transitions are out of scope for NP0.

## What is inherited and what is not

The project may reuse the 3DOF dynamics, heterogeneous roles, legal sensing
and delivered/cache-valid communication machinery, strict actor contract,
continuous guidance interface, physical neutralization evaluator, and
reproducibility infrastructure.

The existing L1--L4 and M0/M2R numbers are development history only. They are
not evidence for the new project. The new task must be implemented as a new
environment/configuration or adapter and must not rewrite the old evidence
chain.

## Capability semantics

Each agent has a capability vector with physical or functional consequences:

* sensing capability;
* forwarding capability;
* mobility/control capability;
* terminal-task capability.

NP0 activates only the sensing component. Before the transition, Scout has the
high-quality target sensing mode. At the frozen transition, that sensing mode
is actually disabled: the corresponding legal local observation is absent or
degraded according to the predeclared sensor model. Merely changing a label
does not count as a transition.

The affected Scout knows its own transition immediately through its local
observation. Other agents do not receive a global failure flag. They may learn
the change only through an actually delivered, cache-valid sender-status or
observation packet under the existing communication semantics. If the current
packet schema cannot carry a lawful self-reported capability status, NP1 must
stop and report that the task is not yet identifiable; no hidden global status
field may be added.

## Mission and action semantics

The new adapter retains continuous guidance actions. The obsolete binary
`engage_commit` action is removed from the learning action space. Once an
attacker is in the frozen physical neutralization envelope for four consecutive
valid transitions, neutralization occurs automatically. Collision and
constraint failure retain precedence over a same-step neutralization candidate.

This automatic terminal interaction is a task-interface change confined to the
new project; it does not alter v1.9 or the historical M0/M2R results.

## NP0 task protocol

The protocol must freeze, before any learning run:

1. the sensing model and exact Scout transition time/window;
2. the backup sensing capability and which role can lawfully provide it;
3. the capability-status provenance and cache-validity rules;
4. the episode horizon and physical neutralization timing window;
5. terminal-outcome precedence;
6. the scripted/oracle controller and random-controller definitions;
7. the baseline interfaces and evaluation seeds.

The initial task contains one Scout, one Relay, one Attacker/Executor, and one
target. The transition must occur before normal scripted completion and leave
enough time for a compensated team to finish.

## Pre-training kill conditions

NP0/NP1 is NO-GO if any of these holds:

* the transition changes only a label and not a legal observation, action,
  or physical effect;
* the task is not reliably completable without a transition;
* the post-transition task is naturally impossible even for a transparent
  scripted/oracle compensating controller;
* the original role allocation remains sufficient and no responsibility
  change is required;
* capability status reaches an actor through a global truth, evaluator flag,
  pending/dropped/expired payload, or privileged critic path;
* static capability conditioning or action masking already matches the
  compensating controller without any responsibility reorganization;
* failure outcomes are dominated by implementation errors rather than the
  intended capability transition.

## Baseline and future method boundary

NP0 does not implement the proposed method. If NP1 passes, the frozen future
comparison will be:

* B0: ordinary heterogeneous MAPPO;
* B1: capability-conditioned policy;
* B2: capability/action-mask robustness baseline;
* proposed: capability-transition-driven responsibility redistribution, with
  the same lawful capability information, masks, budget, and action space.

The proposed method must therefore show improvement beyond knowing that a
capability changed. Its mechanism endpoint will be responsibility transfer
after the transition, followed by physical neutralization—not a graph-closure
or communication proxy.

## Next gate

The only next authorized work is NP1 method-independent calibration:

* deterministic capability-transition semantics tests;
* nominal and post-transition scripted/oracle reachability;
* relay/status provenance audit;
* responsibility-change necessity counterfactual;
* static capability-conditioned/action-mask equivalence check.

No CTRR code, new network, training, cloud run, or formal performance claim is
authorized until NP1 passes.
