# Gate 1 Safety Fixed-Update-60 Dropout Delay Scout-Failure Stressor Diagnostic

Last updated: 2026-07-22

## Purpose

This diagnostic is the accelerated follow-up to `dropout030_scout_failure`. It adds a two-step message delay to test whether the full multi-relation policy is more reliable when the scout node fails and target information is both lossy and delayed.

This is a screen for supplemental scenario depth, not a new main result.

## Protocol

Scenario name: `dropout030_delay2_scout_failure`

- communication dropout: `0.30`
- message delay: `2` steps
- failed blue node: scout, agent `0`
- node failure start: step `40`
- failure duration: `80`
- strict target sensing: enabled
- agent target-information bottleneck: enabled
- checkpoint: frozen `actor_critic_update_0060.pt`
- methods: `no_graph`, `single`, `multi_relation`
- training seeds: `0, 1, 2, 3, 4`
- episodes: `20` per seed and method
- evaluation base seed: `353000`

## Result

| Method | Recovery | Seed recovery | Tracking during failure | Chain closed | Timeout | Collision |
|---|---:|---:|---:|---:|---:|---:|
| MAPPO / no graph | 37.0% +/- 48.9 | [5.0, 100.0, 0.0, 0.0, 80.0] | 23.8% | 5.9% | 63.0% | 0.0% |
| Single graph | 56.0% +/- 44.9 | [90.0, 15.0, 0.0, 80.0, 95.0] | 50.1% | 8.7% | 42.0% | 2.0% |
| Full multi-relation | 85.0% +/- 14.1 | [80.0, 70.0, 100.0, 75.0, 100.0] | 78.3% | 13.6% | 15.0% | 0.0% |

Mean recovery deltas:

- full minus single graph: `+29.0 pp`;
- full minus no graph: `+48.0 pp`.

## Seed-Aware Statistics

Hierarchical bootstrap with 3000 samples:

Full versus single graph:

- recovery delta: `+29.0 pp`, 95% CI `[-5.0, +70.0] pp`;
- tracking delta: `+28.2 pp`, 95% CI `[+0.8, +61.1] pp`;
- chain-closed delta: `+4.9 pp`, 95% CI `[-0.6, +11.6] pp`;
- timeout delta: `-27.0 pp`, 95% CI `[-67.0, +6.0] pp`.

Full versus no graph:

- recovery delta: `+48.0 pp`, 95% CI `[+4.0, +86.0] pp`;
- tracking delta: `+54.5 pp`, 95% CI `[+22.6, +84.7] pp`;
- chain-closed delta: `+7.7 pp`, 95% CI `[+0.2, +14.3] pp`;
- timeout delta: `-48.0 pp`, 95% CI `[-86.0, -4.0] pp`.

## Interpretation

This is the best quick stressor screened so far:

- full multi-relation remains high-recovery and low-variance across seeds;
- full has zero diagnostic collisions, while single has a small collision rate;
- full separates strongly from no graph;
- full improves tracking over single with a positive seed-aware interval.

However, it still does not cleanly separate full from single on recovery probability because the 95% CI slightly crosses zero. Therefore it should be used as supplemental evidence or scenario-design justification, not as a new formal main table.

## Accelerated Decision

Stop adding more small stressors for now.

Reason:

- the main fixed-update-60 result is already the strongest paper evidence;
- the new delayed scout-failure stressor supports the same story but does not create a decisive new full-vs-single recovery claim;
- continuing to search for a perfect stressor risks delaying completion and overfitting the experimental narrative.

Next work should shift to finish mode:

1. freeze current experimental evidence;
2. organize main, mechanism, capacity-control, timing-generalization, no-curriculum boundary, and stressor-screen results;
3. complete manuscript tables/figures and consistency checks;
4. only run more training if a specific reviewer-critical gap remains.

## Artifacts

- Scenario registry change: `scripts/evaluate_3d_topology_robustness.py`
- Diagnostic sweep: `results/gate1_safety_fx60_dropout030_delay2_scout_failure_diag20/validation_checkpoint_summary.csv`
- Episode metrics: `results/gate1_safety_fx60_dropout030_delay2_scout_failure_diag20/validation_episode_metrics.csv`
- Full vs single stats: `docs/gate1_safety_fx60_dropout030_delay2_scout_failure_diag20_seed_aware_multi_vs_single/intercept_3d_strict_sensing_seed_aware_bootstrap.md`
- Full vs no-graph stats: `docs/gate1_safety_fx60_dropout030_delay2_scout_failure_diag20_seed_aware_multi_vs_no_graph/intercept_3d_strict_sensing_seed_aware_bootstrap.md`
