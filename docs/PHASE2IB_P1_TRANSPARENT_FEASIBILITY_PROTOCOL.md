# Phase 2IB P1 Transparent-Controller Feasibility Protocol

**Protocol ID:** `PHASE2IB-P1-TCF-V1`  
**Status:** FROZEN BEFORE EXECUTION  
**Purpose:** mechanism feasibility only; no learning and no performance claim

## 1. Question and boundary

P1 tests whether the new `RELAY_DEPENDENT_TASK_V1` task can expose a causal
relay-channel loss under fixed, transparent controllers. It does not test
EA-RG-MAPPO, Role-Gate, success rate, checkpoint quality, or recovery
superiority. It must not be combined with historical IA8/IA9 results.

The tested causal sequence is:

```text
relay-dependent eligibility -> relay 1 fault -> eligibility loss
                             -> relay recovery -> eligibility rebuild
```

## 2. Frozen design

Two controller arms are run independently:

| Arm | Information available to controller | Purpose |
| --- | --- | --- |
| `structural_oracle` | simulator structural state for deterministic pursuit actions | upper-bound reachability probe |
| `legal_observation` | only the per-agent observation returned by the environment | observation-feasibility probe |

Development seeds are fixed to `1101`, `1102`, and `1103`. They are not
canonical seeds.  Episode IDs are deterministic:

```text
211000 + 10000 * controller_index + 1000 * seed_index + episode_index
```

Each arm/seed combination runs exactly 100 episodes. Episodes are capped at
260 environment steps. The frozen task parameters are:

```text
relay_dependent_task=True
strict_target_sensing=True
agent_target_info_bottleneck=True
target_policy="straight"
communication_dropout_prob=0.30
message_delay_steps=2
radar_dropout_prob=0.0
```

When two consecutive `relay_dependency_eligible_t` observations are reached
at or before step 220, the next step begins a fixed relay-1 failure lasting 80
steps. No controller, episode, or checkpoint is selected using an outcome.

## 3. Episode-level definitions

- `dependency_eligible`: at least one pre-fault observation satisfies
  `relay_dependency_eligible_t=1`.
- `t_failure`: one step after the second consecutive eligible observation.
- `t_loss`: first failure-active timestep with
  `relay_dependency_eligible_t=0`, after eligibility before the fault.
- `t_recovery`: first post-loss timestep after the relay failure window in
  which `relay_dependency_eligible_t=1` again.
- `event`: `t_recovery` exists after a recorded `t_loss`.
- `censor_time`: terminal timestep if no event occurs, otherwise the fixed
  episode end/observation boundary used by the executor.

No success, collision, or `chain_closed` field is used as a substitute for
these definitions. Raw timestep telemetry is retained for every episode.

## 4. Pre-registered adequacy rule

P1 passes only if, for **each controller × seed cell**:

1. at least 10 of 100 episodes become dependency-eligible;
2. at least 80% of eligible episodes record a post-fault loss;
3. at least 50% of eligible-and-lost episodes record a post-loss rebuild.

If any cell fails, the result is `P1-INFEASIBLE` and no development training
may start. The failure is a task feasibility result, not evidence against the
algorithm. A protocol amendment would be required before any new probe.

## 5. Required artifacts and gates

The executor must produce an immutable manifest, raw episode metrics, one raw
timestep CSV per controller/seed cell, and a summary table. It must assert
that canonical seeds, checkpoints, training logs, and headline result files
were not read. P1 is a **PASS** only after all six cells have been checked
against the adequacy rule. Phase 3A remains **NO-GO** regardless of P1.

## 6. Claim boundary

Even a P1 PASS supports only the statement that the new relay-dependent task
has an observable causal information-loss/rebuild mechanism under the frozen
transparent probes. It does not support a method comparison or a paper
headline claim.
