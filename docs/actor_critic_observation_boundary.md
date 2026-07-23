# Actor-Critic Observation Boundary

Last updated: 2026-07-19

## Purpose

This document defines the current CTDE boundary for the 3DOF mission-chain resilience experiments.

The paper must not imply that the decentralized actor can use information that is only available to the centralized critic.

## Decentralized Actor Inputs

The 3DOF actor receives:

- per-agent local observation `obs[i]`;
- graph node, edge, role, and adjacency tensors;
- relation adjacencies for perception, communication, and task support;
- delivered target-message cache information only through communication-feasible paths;
- no 3DOF target-intent context broadcast.

For the Q1 Gate 1 path:

- `use_intent_context=False` for 3DOF training, behavior cloning, and evaluation;
- task-support edges require delivered physical communication;
- target-message caches are updated only after delayed message delivery;
- multi-hop target information advances one hop per delay cycle;
- graph convention is `A[receiver, sender] = 1`.

## Actor Local Observation Fields

Current 3DOF local observation contains:

- own position, speed, heading, flight-path angle, velocity, and energy;
- target relative state from the agent-specific target estimate;
- own detection flag;
- own attack-window flag;
- own platform capability values;
- role indicators;
- aggregate communication connectivity and mean message age;
- time since last target detection;
- current attack-hold progress;
- configured communication dropout and delay scalars.

Under `strict_target_sensing=True` and `agent_target_info_bottleneck=True`:

- if the agent has no target-message cache and no valid target information, its target-relative state falls back to the target prior;
- if the agent has a delivered target-message cache, its target-relative state uses that cached estimate;
- a disconnected attacker should not change its action logits when only hidden target state changes.

## Graph Inputs

The graph still uses a global tensor representation for batching efficiency, but policy information flow is constrained by adjacency masks:

- perception relation: target node can send target information only to blue agents that detect the target;
- communication relation: sender information reaches a receiver only after physical communication delivery;
- task-support relation: role-compatible message gate, active only if physical message delivery exists;
- union graph residual uses active relation edges, not potential task-support edges.

Important limitation:

- this is not yet a fully separate per-agent ego-graph data structure;
- it is a communication-feasible masked graph implementation;
- final Q1 writing should describe it as communication-feasible masked actor graph unless a true ego-graph refactor is later implemented.

## Centralized Critic Inputs

The critic receives `share_obs`, which may include global state for CTDE training:

- all blue platform states;
- red/target state estimate or global state depending on strict-sensing mode;
- aggregate detection, attack-window, communication, message-age, dropout, delay, and time features.
- the controlled blue-agent role one-hot for the value being estimated.

The critic output is used only for training value estimation. It must not be used as an execution-time communication channel.

The role-conditioned critic is intentional because the environment uses role-specific rewards and heterogeneous platform responsibilities. Without an agent-role condition, the centralized value target can become ambiguous for agents that share the same global `share_obs` but optimize different role-dependent returns. This does not expand the decentralized actor's execution-time information.

## Current Tests

Maintained tests:

- `tests/test_gate1_communication_feasibility.py`

Current coverage:

- receiver-sender graph direction;
- task-support no-bypass;
- disconnected attacker action-logit invariance to hidden target changes;
- centralized critic role conditioning;
- delayed-message delivery timing;
- packet-dropout prevention;
- communication-subsystem failure delivery blocking;
- target-message path/hop-count and one-hop-per-delay-cycle propagation.

## Remaining Boundary Work

Before formal Q1/Q2 reruns:

- regenerate the frozen bottleneck dropout-relay diagnostic under the new communication-feasible semantics;
- add CSV fields for target-message cache metrics if used in paper figures;
- consider a true ego-graph wrapper if reviewers or final writing require a stricter implementation description.
