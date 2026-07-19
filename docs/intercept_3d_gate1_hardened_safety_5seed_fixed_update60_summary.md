# Hardened Safety Five-Seed Fixed-Update-60 Summary

Last updated: 2026-07-19

## Status

This is a fixed-budget diagnostic for the safety-enabled hardened Gate-1 line, not yet a validation-selected formal paper result.

The full validation checkpoint sweep for the five-seed safety candidate became too expensive and repeatedly stalled. To avoid blocking the project, all completed five-seed training runs were evaluated at the common checkpoint `actor_critic_update_0060.pt`.

This protocol is acceptable as a development-to-formal candidate only if it is frozen before further tuning and reported as a fixed-training-budget selection rule.

## Protocol

- Result root: `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/checkpoint_sweep_fixed_update60_test/`
- Scenario: `dropout030_relay_failure`
- Split: `test`
- Training seeds: `0, 1, 2, 3, 4`
- Episodes: `100` matched test episodes per seed and method
- Methods: `no_graph`, `single`, `multi_relation`
- Checkpoint: update `60` for every method and seed
- Evaluation batching: `--eval-batch-size 50`
- Total test episodes: `1500`
- Environment hardening:
  - strict target sensing;
  - target-information bottleneck;
  - TTL/confidence target-cache validity;
  - post-step failure/message timing;
  - hidden stale graph target state;
  - light proximity safety auxiliary.

## Main Test Results

Values are seed-level mean plus sample standard deviation across five training seeds.

| Method | Recovery / success | Tracking during failure | Connectivity during failure | Chain closed during failure | Timeout | Collision | Min blue-red distance | Min blue-blue distance |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `no_graph` | 0.218 +/- 0.419 | 0.148 +/- 0.276 | 0.078 +/- 0.079 | 0.037 +/- 0.070 | 0.774 +/- 0.413 | 0.008 +/- 0.008 | 3669.95 m | 1176.05 m |
| `single` | 0.532 +/- 0.381 | 0.475 +/- 0.254 | 0.146 +/- 0.060 | 0.076 +/- 0.055 | 0.440 +/- 0.361 | 0.028 +/- 0.029 | 2472.81 m | 1225.76 m |
| `multi_relation` | 0.886 +/- 0.137 | 0.776 +/- 0.168 | 0.203 +/- 0.018 | 0.138 +/- 0.029 | 0.114 +/- 0.137 | 0.000 +/- 0.000 | 3276.94 m | 2011.36 m |

Seed-level recovery values:

- `no_graph`: `[0.00, 0.96, 0.00, 0.00, 0.13]`
- `single`: `[0.82, 0.27, 0.00, 0.69, 0.88]`
- `multi_relation`: `[0.65, 0.90, 0.99, 0.92, 0.97]`

`multi_relation` is the only method with zero test collisions in this fixed-update evaluation.

## Seed-Aware Statistics

Hierarchical bootstrap first resamples training seeds and then matched episodes inside each seed.

`multi_relation` versus `single`:

- Recovery / success delta: `+0.354`, 95% CI `[+0.012, +0.730]`
- Timeout delta: `-0.326`, 95% CI `[-0.676, 0.000]`
- Restricted mean recovery steps delta: `-64.536`, 95% CI `[-144.381, +7.231]`
- Tracking during failure delta: `+0.301`, 95% CI `[+0.011, +0.615]`
- Connectivity during failure delta: `+0.057`, 95% CI `[+0.000, +0.115]`
- Chain closure during failure delta: `+0.061`, 95% CI `[-0.001, +0.125]`

`multi_relation` versus `no_graph`:

- Recovery / success delta: `+0.668`, 95% CI `[+0.286, +0.938]`
- Timeout delta: `-0.660`, 95% CI `[-0.924, -0.284]`
- Restricted mean recovery steps delta: `-135.796`, 95% CI `[-190.853, -57.135]`
- Tracking during failure delta: `+0.628`, 95% CI `[+0.425, +0.842]`
- Connectivity during failure delta: `+0.124`, 95% CI `[+0.058, +0.168]`
- Chain closure during failure delta: `+0.101`, 95% CI `[+0.038, +0.148]`

## Interpretation

The fixed-update-60 result gives a much stronger safety-enabled hardened evidence line than the earlier three-seed diagnostic:

- It preserves the expected ordering `no_graph < single < multi_relation`.
- It separates `multi_relation` from `single` on recovery/success with a positive seed-aware confidence interval.
- It strongly separates `multi_relation` from `no_graph` across recovery, timeout, restricted recovery time, tracking, connectivity, and chain closure.
- It removes the previous `multi_relation` collision concern under this fixed-update test.

The recovery-time claim should still be written carefully. `multi_relation` improves restricted mean recovery steps versus `no_graph`, but the `multi_relation - single` interval still crosses zero because seed `3` has slow recovered episodes.

## Current Decision

Recommended next step:

Freeze the fixed-update-60 safety-enabled protocol as the practical formal route unless a short validation-selection sweep can be made reliable without changing the training/evaluation budget.

The paper-facing claim should emphasize:

> Multi-relation role graphs improve post-failure kill-chain recovery probability and communication-feasible tracking under strict intermittent sensing, while maintaining zero collision in the fixed-budget safety-enabled evaluation.

Do not overclaim:

- universal faster recovery than `single`;
- superiority under all maneuvering-target settings;
- Q1-level completeness before mechanism figures, ablations, and stronger scenario tests are added.

## Artifacts

- Merged checkpoint summary: `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/checkpoint_sweep_fixed_update60_test/merged/test_checkpoint_summary.csv`
- Merged episode metrics: `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/checkpoint_sweep_fixed_update60_test/merged/test_episode_metrics.csv`
- Fixed checkpoint selection table: `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/checkpoint_sweep_fixed_update60_test/merged/fixed_update60_selected_checkpoints.csv`
- `multi_relation` vs `single` bootstrap: `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/checkpoint_sweep_fixed_update60_test/merged_seed_aware_stats/multi_vs_single/intercept_3d_strict_sensing_seed_aware_bootstrap.csv`
- `multi_relation` vs `no_graph` bootstrap: `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/checkpoint_sweep_fixed_update60_test/merged_seed_aware_stats/multi_vs_no_graph/intercept_3d_strict_sensing_seed_aware_bootstrap.csv`
- Failure-aligned mechanism summary: `docs/gate1_safety_fx60_mechanism/failure_aligned_mechanism_summary.md`
- Failure-aligned mechanism curves: `results/gate1_safety_fx60_mechanism/failure_aligned_mechanism_curves.png`
- Representative case timeline: `results/gate1_safety_fx60_mechanism/representative_case_timeline.png`

## Follow-Up Work

1. Add the most important hardened ablations under the frozen safety protocol:
   - `no_task_support`;
   - `no_role_pair_gate`;
   - optionally `no_curriculum`.
2. Decide whether to continue validation-selected checkpoint selection or formally adopt fixed update `60` as the frozen training-budget rule.
3. If the fixed-update route is adopted, improve the plot styling and captions for paper use.
