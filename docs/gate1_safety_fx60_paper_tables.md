# Gate 1 Safety Fixed-Update-60 Paper Tables

Generated: 2026-07-19T16:35:17

## Status

These tables package the fixed-budget hardened safety evidence for paper drafting. They do not introduce new training or new checkpoint selection.

## Main Comparison

| Method | Recovery | Tracking | Connectivity | Chain | Timeout | Collision |
| --- | --- | --- | --- | --- | --- | --- |
| MAPPO (no graph) | 21.8 +/- 41.9 | 14.8 +/- 27.6 | 7.8 +/- 7.9 | 3.7 +/- 7.0 | 77.4 +/- 41.3 | 0.8 +/- 0.8 |
| Single-graph MAPPO | 53.2 +/- 38.1 | 47.5 +/- 25.4 | 14.6 +/- 6.0 | 7.6 +/- 5.5 | 44.0 +/- 36.1 | 2.8 +/- 2.9 |
| Full multi-relation | 88.6 +/- 13.7 | 77.6 +/- 16.8 | 20.3 +/- 1.8 | 13.8 +/- 2.9 | 11.4 +/- 13.7 | 0.0 +/- 0.0 |

## Mechanism Ablations

| Variant | Recovery | Tracking | Chain | Timeout | Collision | Seed recovery |
| --- | --- | --- | --- | --- | --- | --- |
| Full multi-relation | 88.6 +/- 13.7 | 77.6 +/- 16.8 | 13.8 +/- 2.9 | 11.4 +/- 13.7 | 0.0 +/- 0.0 | [0.65, 0.90, 0.99, 0.92, 0.97] |
| w/o task-support relation | 64.8 +/- 37.3 | 59.6 +/- 39.4 | 8.9 +/- 6.3 | 34.4 +/- 37.6 | 0.8 +/- 0.8 | [0.91, 0.89, 0.72, 0.72, 0.00] |
| w/o role-pair gate | 64.8 +/- 38.0 | 60.7 +/- 38.0 | 9.9 +/- 6.4 | 35.2 +/- 38.0 | 0.0 +/- 0.0 | [0.53, 0.85, 1.00, 0.82, 0.04] |

## Seed-Aware Deltas

| Comparison | Recovery delta | Tracking delta | Chain delta | Timeout delta |
| --- | --- | --- | --- | --- |
| Full vs Single graph | +35.4 [+1.2, +73.0] pp | +30.1 [+1.1, +61.5] pp | +6.1 [-0.1, +12.5] pp | -32.6 [-67.6, +0.0] pp |
| Full vs No graph | +66.8 [+28.6, +93.8] pp | +62.8 [+42.5, +84.2] pp | +10.1 [+3.8, +14.8] pp | -66.0 [-92.4, -28.4] pp |
| Full vs w/o task-support | +23.8 [-9.2, +63.6] pp | +18.0 [-6.3, +42.3] pp | +4.8 [-0.9, +11.0] pp | -23.0 [-63.2, +9.8] pp |
| Full vs w/o role-pair gate | +23.8 [+2.8, +59.2] pp | +16.9 [+2.7, +38.8] pp | +3.9 [+0.2, +10.2] pp | -23.8 [-59.2, -2.8] pp |

## Failure-Timing Generalization

This fixed-checkpoint scenario-depth table evaluates early versus nominal relay-failure onset without retraining.

| Scenario | No graph recovery | Single recovery | Full recovery | Full vs Single | Full vs No graph |
| --- | ---: | ---: | ---: | ---: | ---: |
| Early relay failure | 23.2 | 46.6 | 88.2 | +41.6 [+4.4, +78.6] pp | +65.0 [+27.2, +93.2] pp |
| Nominal relay failure | 21.8 | 53.8 | 88.0 | +34.2 [+0.6, +71.8] pp | +66.2 [+29.4, +93.2] pp |

## Recommended Paper Claim

- The full multi-relation method strongly improves post-failure recovery over no-graph and single-graph baselines.
- Role-pair-conditioned message gating is the cleanest current mechanism ablation; its seed-aware recovery interval separates in favor of the full method.
- Task-support relation removal lowers mean recovery but the seed-aware interval crosses zero, so use it as supportive rather than decisive evidence.
- The fixed-checkpoint early-failure timing test supports limited timing robustness against earlier relay loss; delayed/late failure remains a metric-validity limitation under the current episode termination.

## Caution

- This package uses the frozen fixed `update_0060` rule. Do not mix these tables with validation-selected results without stating the checkpoint-selection protocol.
- `no_curriculum` is not included. If omitted from the paper, state that the current evidence targets graph/message mechanisms, not isolated curriculum causality.

## Artifacts

- Main CSV: `results/gate1_safety_fx60_paper_tables/main_results.csv`
- Ablation CSV: `results/gate1_safety_fx60_paper_tables/ablation_results.csv`
- Bootstrap CSV: `results/gate1_safety_fx60_paper_tables/seed_aware_deltas.csv`
- Main LaTeX: `results/gate1_safety_fx60_paper_tables/main_results_latex.tex`
- Ablation LaTeX: `results/gate1_safety_fx60_paper_tables/ablation_results_latex.tex`
- Bootstrap LaTeX: `results/gate1_safety_fx60_paper_tables/seed_aware_deltas_latex.tex`
- Timing summary CSV: `results/gate1_safety_fx60_failure_timing_generalization_formal_merged/timing_summary.csv`
- Timing LaTeX: `results/gate1_safety_fx60_failure_timing_generalization_formal_merged/timing_generalization_latex.tex`
