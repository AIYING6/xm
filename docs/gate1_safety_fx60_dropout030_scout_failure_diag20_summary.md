# Gate 1 Safety Fixed-Update-60 Dropout Scout-Failure Stressor Diagnostic

Last updated: 2026-07-22

## Purpose

This is a small graph-relation stressor diagnostic. It evaluates whether the frozen fixed-update-60 policies remain separated when the perception-support node is removed under additional communication dropout.

This is not a formal paper table:

- no new training was introduced;
- no checkpoint selection was changed;
- the frozen main test split was not reused or modified;
- the diagnostic uses 20 matched episodes per seed and method.

## Scenario

Scenario name: `dropout030_scout_failure`

Configuration:

- communication dropout: `0.30`
- failed blue node: scout, agent `0`
- node failure start: step `40`
- failure duration: `80`
- strict target sensing: enabled
- agent target-information bottleneck: enabled
- checkpoint: `actor_critic_update_0060.pt`
- training seeds: `0, 1, 2, 3, 4`
- diagnostic episodes: `20` per seed and method
- evaluation base seed: `351000`

## Result

| Method | Recovery | Seed recovery | Tracking during failure | Chain closed | Timeout | Collision |
|---|---:|---:|---:|---:|---:|---:|
| MAPPO / no graph | 24.0% +/- 41.1 | [0.0, 95.0, 0.0, 0.0, 25.0] | 15.1% | 4.0% | 76.0% | 0.0% |
| Single graph | 51.0% +/- 35.1 | [80.0, 30.0, 0.0, 65.0, 80.0] | 44.7% | 7.6% | 47.0% | 2.0% |
| Full multi-relation | 76.0% +/- 26.1 | [60.0, 80.0, 100.0, 40.0, 100.0] | 70.4% | 12.2% | 24.0% | 0.0% |

Mean recovery deltas:

- full minus single graph: `+25.0 pp`;
- full minus no graph: `+52.0 pp`.

## Seed-Aware Statistics

Hierarchical bootstrap with 3000 samples:

Full versus single graph:

- recovery delta: `+25.0 pp`, 95% CI `[-15.0, +66.0] pp`;
- tracking delta: `+25.6 pp`, 95% CI `[-5.2, +59.4] pp`;
- chain-closed delta: `+4.6 pp`, 95% CI `[-1.4, +11.1] pp`;
- timeout delta: `-23.0 pp`, 95% CI `[-63.0, +15.0] pp`.

Full versus no graph:

- recovery delta: `+52.0 pp`, 95% CI `[+15.0, +83.0] pp`;
- tracking delta: `+55.3 pp`, 95% CI `[+33.0, +79.7] pp`;
- chain-closed delta: `+8.2 pp`, 95% CI `[+1.8, +13.5] pp`;
- timeout delta: `-52.0 pp`, 95% CI `[-83.0, -15.0] pp`.

## Interpretation

This stressor is useful but not yet decisive.

Positive signs:

- method ordering remains `no_graph < single < multi_relation`;
- full multi-relation keeps zero diagnostic collisions;
- full multi-relation improves tracking and chain closure over no graph with separated confidence intervals;
- the mean full-minus-single recovery gap is larger than in several earlier easy-scenario probes.

Limitations:

- full versus single graph still has a wide seed-aware interval crossing zero;
- seed `0` and seed `3` favor single graph on recovery, so the full method is not uniformly dominant;
- only 20 episodes per seed were used;
- scout failure stresses perception loss, but it is not necessarily the cleanest task-support relation stressor.

## Decision

Do not promote this diagnostic to a main table yet.

Use it as evidence that a perception-support stressor is worth developing, but the next higher-value step is to design a sharper relation-dependency scenario where single graph cannot bypass the role-specific information flow as easily.

Recommended next step:

Run one more small stressor that targets relay and scout dependencies without changing the frozen main result, for example:

- delayed target-message propagation plus scout failure;
- stricter target-cache TTL under dropout scout failure;
- a matched `dropout030_scout_failure` extension with 50 episodes only if the scenario is being considered for a supplemental table.

## Artifacts

- Scenario registry change: `scripts/evaluate_3d_topology_robustness.py`
- Diagnostic sweep: `results/gate1_safety_fx60_dropout030_scout_failure_diag20/validation_checkpoint_summary.csv`
- Episode metrics: `results/gate1_safety_fx60_dropout030_scout_failure_diag20/validation_episode_metrics.csv`
- Full vs single stats: `docs/gate1_safety_fx60_dropout030_scout_failure_diag20_seed_aware_multi_vs_single/intercept_3d_strict_sensing_seed_aware_bootstrap.md`
- Full vs no-graph stats: `docs/gate1_safety_fx60_dropout030_scout_failure_diag20_seed_aware_multi_vs_no_graph/intercept_3d_strict_sensing_seed_aware_bootstrap.md`
