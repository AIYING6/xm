# Dropout-Relay Strict-Sensing Protocol

Last updated: 2026-07-17

## Purpose

The straight relay-failure setting separates graph policies from `no_graph`, but `single` remains close to `multi_relation`.

Checkpoint-only probes identified `communication_dropout_prob=0.30 + relay_failure + strict_target_sensing` as the best next scenario candidate:

- `multi_relation`: `98.3%` recovery;
- `single`: `76.7%` recovery;
- `no_graph`: `28.3%` recovery;
- seed-aware `multi_relation - single`: `+21.7 pp`, 95% CI `[+3.3, +41.7] pp`.

This is not final paper evidence because the checkpoints were selected on the easier straight relay-failure validation split.

## Scenario Definition

Scenario name:

`dropout030_relay_failure`

Environment settings:

- `strict_target_sensing=True`;
- `communication_dropout_prob=0.30`;
- `failed_blue_agent=1`;
- `node_failure_start_step=40`;
- `node_failure_duration_steps=80`;
- `target_policy=straight`.

The scenario is implemented in `scripts/evaluate_3d_topology_robustness.py` and is available to:

- `scripts/evaluate_3d_checkpoint_sweep.py`;
- `scripts/run_3d_strict_sensing_formal_protocol.py`.

## Development Protocol

Use the existing 30-update training outputs first:

`results/intercept_3d_strict_sensing_fair_30update_diag/runs/`

Run validation checkpoint selection with:

- methods: `no_graph`, `single`, `multi_relation`;
- seeds: `0, 1, 2`;
- scenario: `dropout030_relay_failure`;
- validation episodes: at least `20` per training seed;
- fixed validation base seed;
- no test tuning.

Then run disjoint test with:

- selected checkpoints from dropout-relay validation;
- test episodes: at least `20` per training seed for development, preferably `50+` for formal reporting;
- different base seed from validation.

## Decision Rule

Promote to five-seed formal training only if:

- `multi_relation` keeps recovery above roughly `80%`;
- `single` remains meaningfully below `multi_relation`;
- `no_graph` remains clearly weaker;
- seed-aware `multi_relation - single` recovery delta remains mostly positive;
- failure cases are not dominated by collisions or flight-envelope violations.

If the difference disappears after validation is moved to dropout-relay, do not force the claim. Report straight relay-failure as graph-structure necessity evidence and redesign the task-support bottleneck.

## Verification

The new scenario enum was compiled and smoke-tested with a one-episode checkpoint sweep:

`results/intercept_3d_strict_sensing_dropout030_relay_scenario_smoke/`

## First Development Result

A first 30-update development diagnostic has been completed:

`results/intercept_3d_strict_sensing_fair_30update_dropout030_formal_diag/`

This run used dropout-relay validation checkpoint selection and disjoint dropout-relay test episodes.

Test recovery:

- `multi_relation`: `93.3%`;
- `single`: `86.7%`;
- `no_graph`: `31.7%`.

Seed-aware recovery deltas:

- `multi_relation - single`: `+6.7 pp`, 95% CI `[-15.0, +33.3] pp`;
- `multi_relation - no_graph`: `+61.7 pp`, 95% CI `[+0.0, +100.0] pp`.

Decision:

This is not strong enough for five-seed formal reporting of the multi-relation-over-single claim. Use it to justify either a longer 60-120 update dropout-relay diagnostic or a task-support bottleneck redesign.

## 60-Update Diagnostic

A 60-update diagnostic was completed for `single` and `multi_relation`:

`results/intercept_3d_strict_sensing_fair_60update_dropout030_diag/`

Test recovery:

- `multi_relation`: `96.7%`;
- `single`: `88.3%`.

Seed-aware recovery delta:

- `multi_relation - single`: `+8.3 pp`, 95% CI `[-1.7, +21.7] pp`.

Decision:

The longer run improves the average but remains non-separated. The next step should be a task-support bottleneck redesign or a controlled information-dependency scenario before a five-seed formal run.
