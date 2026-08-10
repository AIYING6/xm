# N2 Failure Localization Report

## Status

`N2_FAILURE_LOCALIZATION_COMPLETE__NO_METHOD_DESIGN_AUTHORIZED`

This is a development-only, read-only diagnosis. It is not formal evidence and
must not be used as a performance comparison in the paper.

## Protocol

The four existing vanilla-MAPPO checkpoints (two original N2 and two
potential-shaping repair checkpoints) were evaluated on the same 48 fixed
episode seeds (`730000`--`730047`) under three modes:

1. `baseline`: the checkpoint controls flight and `engage_commit`;
2. `auto_commit`: the checkpoint controls flight, while the evaluator commits
   whenever true physical neutralization geometry is legal;
3. `oracle_motion_policy_commit`: a scripted motion controller controls flight,
   while the checkpoint controls only `engage_commit`.

For every episode we recorded geometry entry, maximum continuous geometry dwell,
commit alignment, and terminal outcome. No reward, environment, architecture,
action semantics, or training budget was changed.

## Results

| checkpoint | mode | geometry-entry rate | mean max dwell | neutralization rate | escape rate |
|---|---|---:|---:|---:|---:|
| N2 seed 7201 | baseline | 0/48 | 0.0 | 0/48 | 48/48 |
| N2 seed 7201 | auto commit | 0/48 | 0.0 | 0/48 | 48/48 |
| N2 seed 7201 | oracle motion + policy commit | 48/48 | 18.3 | 45/48 (93.75%) | 3/48 |
| N2 seed 7202 | baseline | 0/48 | 0.0 | 0/48 | 48/48 |
| N2 seed 7202 | auto commit | 0/48 | 0.0 | 0/48 | 48/48 |
| N2 seed 7202 | oracle motion + policy commit | 48/48 | 18.3 | 45/48 (93.75%) | 3/48 |
| repair seed 7201 | baseline | 0/48 | 0.0 | 0/48 | 48/48 |
| repair seed 7201 | auto commit | 0/48 | 0.0 | 0/48 | 48/48 |
| repair seed 7201 | oracle motion + policy commit | 48/48 | 18.3 | 45/48 (93.75%) | 3/48 |
| repair seed 7202 | baseline | 0/48 | 0.0 | 0/48 | 48/48 |
| repair seed 7202 | auto commit | 0/48 | 0.0 | 0/48 | 48/48 |
| repair seed 7202 | oracle motion + policy commit | 48/48 | 60.4 | 0/48 | 48/48 |

The repair seed 7202 checkpoint is a diagnostic outlier: it produced no
commit actions in the oracle-motion mode, despite entering geometry in all
episodes. It is retained rather than removed.

## Localization decision

The evidence localizes the dominant failure to the learned flight/control
interface: both the learned baseline and evaluator auto-commit fail before
geometry entry. The oracle-motion intervention demonstrates that, for three of
four checkpoints, the commit/terminal transition can be exercised successfully
when motion is supplied by a scripted controller. Thus the result is not
consistent with an unreachable mission or a universally unlearnable commit
action.

The joint task remains unlearned because the policy must discover and maintain
the physical engagement geometry while synchronizing a four-step commit. This
diagnostic does not identify whether the remaining cause is exploration,
low-level control, or temporal credit assignment; those require a separately
authorized task-interface experiment.

## Gate

`N2_FAILURE_LOCALIZATION_PASS__TASK_CONTROL_BOTTLENECK_IDENTIFIED`

No architecture, reward, action space, horizon, or protocol change is
authorized by this report. The next decision must be an explicit author
authorization for at most one task-interface repair; do not start N3 or new
method design automatically.

Raw records and manifest:

- `results/new_project_n2_failure_localization/localization_records.csv`
- `results/new_project_n2_failure_localization/localization_summary.csv`
- `results/new_project_n2_failure_localization/LOCALIZATION_MANIFEST.json`
