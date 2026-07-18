# Agent Target-Information Bottleneck Protocol

Last updated: 2026-07-17

## Motivation

The strict-sensing experiments showed a consistent gap between graph policies and `no_graph`, but `single` often remained close to `multi_relation`.

Inspection showed that, under strict sensing, all agents still received the same remembered target estimate in their local observations. This makes the task partly geometry-dominant and weakens the need for explicit task-support information flow.

## New Switch

`agent_target_info_bottleneck`

When enabled:

- strict sensing remains active;
- an agent that currently has target information uses the estimated target state;
- an agent without target information receives the target prior instead;
- default behavior is unchanged when the switch is disabled.

This is implemented as an opt-in environment/config flag and exposed through:

- `envs/uav_intercept_3d_env.py`;
- `algorithms/ri_gmappo/simple_ri_gmappo.py`;
- `scripts/train_ri_gmappo.py`;
- `scripts/evaluate_ri_gmappo_3d.py`;
- `scripts/evaluate_3d_checkpoint_sweep.py`;
- `scripts/run_3d_strict_sensing_formal_protocol.py`.

## Initial Probe

Probe:

`dropout030_relay_failure + strict_target_sensing + agent_target_info_bottleneck`

Checkpoints:

`results/intercept_3d_strict_sensing_fair_60update_dropout030_diag/`

Evaluation:

`results/intercept_3d_strict_sensing_fair_60update_dropout030_info_bottleneck_probe/`

Result:

- `multi_relation`: `95.0%` recovery;
- `single`: `78.3%` recovery;
- `multi_relation - single`: `+16.7 pp`, 95% CI `[+3.3, +33.3] pp`;
- restricted mean recovery time improved by `-35.02` steps, 95% CI `[-69.82, -6.68]`.

## Interpretation

This is the strongest current evidence that the multi-relation role graph helps beyond a single union graph.

It is still a checkpoint-only probe, not a final paper result, because checkpoints were selected without the bottleneck enabled.

## Next Step

Run validation checkpoint selection and disjoint test with the bottleneck enabled throughout:

- methods: `single`, `multi_relation`;
- scenario: `dropout030_relay_failure`;
- strict sensing: enabled;
- agent target-information bottleneck: enabled;
- validation/test base seeds: fixed and disjoint;
- report seed-aware statistics.

If the separated signal remains, promote this as the next formal scenario-depth experiment before moving to five seeds.

## Bottleneck-Enabled Validation/Test Result

This follow-up diagnostic has been completed:

`results/intercept_3d_strict_sensing_fair_60update_dropout030_bottleneck_formal_diag/`

Validation selection and test evaluation both used:

- `dropout030_relay_failure`;
- `strict_target_sensing`;
- `agent_target_info_bottleneck`;
- disjoint validation/test base seeds.

Test recovery:

- `multi_relation`: `95.0%`;
- `single`: `78.3%`.

Seed-aware recovery delta:

- `multi_relation - single`: `+16.7 pp`, 95% CI `[+6.7, +28.3] pp`.

Decision:

This is now the strongest formal scenario-depth candidate. Next, add `no_graph` under the same bottleneck-enabled validation/test protocol, then freeze the protocol before any five-seed expansion.

## Three-Method Development Result

`no_graph` has now been added under the same bottleneck-enabled protocol.

Test recovery:

- `multi_relation`: `95.0%`;
- `single`: `78.3%`;
- `no_graph`: `25.0%`.

Seed-aware recovery deltas:

- `multi_relation - single`: `+16.7 pp`, 95% CI `[+6.7, +28.3] pp`;
- `multi_relation - no_graph`: `+70.0 pp`, 95% CI `[+20.0, +100.0] pp`.

Decision:

Freeze this as the current formal scenario-depth protocol candidate. The next major experiment should be a five-seed expansion, after deciding whether the formal `no_graph` policy keeps weak-source variance or retrains all no-graph sources under a stronger predefined budget.
