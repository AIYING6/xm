# Information Boundary Audit

Last updated: 2026-08-02

## Purpose

This document defines the information-boundary checks that must pass before any
new long-running experiment can be treated as formal paper evidence.

The goal is to prevent decentralized actors from receiving information that
would not be available under intermittent sensing and finite communication.

## Current Scope

Main environment:

```text
env_name = 3d_intercept
num_blue = 3
num_red = 1
strict_target_sensing = true
agent_target_info_bottleneck = true
relay_failure_agent = 1
```

Main learning setting:

```text
centralized critic may use global training state
decentralized actors must use only local observation and delivered graph messages
```

## Actor-Allowed Information

An actor may receive:

- own 3DOF state: position, speed, heading, flight-path angle, velocity;
- own role identity and platform capability fields;
- direct target detection flag and target-relative fields only when target
  information is locally valid;
- local attack-window indicator computed from actor-visible target information;
- local inbound communication connectivity;
- local inbound message age;
- local target-cache age and confidence;
- communication dropout and message-delay condition fields;
- graph node/edge features derived from direct sensing, delivered communication,
  role identity, message age, and task-support relations.

## Actor-Forbidden Information

An actor must not receive:

- true target state when it has neither direct sensing nor delivered target
  information;
- future target state, future communication success, or future node-failure
  status;
- global attack-chain progress as an actor graph feature;
- target information held only by another UAV unless communication delivered it;
- centralized critic fields during decentralized actor execution;
- final success, final reward, or termination reason before it is observable;
- test-split checkpoint-selection information during training or validation.

## Critic-Allowed Information

The centralized critic may use global training state under CTDE, including:

- full blue/red state;
- global communication and sensing condition;
- chain/attack-window progress;
- termination-relevant state.

This permission applies only during training. It does not justify actor-side
access to the same fields.

## Current Automated Checks

Run:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe -m pytest tests/test_gate1_communication_feasibility.py -q
```

Current coverage includes:

- actor observation schema matches exported `OBS3D_FIELD_NAMES`;
- role identity slice is explicit and correctly masked by no-role ablation;
- task-support relation requires delivered communication;
- task-support relation does not depend on hidden target state;
- local attack window requires actor-visible target information;
- actor graph does not include global attack-hold progress;
- actor logits are invariant to global attack-hold changes;
- attacker logits are invariant to unreachable target-cache changes.

Known latest result:

```text
24 passed
```

## Required Manual Audit Before Freeze

Before formal training, inspect and record:

- `envs/uav_intercept_3d_env.py`
  - `_get_obs`
  - `_get_share_obs`
  - `_get_graph_obs`
  - target-cache update logic
  - communication delivery and message-age update logic
  - node-failure masking logic
- `algorithms/ri_gmappo/simple_ri_gmappo.py`
  - actor inputs
  - critic inputs
  - graph ablation paths
  - role identity and edge-feature masking
- `scripts/evaluate_ri_gmappo_3d.py`
  - evaluation metrics must not feed back into actor decisions;
  - validation/test split and checkpoint selection must remain separate.

The manual audit must explicitly answer:

- Can attacker act on target state after radar dropout if no message was delivered?
- Can task-support edges appear without communication delivery?
- Can actor logits change when only critic/global-only state changes?
- Can validation checkpoint selection read test outcomes?
- Can failed relay state leak future recovery information?

## Freeze Pass Criteria

All conditions must be true:

- automated information-boundary tests pass;
- config audit passes;
- checkpoint-selection schema audit passes;
- manual audit finds no actor-side hidden-state dependency;
- any discovered leak marks all affected previous results as development-only;
- freeze tag is created only after the audit report is updated.

## Failure Rules

If an information leak is found after training starts:

- stop the run;
- mark affected checkpoints and outputs invalid for paper evidence;
- fix the leak;
- add or update an automated regression test;
- rerun smoke and freeze rehearsal;
- create a new freeze tag before formal training resumes.

