# Phase R0–R2 Relay-Dependent Task Redesign Protocol

**Status:** FROZEN DESIGN BEFORE IMPLEMENTATION  
**Protocol ID:** `PHASE-R0-R2-RDT-V1`  
**Purpose:** construct and verify a physically meaningful relay-dependent
interception task before any MARL training

## R0 — Requirement definition

The new task represents a reconnaissance–relay–strike mission:

```text
Target -> Scout sensing -> Relay track forwarding -> Attacker terminal action
```

The roles are operationally distinct:

- **Scout (ID 0):** long-range target sensing and track generation.
- **Relay (ID 1):** track forwarding and communication repositioning.
- **Attacker (ID 2):** local navigation and terminal action; it has no
  long-range full-track sensor.

The attacker’s direct target sensing is not globally deleted.  It is restricted
by a frozen terminal sensing envelope: direct target observation is allowed
only when the attacker is inside a separately configured terminal range and
the existing FOV predicate is satisfied.  Outside that envelope, the attacker
can use only legal delivered messages and its own state.

The primary pre-failure information path must therefore be:

```text
Scout -> Relay -> Attacker
```

The intended recovery path is a direct scout-to-attacker link formed after the
attacker repositions into the legal communication/sensing envelope:

```text
Relay failure -> information loss -> attacker repositioning -> Scout -> Attacker
```

No second relay is added in R0.  This keeps the causal mechanism interpretable
and avoids expanding the architecture before task feasibility is known.

## Frozen information policy

The implementation must expose the source and path of every target estimate.

1. Before failure, an attacker target estimate is primary-valid only if its
   fresh path contains relay ID 1.
2. During relay-1 failure, relay-dependent caches are invalid for the live
   task endpoint.
3. After failure, a direct scout-to-attacker message is valid only when the
   communication geometry permits it; it must carry path `[0, 2]` and a new
   delivery timestamp after the failure.
4. A stale pre-failure cache cannot count as recovery.
5. Direct attacker sensing, when inside the terminal envelope, is a secondary
   terminal mechanism and must be separately logged from communication-based
   recovery.

The environment must not expose hidden target truth through shared graph
features.  A legal-observation replay that changes target truth while holding
the actor’s delivered observations fixed must produce identical actor inputs.

## R1 — Transparent pre-failure feasibility

Use two non-learning controllers only:

- `structural_oracle`, for geometric reachability;
- `legal_observation`, using only returned per-agent observations.

Before any fault, each controller must repeatedly establish the primary
Scout–Relay–Attacker path.  The test must record direct sensing, cache path,
hop count, source ID, and delivery time at every timestep.

The pre-failure adequacy rule is at least 10 eligible episodes in every
controller×development-seed cell of 100 episodes.  Development seeds must be
new and fixed before execution; canonical seeds and checkpoints are forbidden.

## R2 — Failure and recovery feasibility

For every eligible episode, inject a fixed relay-1 failure at the pre-registered
trigger.  The controller must continue moving under the same fixed rule; no
manual repositioning may be inserted after observing failure outcomes.

The episode-level chain is:

```text
pre-established -> relay failure -> strict information loss
                 -> direct scout-attacker path or terminal sensing
                 -> recovered
```

R2 passes only when, in every controller×seed cell:

1. at least 80% of eligible episodes show strict information loss;
2. at least 50% of lost episodes show a post-loss valid alternative path;
3. every recovery record has a new post-failure delivery/sensing timestamp;
4. no recovery record uses a stale relay cache or hidden target truth.

The primary recovery endpoint remains strict and episode-level:

```text
pre_failure_chain_established
AND chain_lost_after_failure
AND post_failure_chain_recovered_after_loss
```

No success or collision flag may substitute for this endpoint.

## Four mandatory transparent tests

1. **Pre-failure feasibility:** the primary relay path is repeatedly formed.
2. **Failure dependency:** relay failure produces strict information loss.
3. **Recovery feasibility:** fixed transparent motion produces a legal
   alternative path after loss.
4. **Information-boundary legality:** target-truth perturbation with identical
   legal observations leaves actor inputs unchanged.

If any test fails, the task is not ready for learning.  The result is recorded
as a task-design failure and no threshold, endpoint, geometry, failure timing,
or seed set may be altered in response to the observed outcome.

## Prohibited actions

- No MARL training before R1/R2 pass.
- No Role-Gate selection or architecture comparison in R0–R2.
- No canonical seed, checkpoint, headline result, or survival analysis.
- No post-result changes to sensing envelope, communication geometry, fault
  timing, endpoint, seed set, or recovery definition.
- No use of the Phase2IB P1 `P1-INFEASIBLE` output as evidence against the
  redesigned task or against any algorithm.

Phase 3A remains **NO-GO** until R0–R2 are complete and separately audited.
