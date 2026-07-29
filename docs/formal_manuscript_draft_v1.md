# Formal Manuscript Draft v1

Date: 2026-07-29

This draft follows `docs/FINAL_Q1_SINGLE_PAPER_PLAN.md`,
`docs/formal_protocol_freeze.md`, and
`docs/gate_prior_dev100_three_seed_decision.md`. It is a writing draft, not a
final result report. Numerical claims that require the formal budget study,
five-seed validation, or final held-out test are left as placeholders.

## Writing Status

Paper type: algorithmic research paper.

Target level: Q1 attempt with Q2 fallback.

Current writing boundary:

- The problem definition, method, environment, training protocol, baseline set,
  metric definitions, and statistical plan can be drafted now.
- Final abstract numbers, main result claims, ablation conclusions, and final
  discussion must wait for validation-selected formal results and the once-only
  held-out test.

## One-Sentence Argument

In heterogeneous UAV kill-chain recovery under strict intermittent sensing,
message loss, message delay, and relay-node failure, we test whether an
edge-aware multi-relation role graph can improve post-failure recovery by
separating perception, communication, and task-support relations during
centralized-training decentralized-execution policy learning.

## Terminology Ledger

| Canonical term | First-use definition | Notes |
|---|---|---|
| EA-RG-MAPPO | Edge-Aware Multi-Relation Role-Graph MAPPO | Main paper method name. |
| EA-RG-MAPPO-S | EA-RG-MAPPO with the frozen paper training protocol | Use only when the implementation/protocol name is needed. |
| role-gate prior | Initialization bias with `role_gate_prior_strength=0.4` | Training protocol detail, not a primary contribution. |
| kill-chain recovery | Restoring the detection-information-attack chain after relay failure | Primary task concept. |
| perception relation | Directed relation induced by direct target sensing | One graph channel. |
| communication relation | Directed relation induced by delivered messages | One graph channel. |
| task-support relation | Dynamic relation indicating role-dependent support for recovery | One graph channel. |
| role-pair-conditioned message passing | Message mapping conditioned on sender and receiver roles | Core method component. |
| strict target sensing | Target information is available only by sensing or valid received messages | Actor information-boundary condition. |
| target-information bottleneck | Actor cannot use unavailable target state shortcuts | Scientific-validity condition. |
| HAPPO | Heterogeneous-agent PPO baseline | Describe as standard only if the implemented correction is verified. |
| final held-out test | Test split run once after all protocol decisions are frozen | Not yet run at this writing stage. |

## Title Options

Recommended:

**Multi-Relation Role-Graph Reinforcement Learning for Heterogeneous UAV
Kill-Chain Recovery under Limited Communication**

Alternative 1:

**Edge-Aware Role-Graph MAPPO for Relay-Failure Recovery in Heterogeneous UAV
Teams**

Alternative 2:

**Communication-Feasible Multi-Agent Reinforcement Learning for Heterogeneous
UAV Kill-Chain Recovery**

Avoid:

- "full air combat"
- "complete 6DOF system"
- "guaranteed kill-chain closure"
- "human-UAV collaborative combat system"

These phrases exceed the current evidence boundary.

## Abstract Draft

Heterogeneous unmanned aerial vehicle (UAV) teams often depend on a sequence of
sensing, information transfer, and attack-window formation to complete
cooperative interception tasks. This sequence can break when target sensing is
intermittent, communication links are lossy or delayed, and a relay platform
loses its communication function. Existing multi-agent reinforcement learning
methods usually represent inter-agent relations with either no explicit graph
or a single homogeneous graph, which can obscure whether an edge corresponds to
direct perception, delivered communication, or task support. This paper proposes
EA-RG-MAPPO, an edge-aware multi-relation role-graph MAPPO method for
communication-feasible heterogeneous UAV kill-chain recovery. The method builds
separate perception, communication, and task-support relations and applies
role-pair-conditioned message passing under centralized training and
decentralized execution. We evaluate the method in a constrained 3DOF 3v1 UAV
interception task with strict target sensing, actor target-information
bottlenecks, packet dropout, message delay, and relay-node failure. Under the
frozen formal protocol, EA-RG-MAPPO is compared with MAPPO/no-graph,
Single-Graph MAPPO, HAPPO, and a parameter-matched single-graph baseline using
matched validation and held-out test episodes. [Insert final result sentence:
method, metric, baseline, confidence interval.] Mechanism analyses further
examine whether recovery is associated with target tracking, communication
connectivity, message age, and task-support routing after relay failure. The
results provide a bounded step toward resilient heterogeneous UAV cooperative
decision making under limited communication, while leaving full 6DOF combat,
online missile engagement, and human-UAV teaming for future validation.

## Keywords

Heterogeneous UAVs; multi-agent reinforcement learning; MAPPO; graph neural
networks; limited communication; intermittent sensing; kill-chain recovery;
resilient multi-agent systems

## 1. Introduction

Cooperative UAV interception is increasingly shaped by networked sensing,
information transfer, and engagement rather than by the behavior of a single
platform. In a heterogeneous team, one vehicle may detect a target, another may
relay target information, and a third may form the final attack window. The
mission therefore depends on a kill chain that links detection, information
delivery, and engagement geometry. When the sensing or communication layer is
damaged, the team can fail even if individual UAVs remain flyable and
physically close to the target.

This problem is especially difficult under strict local information. A scout
may have a wider field of view but limited attack capability. A relay may be
important for message delivery but vulnerable as a functional communication
node. An attacker may be able to close the engagement geometry only when it
receives fresh target information through a feasible sensing-communication
path. As a result, the meaning of an inter-agent relation is not fixed. A
scout-to-attacker relation may indicate target-information support, a
relay-to-attacker relation may indicate message delivery, and an
attacker-to-relay relation may express the need to preserve the information
path that supports the shooter.

Centralized-training decentralized-execution multi-agent reinforcement learning
provides a practical framework for this setting because it allows the critic to
use global training information while requiring each actor to operate from its
available local inputs. MAPPO and graph-based MAPPO variants are strong
starting points for cooperative control problems [CITE: MAPPO; CITE:
graph-MARL]. However, a no-graph actor has no explicit topology model, and a
single-graph actor can mix perception reachability, physical message delivery,
and task-support semantics into one edge type. Under relay failure, this
collapse can make it difficult to learn how the team should reconstruct the
kill chain through alternative information routes.

We study this issue in a communication-feasible 3DOF 3v1 heterogeneous UAV
interception environment. The task keeps the experiment small enough for
multi-seed controlled comparisons while retaining the main decision constraints
that matter for the paper claim: strict intermittent target sensing, actor-side
target-information bottlenecks, packet dropout, message delay, target-message
TTL and confidence, and relay-node communication failure. The environment is
not presented as a full 6DOF air-combat simulator. Instead, it is a controlled
testbed for asking whether relation-aware information routing improves
post-failure kill-chain recovery.

This paper proposes EA-RG-MAPPO, an edge-aware multi-relation role-graph MAPPO
method. The policy separates perception, communication, and task-support
relations and performs role-pair-conditioned message passing for heterogeneous
sender-receiver pairs. The paper makes three contributions:

1. We define a communication-feasible heterogeneous UAV kill-chain recovery
   task under strict target sensing, message uncertainty, and relay-node
   failure.
2. We introduce a perception-communication-task-support multi-relation role
   graph that separates physical sensing, delivered communication, and dynamic
   task-support semantics.
3. We use role-pair-conditioned message passing to allow different
   sender-receiver role pairs to use different message transformations during
   recovery.

The main empirical question is not whether the proposed method is universally
best across all UAV tasks. It is whether this explicit relation structure
improves recovery reliability, safety, and interpretability under the frozen
strict-sensing relay-failure protocol.

## 2. Related Work

### 2.1 Multi-Agent Reinforcement Learning for UAV Cooperation

Multi-agent reinforcement learning has been used for cooperative pursuit,
formation control, target interception, and air-combat decision making. CTDE
methods such as MAPPO provide stable policy optimization by using centralized
state information during training while preserving decentralized execution
[CITE: MAPPO]. Heterogeneous-agent methods such as HAPPO further address the
fact that different agents may have different policies or action semantics
[CITE: HAPPO]. These methods are relevant baselines, but they do not by
themselves specify how task information should propagate through a damaged
sensing-communication network.

### 2.2 Graph-Based Multi-Agent Coordination

Graph neural networks and graph attention mechanisms are natural tools for
multi-agent coordination because they aggregate information across agents and
adapt to changing neighborhoods [CITE: GAT; CITE: graph-MARL]. In UAV tasks,
however, an edge has physical meaning. It can be created by target sensing,
message delivery, role support, or simple geometric proximity. A single
homogeneous graph may be sufficient for some coordination tasks, but it is a
coarse representation for kill-chain recovery because relation type and
sender-receiver role both affect how information should be used.

### 2.3 Limited Communication and Resilient Multi-Agent Systems

Limited communication, packet dropout, message delay, and node failure are
central to resilient multi-agent systems [CITE: resilient-MARL; CITE:
communication-MARL]. Prior work has studied learning when to communicate, how
to compress messages, or how to remain robust to topology changes. The present
paper focuses on a complementary question: when the team already has physically
constrained sensing and message delivery, can the policy representation
separate the relation types that determine whether the kill chain can be
recovered after a key relay function is lost?

### 2.4 UAV Kill-Chain and Cooperative Interception

UAV cooperative interception is often evaluated by pursuit success, distance
to target, or collision rate. These metrics are necessary but incomplete for
heterogeneous teams because they do not directly reveal whether target
information remains fresh, whether the attacker has a valid information path,
or whether the team can restore an attack window after relay failure. We
therefore evaluate recovery-oriented metrics, including post-loss kill-chain
recovery, delayed recovery, message age, target tracking, and communication
connectivity.

## 3. Problem Formulation

We model the task as a decentralized partially observable Markov decision
process with centralized training. The blue team contains three heterogeneous
UAVs: a scout, a relay, and an attacker. The red side contains one controlled
target. At each step, UAV \(i\) receives a local observation \(o_i^t\), a graph
observation \(G_i^t\), and selects a high-level 3DOF command \(a_i^t\). The
centralized critic may use the global state during training, but the actor must
not use unavailable target state, unreachable agent state, future messages, or
global attack-chain progress at execution time.

The kill chain is represented by four stages:

1. target detection by a valid sensing platform;
2. information delivery through feasible communication;
3. attacker access to fresh target information;
4. attack-window formation or reclosure after failure.

Relay failure interrupts the communication function of the relay platform for a
fixed duration. A successful recovery requires the remaining feasible sensing
and communication paths to restore the chain after the failure event.

## 4. Environment

The main environment is a lightweight 3DOF heterogeneous UAV interception
testbed. Each UAV state includes three-dimensional position, speed, heading,
and flight-path angle. Actions are high-level turn, climb, and speed commands.
The environment enforces bounded speed, turn, climb, altitude, and safety
constraints. The target follows the frozen straight policy in the formal
scenario suite.

The sensing and communication model includes:

- strict target sensing;
- actor target-information bottleneck;
- finite communication radius;
- packet dropout probability of 0.30;
- two-step message delay;
- message cache TTL and confidence;
- relay-node communication failure;
- predefined early, standard, delayed, and late failure-timing scenarios.

The environment returns recovery metrics through evaluation logs. Primary
paper metrics are kill-chain recovery rate and restricted mean recovery time.
Secondary metrics include delayed recovery, timeout rate, tracking rate after
failure, attacker fresh-cache ratio, chain-closed probability, communication
connectivity, message age, collision rate, and flight-envelope violations.

## 5. Method: EA-RG-MAPPO

### 5.1 Overview

EA-RG-MAPPO extends MAPPO with a multi-relation role graph for the actor and a
centralized critic for training. The actor receives local observations and
information that is available through physically feasible sensing and
communication. The critic receives centralized state information for value
estimation only.

The graph encoder contains three relation channels:

1. perception relation;
2. communication relation;
3. task-support relation.

These channels are encoded separately and then fused for action selection.
This design allows the policy to distinguish whether a neighbor is relevant
because it sensed the target, delivered a valid message, or supports the
current kill-chain stage.

### 5.2 Multi-Relation Graph Construction

At each time step, the environment builds a role graph over the blue UAVs and
target-related information nodes. A perception edge is active when a platform
directly senses the target. A communication edge is active only when a message
is physically deliverable after dropout, delay, and node-failure constraints.
A task-support edge is active when the current role pair is relevant to
detection, information delivery, or attack-window recovery.

The actor-side graph excludes global attack-chain progress and unavailable
target state. This separation is required for a valid decentralized execution
claim.

### 5.3 Role-Pair-Conditioned Message Passing

For each relation channel, messages are conditioned on sender and receiver
roles. This allows Scout-to-Relay, Scout-to-Attacker, Relay-to-Attacker, and
peer-support messages to use different transformations. The role-pair
conditioning is intended to reduce the burden on a single homogeneous attention
function that would otherwise need to infer all relation semantics from node
features alone.

The frozen implementation uses a role-gate prior with strength 0.4. This prior
is treated as a training initialization detail that encourages non-neutral
role-pair routing early in training. It is not claimed as the main algorithmic
contribution.

### 5.4 Training Objective

The policy is optimized with a conservative MAPPO-style objective. The formal
protocol uses fixed actor and critic learning rates, clipped PPO updates,
entropy regularization, gradient clipping, and critic-only warm-up. Behavior
cloning from a geometric offset teacher is used as a common initialization for
methods that support it. The same BC family, number of demonstrations, epochs,
teacher policy, reward settings, and safety settings are applied across the
formal methods.

## 6. Experimental Protocol

### 6.1 Methods

The formal comparison includes:

1. MAPPO/no-graph;
2. Single-Graph MAPPO;
3. HAPPO;
4. EA-RG-MAPPO with the frozen role-gate prior;
5. Parameter-Matched Single Graph, if completed before final paper lock;
6. Rule/geometric controller as a feasibility reference.

Original EA-RG-MAPPO without the prior can be reported as an internal
development ablation, not as a required external baseline.

### 6.2 Scenario Suite

All validation and final testing use the frozen four-scenario suite:

- `dropout030_delay2_relay_failure_early`;
- `dropout030_delay2_relay_failure`;
- `dropout030_delay2_relay_failure_delayed`;
- `dropout030_delay2_relay_failure_late`.

No new difficulty, target policy, dropout, delay, or failure timing is used to
select the final method.

### 6.3 Budget Study and Checkpoint Selection

The common budget study first evaluates 1M environment transitions for the four
main methods over development seeds. If validation curves are still rising or
seed failures remain common, all methods are extended to 2M. The final common
budget \(B^*\) is shared across methods.

Each method and training seed selects one checkpoint using the validation split
only. The selection score is suite-level delayed recovery with a minimum
success step of 80. Final held-out testing is run once after the method,
budget, checkpoint rule, reward, safety, BC, and scenario settings are frozen.

### 6.4 Statistical Analysis

Main comparisons use seed-aware hierarchical bootstrap. The resampling first
samples training seeds and then samples matched episodes within each seed. We
report method means, seed-level spread, mean differences, and 95% confidence
intervals. Episode-level samples from the same trained policy are not treated
as fully independent model samples.

## 7. Results Plan

This section will be filled only after the formal study is complete.

### 7.1 Overall Comparison

Claim to test:

EA-RG-MAPPO improves suite-level kill-chain recovery or delayed recovery
relative to no-graph and single-graph baselines under the frozen strict-sensing
relay-failure protocol.

Required evidence:

- selected checkpoint per method and seed;
- final held-out test mean and confidence interval;
- seed-level scatter;
- collision and timeout rates.

### 7.2 Relay-Failure Recovery

Claim to test:

The proposed multi-relation role graph improves the probability or speed of
post-failure kill-chain recovery.

Required evidence:

- recovery rate;
- delayed recovery;
- restricted mean recovery time;
- failure-aligned recovery curves.

### 7.3 Mechanism Analysis

Claim to test:

If EA-RG-MAPPO improves recovery, the improvement should be accompanied by more
stable target tracking, fresher attacker target information, better
communication connectivity, or more interpretable task-support routing after
failure.

Required evidence:

- tracking rate after failure;
- attacker fresh-cache ratio;
- chain-closed probability;
- message age;
- relation attention or gate diagnostics;
- predefined representative case.

### 7.4 Ablation Studies

Required ablations:

- w/o Role-Pair Gate;
- w/o Task-Support Relation;
- w/o Explicit Role Identity;
- Parameter-Matched Single Graph.

The ablations must be retrained under the final protocol. Test-time module
shutdown can be used as a diagnostic only, not as formal ablation evidence.

### 7.5 Scenario-Depth Supplements

After the main 3v1 evidence is complete, controlled supplements may be added:

- mild maneuvering target;
- small 4v2 or 5v2 rule-red extension;
- limited LAG/JSBSim replay or feasibility validation.

These supplements support realism and scope. They do not replace the main
formal 3v1 statistical evidence.

## 8. Discussion Draft

If the formal results confirm the development trend, the main interpretation
will be that relation semantics matter for recovery-oriented heterogeneous UAV
coordination. A no-graph actor may learn useful team behavior, and a
single-graph actor may exploit topology information, but neither explicitly
separates sensing reachability, delivered communication, and dynamic
task-support structure. The expected advantage of EA-RG-MAPPO is therefore not
unconditional peak performance. The bounded claim is improved recovery
reliability or recovery interpretability when communication is damaged and the
relay function is unavailable.

The paper must also discuss rival explanations. If the role-gate prior,
behavior cloning, or reward shaping explains most of the advantage, then the
method claim must be narrowed. If Single-Graph MAPPO matches or exceeds
EA-RG-MAPPO on the final held-out test, the paper should emphasize the value of
explicit graph coordination and report multi-relation routing as a partial or
diagnostic result rather than as a dominant mechanism. If HAPPO performs
competitively, the discussion should separate heterogeneity-aware policy
updates from graph-based information routing.

The current study has clear boundaries. The main environment is 3DOF and 3v1,
not full 6DOF air combat. The target policy is controlled in the frozen main
suite. Missile dynamics, radar signal processing, human-UAV teaming, and
large-scale red-blue self-play are outside the main statistical claim. These
limitations are intentional: they allow the study to isolate whether
communication-feasible multi-relation role graphs improve kill-chain recovery
before adding high-fidelity combat subsystems.

## 9. Conclusion Draft

This paper studies heterogeneous UAV kill-chain recovery under strict target
sensing, limited communication, message uncertainty, and relay-node failure. We
define a communication-feasible 3DOF recovery task and propose EA-RG-MAPPO, a
multi-relation role-graph MAPPO method that separates perception,
communication, and task-support relations and uses role-pair-conditioned
message passing. The final conclusion will be completed after the formal
held-out test. It must report the confirmed recovery, safety, and mechanism
evidence without extending the claim to full 6DOF air combat or universal UAV
coordination.

## Claim-Evidence Map

| Claim | Required evidence | Current status |
|---|---|---|
| The task is communication-feasible and actor-local. | P0 information-boundary tests; observation schema; protocol docs. | Partly supported by project docs; cite exact tests in Methods. |
| EA-RG-MAPPO improves recovery over no-graph MAPPO. | Final held-out test, five seeds, hierarchical bootstrap. | Needs formal results. |
| EA-RG-MAPPO improves over Single-Graph MAPPO. | Final held-out test and parameter-matched baseline. | Needs formal results; do not overclaim. |
| Role-pair routing contributes to recovery. | Retrained w/o Role-Pair Gate ablation plus mechanism diagnostics. | Needs formal ablation. |
| Task-support relation contributes to recovery. | Retrained w/o Task-Support Relation ablation. | Needs formal ablation. |
| The method is robust to scenario timing. | Four-scenario suite results. | Needs formal validation/test. |
| The method transfers to high-fidelity flight simulation. | LAG/JSBSim replay or feasibility validation. | Future supplement only. |

## Immediate Writing To-Do

1. Replace citation placeholders with verified references.
2. Add notation for Dec-POMDP, relation graphs, message passing, and PPO loss.
3. Convert the environment and method sections into LaTeX after formulas are
   finalized.
4. Fill Results only from validation-selected formal runs.
5. Run a consistency audit between this draft, `formal_protocol_freeze.md`, and
   final result tables before PDF generation.
