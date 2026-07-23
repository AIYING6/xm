# Gate 1 Safety Fixed-Update-60 Seed-Level Mechanism Figures

Generated: 2026-07-22T21:43:54

## Purpose

This package turns the frozen fixed-update-60 evidence into seed-level mechanism figures. It does not introduce new training, new checkpoint selection, or new test episodes.

## Main Seed-Level Recovery

| Method | Recovery | Seed recovery |
|---|---:|---:|
| MAPPO (no graph) | 21.8% +/- 41.9 | [0.0, 96.0, 0.0, 0.0, 13.0] |
| Single Graph | 53.2% +/- 38.1 | [82.0, 27.0, 0.0, 69.0, 88.0] |
| Full Multi-Rel. | 88.6% +/- 13.7 | [65.0, 90.0, 99.0, 92.0, 97.0] |

## Mechanism Ablation Seed Recovery

| Variant | Recovery | Seed recovery |
|---|---:|---:|
| Full Multi-Rel. | 88.6% +/- 13.7 | [65.0, 90.0, 99.0, 92.0, 97.0] |
| w/o Task Support | 64.8% +/- 37.3 | [91.0, 89.0, 72.0, 72.0, 0.0] |
| w/o Role-Pair Gate | 64.8% +/- 38.0 | [53.0, 85.0, 100.0, 82.0, 4.0] |

## Interpretation

- The main comparison figure makes the seed-level stability gap visible: full multi-relation has high recovery on all five seeds, while `no_graph` and `single` have large seed-to-seed failures.
- The paired ablation figure shows that role-pair gating is the cleaner mechanism result; task-support removal reduces mean recovery but has weaker seed separation.
- The bootstrap forest plot should be used to avoid overclaiming: only intervals that stay away from zero should be described as statistically separated.

## Artifacts

- Main seed scatter: `results/gate1_safety_fx60_seed_mechanism/main_seed_recovery_scatter.png`
- Ablation paired deltas: `results/gate1_safety_fx60_seed_mechanism/mechanism_ablation_seed_pairs.png`
- Bootstrap forest: `results/gate1_safety_fx60_seed_mechanism/seed_aware_delta_forest.png`
- Long-form seed CSV: `results/gate1_safety_fx60_seed_mechanism/seed_level_recovery_long.csv`
