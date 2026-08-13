# Phase S2 Primary Estimand Freeze

Primary outcome: paired mission-performance degradation under Relay-node
failure.

```text
Delta_J = J_nominal - J_failure
```

`J` is the sum of per-step multi-agent mission reward over the realized episode
horizon, with terminal handling unchanged from the frozen environment. The
primary aggregation is over all planned paired episodes, including episodes
that terminate before the scheduled failure. Exposure rate and pre-failure
terminal counts are reported separately. Mechanism analyses are explicitly
conditional on exposed episodes.

The normalized quantity is not primary in S2. It may be reported only as a
secondary standardized display using the frozen positive nominal cell mean:

```text
D_J = Delta_J / max(J_nominal_cell_mean, epsilon)
```

No denominator may be selected after algorithm results. Later inference uses
seed-level paired summaries and hierarchical bootstrap over seeds and paired
evaluation tapes.

Robustness ratio is not used as a primary estimand because per-episode and
cell-level denominators are not guaranteed to be safely away from zero across
future methods. If displayed descriptively, it is `R_J = J_failure / J_nominal`
only after positivity checks, never as the basis of the main decision.
