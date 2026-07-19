# Hardened 60-Update Safety Diagnostic Summary

Date: 2026-07-19

## Purpose

This diagnostic checks whether a light proximity safety penalty can reduce the collision issue found in the hardened 60-update development run without destroying the relay-failure recovery signal.

The safety term is a training auxiliary only. It is not a claimed algorithmic innovation.

## Protocol

- Scenario: `dropout030_relay_failure`
- Environment switches:
  - `strict_target_sensing=True`
  - `agent_target_info_bottleneck=True`
  - `max_target_message_age_steps=80`
  - `min_target_confidence=0.2`
- Methods: `no_graph`, `single`, `multi_relation`
- Training seeds: `0, 1, 2`
- Continuation budget: `60` PPO updates
- Validation: `30` matched episodes per seed
- Test: `50` disjoint matched episodes per seed
- Validation checkpoint selection: zero validation collision required
- Safety training auxiliary:
  - `safety_proximity_distance=1000`
  - `safety_proximity_penalty_weight=0.3`
- Output directory: `results/intercept_3d_gate1_hardened_60update_safety_diag/`

## Test Summary

| Method | Recovery | Success | Timeout | Collision | Tracking During Failure | Connectivity During Failure |
|---|---:|---:|---:|---:|---:|---:|
| `no_graph` | `0.280 +/- 0.451` | `0.280 +/- 0.451` | `0.707 +/- 0.439` | `0.013 +/- 0.023` | `0.166 +/- 0.260` | `0.095 +/- 0.088` |
| `single` | `0.533 +/- 0.382` | `0.533 +/- 0.382` | `0.460 +/- 0.370` | `0.007 +/- 0.012` | `0.607 +/- 0.317` | `0.171 +/- 0.065` |
| `multi_relation` | `0.867 +/- 0.099` | `0.867 +/- 0.099` | `0.133 +/- 0.099` | `0.000 +/- 0.000` | `0.878 +/- 0.091` | `0.216 +/- 0.014` |

Seed-level selected test recovery:

- `no_graph`: `0.04`, `0.80`, `0.00`
- `single`: `0.82`, `0.10`, `0.68`
- `multi_relation`: `0.80`, `0.82`, `0.98`

## Minimum-Distance Audit

After adding minimum-distance fields to the evaluator, the selected safety-diagnostic checkpoints were re-evaluated without retraining under:

- `results/intercept_3d_gate1_hardened_60update_safety_diag_min_distance_eval/`

Mean over training seeds:

| Method | Episode Min Blue-Red Distance | Episode Min Blue-Blue Distance |
|---|---:|---:|
| `no_graph` | `3341.0 +/- 157.1 m` | `1543.7 +/- 666.0 m` |
| `single` | `2275.0 +/- 1038.6 m` | `2346.3 +/- 1431.8 m` |
| `multi_relation` | `3290.2 +/- 126.2 m` | `2334.4 +/- 1189.6 m` |

Seed-level distance notes:

- `single` seed `1` is the main safety concern: blue-red minimum distance mean is `1088.9 m`, blue-blue minimum distance mean is `981.1 m`, and test collision is `0.02`.
- `no_graph` seed `2` still has test collision `0.04`, despite its mean blue-red distance remaining large; this suggests unsafe episodes are rare but severe and the policy mostly fails through timeout and poor task-chain recovery.
- `multi_relation` has zero test collision across all three seeds while preserving the highest recovery rate.

## Seed-Aware Bootstrap

Hierarchical bootstrap treats training seed as the primary unit, then resamples matched evaluation episodes within each seed.

`multi_relation - no_graph`:

- Recovery delta: `+58.7 pp`, 95% CI `[+7.3, +97.4] pp`
- Timeout delta: `-57.3 pp`, 95% CI `[-93.3, -7.3] pp`
- Restricted mean recovery-step delta: `-124.13` steps, 95% CI `[-204.82, -14.91]`
- Tracking-during-failure delta: `+71.3 pp`, 95% CI `[+40.8, +97.5] pp`
- Connectivity-during-failure delta: `+12.1 pp`, 95% CI `[+1.5, +19.0] pp`

`multi_relation - single`:

- Recovery delta: `+33.3 pp`, 95% CI `[-0.7, +68.7] pp`
- Timeout delta: `-32.7 pp`, 95% CI `[-66.7, +0.7] pp`
- Restricted mean recovery-step delta: `-70.11` steps, 95% CI `[-143.11, +1.53]`
- Tracking-during-failure delta: `+27.1 pp`, 95% CI `[-2.2, +56.4] pp`
- Connectivity-during-failure delta: `+4.4 pp`, 95% CI `[-0.7, +9.9] pp`

## Interpretation

The safety auxiliary is useful but not sufficient as a final formal protocol by itself.

Positive:

- `multi_relation` keeps strong recovery after adding the safety penalty.
- `multi_relation` reaches zero test collision across all three training seeds.
- The method remains clearly separated from `no_graph` under seed-aware statistics.
- Failure-period tracking and connectivity remain much higher for `multi_relation`, which supports the mechanism claim.

Remaining risk:

- `single` still has one weak seed and one collision case.
- `no_graph` still has one collision seed and very high variance.
- `multi_relation - single` remains a strong mean advantage, but the three-seed CI still touches zero. This should not be promoted as final significance evidence without either five seeds or a stronger frozen safety-selection rule.
- The current validation gate constrains validation collision only; final testing can still produce collisions for baselines. A paper-facing protocol should report test collision and minimum-distance metrics directly.

## Decision

Use this safety auxiliary as the default candidate for the next hardened development line, but do not launch a final five-seed formal rerun until the evaluation reports minimum-distance distributions and the protocol explicitly defines how unsafe checkpoints are selected and reported.

Recommended next implementation step:

1. Decide whether to freeze `safety_proximity_distance=1000`, `safety_proximity_penalty_weight=0.3` for the next five-seed hardened formal rerun.
2. If uncertain, run a small safety-weight sweep before the formal rerun.
3. Preserve minimum-distance metrics in all future formal summaries.
