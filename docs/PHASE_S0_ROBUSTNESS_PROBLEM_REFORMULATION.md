# Phase S0: Heterogeneous Communication–Task Graph Robustness

**Status:** FROZEN PROBLEM REFORMULATION  
**Protocol ID:** `PHASE-S0-CTGR-V1`  
**Training:** not authorized by S0

## 1. Closed claim and new question

The strict relay-recovery headline is permanently closed as unsupported. The
project no longer claims that EA-RG-MAPPO or Role-Gate restores a strict
pre-failure-to-post-failure recovery endpoint.

The new research question is:

> Under heterogeneous UAV sensing and communication constraints, how does a
> critical relay failure degrade the perception–communication–task-support
> graph, and can relation-aware graph policies limit mission-performance
> degradation without violating local information boundaries?

The paper’s bounded argument is:

```text
relay failure -> relation/topology degradation -> information staleness and
task-performance loss; relation-aware graph modeling may reduce that loss.
```

The phrase “may reduce” remains provisional until new development evidence is
collected. Existing recovery/oracle results cannot support a learned-method
claim.

## 2. Conditions and paired design

Every method and seed is evaluated on the same paired episode tape under:

1. **Nominal:** no relay fault, with the fixed sensing, communication,
   dynamics, reward, and horizon protocol.
2. **Relay-failure:** the same initial state and exogenous realization, with
   the pre-registered relay node failure process.

The failure condition must not be adapted to a method outcome. The primary
comparison is within method/seed nominal versus relay-failure degradation,
followed by between-method comparison of degradation.

## 3. Primary metrics

Strict recovery event and recovery duration are not primary metrics. Primary
metrics are:

### Mission degradation

For a metric where higher is better:

```text
D_J = (J_nominal - J_failure) / max(|J_nominal|, epsilon)
```

The paper must report the underlying nominal and failure values, not only the
ratio. For collision/safety metrics where lower is better, direction must be
reported explicitly rather than silently applying the same formula.

### Legal target-information availability

```text
A_info = T^{-1} sum_t 1[attacker has fresh legal target information at t]
```

This is computed from delivered cache/direct sensing provenance, never from
ground-truth target state.

### Information staleness

For timesteps with a valid or previously valid target track:

```text
Age_t = t - t_last_valid_posted_update
```

Report mean, median, upper quantiles, and the fraction beyond the frozen TTL.

### Task-chain availability

```text
A_chain = T^{-1} sum_t 1[the legal task-support chain is active at t]
```

This is a time-occupancy metric, not a claim that the chain must recover.

### Robustness ratio

```text
R_rob = J_failure / J_nominal
```

Use only for metrics whose direction and denominator are meaningful; always
show the paired raw values and confidence intervals.

### Safety and termination

Report collision, constraint violation, timeout, target escape, and mission
success separately. A method may not claim robustness by preserving
communication at the expense of safety.

## 4. Secondary mechanism evidence

The three graph relations remain:

- Perception: who legally senses target information;
- Communication: which delivered message links are active;
- Task-support: which legal information path currently supports the task.

Secondary telemetry includes relation occupancy before/after failure, direct
and relay-routed cache provenance, message age, dropout/delay exposure, graph
connectivity, and information-boundary invariance.

The R2B operating map and strict recovery artifacts are retained as bounded
mechanism and limitation evidence. They are not primary performance results.

## 5. Method scope

The first development comparison is limited to:

1. MAPPO no-graph baseline;
2. Multi-Relation Full;
3. parameter-matched Single-Graph.

Role-Gate is excluded from the core claim and remains `UNRESOLVED`. A later
small ablation may test it only after the three-method robustness smoke passes;
it cannot block the mainline and cannot be selected from favorable outcomes.

## 6. Statistical and provenance boundary

The primary analysis is paired nominal-versus-failure degradation with
seed-level aggregation and hierarchical bootstrap over episodes nested within
seed/scenario. KM/RMST survival analysis is downgraded from primary and is not
required for the new headline. All raw episode records, checkpoints, hashes,
configs, tapes, and derived-statistics provenance remain mandatory.

## 7. Phase sequence

```text
S0 problem freeze -> S1 transparent robustness validation
-> S2 environment/metric freeze -> S3 three-method learnability smoke
-> S4 architecture decision -> S5 canonical readiness -> Phase 3A
```

S1 must show measurable nominal-to-failure degradation and valid information
boundaries before any MARL training. S0 does not authorize formal training.
