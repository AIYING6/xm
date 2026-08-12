# Phase 2IB: Relay-Dependent Cooperative Interception Task Protocol

**Status:** FROZEN DESIGN — P0 implementation and semantic tests only  
**Protocol ID:** `PHASE2IB-RDT-V1`  
**Scope:** a new development-only task family; it does not amend, replace, or
reinterpret any historical or canonical result.

## 1. Decision and scientific boundary

Phase 2IA9 showed that the prior task cannot support a relay-recovery claim:
at every audited trigger and failure-active timestep, the attacker retained a
direct sensing route.  This protocol therefore creates a *new*, explicitly
defined relay-dependent mission.  It is not a post-hoc alteration of the
historical endpoint, seed set, fault schedule, or reported result.

The one-sentence scientific argument is: in an emission-constrained
scout--relay--attacker interception mission, a relay-aware policy may provide
more resilient coordination after a causally relevant relay-channel loss; this
claim is testable only after the information-flow and failure semantics below
have passed pre-result feasibility gates.

Terminology locked for this task:

| Canonical term | Definition |
| --- | --- |
| relay-dependent task | The `RELAY_DEPENDENT_TASK_V1` environment configuration specified here. |
| target-information path | Ordered node IDs attached to a fresh target cache. |
| relay-required attacker information | A fresh attacker cache whose path includes relay ID 1. |
| dependency eligibility | A pre-failure state with attack geometry, scout detection, and relay-required attacker information. |
| relay-channel loss | Loss of valid attacker target information caused while relay 1 is failed. |

## 2. Operational task rationale

The blue team represents a heterogeneous mission in which a reconnaissance
platform carries the active target sensor, a relay platform carries the
long-range data link, and a strike platform is emission-constrained during the
terminal approach.  The attacker can act on target state received through the
approved data path, but it is not given an independent target-radar modality.
This is a task assumption, not a claim that every physical UAV has this
capability allocation.

The task’s causal communication route is therefore:

```text
scout (ID 0, target sensor) -> relay (ID 1, data-link relay) -> attacker (ID 2, terminal action)
```

## 3. Frozen information and failure semantics

`RELAY_DEPENDENT_TASK_V1` shall be implemented as a no-op-by-default
configuration mode.  When enabled, all of the following must hold:

1. The scout may produce a direct target detection subject to its existing
   geometry, radar-dropout, and target-sensing rules.
2. The attacker is denied direct target detection irrespective of whether the
   geometric radar predicate would otherwise be true.  This does not change
   ground-truth flight dynamics or the environment-defined attack geometry.
3. An attacker cache is considered usable only when it is fresh and its
   recorded target-information path contains relay ID 1.  A direct
   scout-to-attacker cache, or an attacker-local cache, is not target
   information under this task.
4. During an active failure of relay ID 1, an attacker cache requiring relay 1
   is unavailable.  The channel is treated as a live targeting service, not as
   a stored fire-and-forget packet.  Once relay 1 recovers, information must
   be rebuilt by ordinary sensing and message delivery; no synthetic recovery
   signal is injected.
5. Communication range, dropout, delay, dynamics, rewards, success logic,
   termination logic, and the pre-existing `chain_closed` endpoint remain
   unchanged in P0.  This protocol does not convert success into recovery.

The intended primary diagnostic state is:

```text
dependency_eligible_t = attack_window_t
                       AND scout_detected_t
                       AND attacker_has_relay_required_fresh_information_t
```

The later recovery endpoint, if feasibility passes, must require a loss of
this state after the frozen relay fault and a post-loss re-establishment.  Its
full statistical protocol is deliberately deferred; P0 creates no headline
metric and no new training result.

## 4. Configuration freeze for P0

P0 uses only the following new environment flag:

```text
relay_dependent_task = True
```

It is valid only with `strict_target_sensing=True` and
`agent_target_info_bottleneck=True`.  Enabling it with either prerequisite
disabled must raise an error.  Existing configurations default to
`relay_dependent_task=False` and must remain bit-for-bit behaviorally
unchanged at the environment-interface level.

## 5. Pre-result gates

No development learning, canonical evaluation, checkpoint selection, or
survival/RMST analysis may begin until all gates below pass and their raw
artifacts are committed or archived with hashes.

| Gate | Required evidence | Pass condition |
| --- | --- | --- |
| P0-A | legacy invariance test | Default configuration has unchanged observations, rewards, termination, and legacy telemetry for a deterministic replay. |
| P0-B | sensing-policy test | Attacker direct detection is impossible in relay-dependent mode; scout detection remains governed by the legacy sensor predicate. |
| P0-C | provenance-policy test | Attacker information is accepted only for a fresh path containing ID 1; a bypass path is rejected. |
| P0-D | fault-policy test | An active failure of ID 1 makes a relay-required attacker cache unavailable; recovery requires subsequent ordinary delivery. |
| P1 | transparent-controller feasibility probe | Before learning, demonstrate dependency eligibility and actual post-fault loss with raw timestep traces; no performance comparison. |

P1 scenario geometry, deterministic episode IDs, controller definitions,
fault trigger, episode count, and adequacy threshold must be recorded in a
separate launch protocol before execution.  It may not be selected after
inspecting learned-policy results.

## 6. Prohibited actions and provenance separation

- Do not reuse the historical `DIRECT_BYPASS` task as evidence for this new
  task, except as the motivation for creating it.
- Do not change the endpoint, fault timing, seed set, checkpoint policy, or
  task configuration after a development-learning result is visible.
- Do not use canonical seeds 0--4, canonical checkpoints, canonical test
  episodes, or historical headline tables in P0/P1.
- Do not start any training in Phase 2IB without a separately committed,
  pre-result training and evaluation protocol.

## 7. Immediate next action

Implement and test P0 only.  A P0 PASS establishes semantic correctness, not
task feasibility, method superiority, or readiness for Phase 3A.  Phase 3A
remains **NO-GO**.
