# Q1 Execution Plan

Last updated: 2026-07-18

## Target

The project target is now a Q1-level submission attempt, while keeping a Q2-level fallback path.

Core paper claim:

> Communication-feasible temporal multi-relation policy learning improves heterogeneous UAV mission-chain resilience under intermittent sensing, packet loss, delay, jamming, and key communication-function failure.

The current 3v1 bottleneck dropout-relay result is not discarded. It becomes the mechanism and protocol foundation. Q1-level evidence requires additional realism, stronger baselines, a more complex 5v2 scenario family, OOD tests, and 6DOF replay.

## Non-Negotiable Principle

Do not expand the scenario before fixing information realism.

The actor must not receive target information through any path that would be unavailable during decentralized execution. Task-support edges can only gate already delivered communication messages; they cannot act as an independent information channel.

## Gate 1: Information Realism

Goal:

Make the existing 3DOF environment and graph interface communication-feasible.

Required work:

- audit actor observations, graph node features, edge features, relation adjacencies, and intent context;
- ensure the decentralized actor only uses local observations and delivered messages;
- keep centralized critic access to global state only for CTDE training;
- enforce `A[receiver, sender] = 1` as the project-wide graph direction convention;
- ensure task-support relations cannot bypass physical communication;
- implement or verify a real message-delay queue rather than using delay only as a scalar feature;
- distinguish communication-subsystem failure from whole-aircraft failure in code, metrics, and manuscript wording.

Required tests:

- information isolation: if no delivered communication path exists, changing the target state must not change a disconnected attacker's actor input/action distribution;
- edge direction: a sender-to-receiver edge must update only the receiver;
- task edge no bypass: task-support relation without physical message delivery must not transmit target information;
- one-hop-per-step causality for multi-hop communication;
- packet dropout and communication failure behavior;
- decentralized actor input test;
- regression smoke for the current frozen 3v1 protocol.

Exit criteria:

- all communication-feasibility tests pass;
- existing 2D evidence chain remains untouched;
- current frozen 3v1 protocol still runs;
- documentation states exactly what the actor and critic can observe.

## Gate 2: 3v1 Mechanism Paper Core

Goal:

Turn the current 3v1 bottleneck dropout-relay protocol into a rigorous mechanism study.

Use:

- `dropout030_relay_failure`;
- `strict_target_sensing=True`;
- `agent_target_info_bottleneck=True`;
- fixed validation split for checkpoint selection;
- validation-time collision rejection for safety-critical checkpoint selection;
- disjoint matched test split;
- seed-aware hierarchical bootstrap.

Methods:

- rule-based recovery;
- `no_graph`;
- `single`;
- parameter-matched GAT if feasible;
- heterogeneous graph baseline if feasible;
- proposed multi-relation method.

Minimum formal scale:

- 5 independent training seeds;
- at least 50 validation episodes per seed;
- preferably 100 test episodes per seed;
- matched episodes across methods.
- validation checkpoints with nonzero collision rate should be rejected for the main formal table unless a separate development note justifies a softer threshold.

Decision rule:

- if proposed method does not clearly beat `single` or parameter-matched GAT, do not enter 5v2 formal training;
- first inspect whether the failure is due to information leakage, unfair baseline budgets, insufficient task-support dependency, or over-saturation.

Output:

- main 3v1 mechanism table;
- relation/message/curriculum ablations;
- seed-aware statistics;
- recovery timeline and message-path case;
- parameter count and inference-time table.

## Gate 3: Q1 Method Hardening

Goal:

Make the method defensible against strong graph baselines.

Allowed changes:

- communication-feasible ego graph;
- temporal message memory;
- role-pair and task-support gates;
- message freshness and confidence weighting.

Not allowed:

- adding unrelated fourth or fifth innovation modules;
- self-play/ELO as a main contribution;
- online missile loop as a main contribution;
- generic dynamic task allocation.

Baseline requirements:

- all learning methods use the same local observations and communication channel;
- all methods use the same BC generation rule if BC is used;
- training interaction budget and checkpoint selection rule must match;
- parameter differences must be reported; if the proposed model is much larger, add a parameter-matched GAT baseline.

## Gate 4: 5v2 Main Scenario Family

Goal:

Add a scenario with real recovery decisions, not just a larger fixed formation.

Blue team:

- scout UAV;
- primary relay UAV;
- backup multifunction UAV;
- two executor UAVs.

Red team:

- maneuvering target;
- rule-based jammer/defender.

The red side remains rule-based. Do not add end-to-end red-blue self-play for this paper.

Required decision pressure:

- backup node may need to replace relay function;
- an executor may need to temporarily forward information;
- the team may need to avoid a jammer region;
- communication path choice must trade off target approach speed, message freshness, and link reliability;
- there must be multiple valid recovery routes.

Development scale:

- start with 3 development seeds;
- freeze reward, scenario distributions, and protocol before formal testing;
- do not use test results to tune.

Exit criteria:

- proposed method beats the strongest non-oracle baseline on recovery rate and restricted recovery time;
- success rates are not saturated for all graph methods;
- absolute success is not too low to interpret.

## Gate 5: Formal Q1 Experiments

Goal:

Build the full evidence chain.

Recommended scale:

- 5 seeds minimum for 3v1 mechanism experiments;
- 6 to 8 seeds for 5v2 main experiments if runtime permits;
- 100 matched test episodes per seed for core conditions;
- 150+ matched episodes per OOD condition if affordable.

Formal tests:

- normal communication;
- relay communication failure;
- 30% dropout plus relay failure;
- delay plus relay failure;
- jammer plus relay failure;
- OOD dropout/delay;
- longer or permanent relay communication failure;
- scout sensing interruption followed by relay failure;
- stronger jammer and target maneuver;
- 4v2 node-removal test;
- 6v2 node-addition test.

Statistics:

- training seed is the independent unit;
- report seed means and paired deltas;
- use hierarchical bootstrap;
- handle unrecovered episodes with restricted mean recovery time;
- apply Holm correction for multiple key comparisons.

## Gate 6: 6DOF Replay Validation

Goal:

Verify aviation plausibility without retraining every baseline in JSBSim.

Procedure:

- train policies in 3DOF;
- map high-level actions to heading, climb, and speed references;
- use low-level control in LAG/JSBSim;
- replay proposed method and strongest baseline on matched cases;
- check whether method ranking reverses.

Report:

- task success drop;
- recovery-rate change;
- recovery-time change;
- turn-rate, speed, altitude, and overload violations;
- inference time;
- qualitative trajectory and topology replay.

This is validation evidence, not a new training environment for all baselines.

## Fallback Strategy

If Gate 4 or Gate 5 fails:

- submit the rigorous 3v1 communication-feasible mechanism study as a Q2-oriented paper;
- keep 5v2 and 6DOF as the next paper's extension.

If 5v2 works:

- position the paper as a Q1 attempt with a Q2 fallback journal list.

## Immediate Next Task

Start Gate 1.

Concrete next implementation task:

> Add communication-feasibility audit tests for the current 3DOF actor graph: information isolation, task-support no-bypass, and edge-direction convention.

Do not launch five-seed formal training until Gate 1 passes.
