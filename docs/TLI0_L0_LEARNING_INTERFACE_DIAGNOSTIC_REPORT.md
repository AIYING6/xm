# TLI0 L0 Learning-Interface Diagnostic

## Status

`TLI0_COMPLETE__NO_INTERFACE_CHANGE_AUTHORIZED`

This is a read-only diagnostic of the frozen L0 checkpoint. No training,
reward change, task-physics change, or formal evaluation was performed.

## Findings

### 1. Trajectory/action divergence

On all eight aligned fixed seeds, the first action already differed at step 0.
The heuristic used guidance actions `{4, 6, 7, 8}`, whereas the PPO checkpoint
used only action `6` over the diagnostic trajectory. Initial physical states
were essentially identical (range differences below 1 m), so the divergence
is an action-selection failure rather than an initial-state mismatch.

The PPO policy therefore collapses to a single guidance command and never
approaches the simple state-dependent heuristic rule.

### 2. Observation representation

The 34 actor fields were finite and mostly normalized. Target-relative fields,
velocity fields, and heading sine/cosine values were present and varied on the
heuristic trajectory; no unavailable global or communication feature was
introduced. This audit found no immediate scale explosion or missing target
relative state sufficient to explain the failure by itself.

### 3. Action expressibility

The 9-command guidance interface can represent the heuristic trajectory: the
heuristic actually uses four of the nine commands. Thus the action set is not
missing the required control directions. The failure is that PPO does not
select the state-dependent sequence, not that the sequence is unrepresentable.

### 4. Reward/potential relationship

Along the successful heuristic trajectory, one-step range progress and the
physical mission potential change had correlation approximately `-0.56`. The
current L0 reward is range-progress based, while the potential combines range,
heading, altitude, closure, and geometry terms. This is evidence that the
available scalar learning signal is not uniformly aligned with the complete
neutralization geometry. It is a diagnostic warning, not authorization to
change reward.

### 5. Control timescale

Repeating a fixed command for 1, 2, 4, and 8 transitions produced approximately
linear displacement (207, 414, 828, and 1656 m) and no unexpected state
instability. This short deterministic check did not identify a discrete
timescale bug, although it does not prove that the PPO credit-assignment
timescale is optimal.

## Decision

The strongest current explanation is a degenerate PPO action policy combined
with a reward signal that does not consistently encode the multi-condition
geometry. Observation and action expressivity are not immediately invalid,
and the basic dynamics are stable. No single repair is authorized by TLI0;
the next step, if desired, must be separately authorized as exactly one of:
observation representation, action interface, reward design, or control
timescale. Do not combine them and do not enter L1/N3.

Raw diagnostic output:

- `results/tli0_l0_learning_interface_diagnostic_v2/TLI0_DIAGNOSTIC.json`
- `results/tli0_l0_learning_interface_diagnostic_v2/aligned_trajectories.csv`
