# Gate 1 Safety Fixed-Update-60 Paper Tables

Generated: 2026-07-22T12:22:32

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

## Capacity-Control Baseline

This supplemental capacity-control table compares the full method with a single-graph baseline whose hidden dimension is increased to approximately match the full method's parameter count. The result is separate from the main fixed-budget table because the capacity-control single-graph checkpoints use validation selection.

| Method | Recovery | Tracking | Chain | Timeout | Collision | Seed recovery |
| --- | --- | --- | --- | --- | --- | --- |
| Param-matched single graph | 33.2 +/- 46.3 | 20.3 +/- 32.4 | 4.0 +/- 6.0 | 66.8 +/- 46.3 | 0.0 +/- 0.0 | [0.64, 0.00, 0.00, 0.02, 1.00] |
| Full multi-relation | 89.2 +/- 19.7 | 78.9 +/- 20.2 | 13.4 +/- 2.9 | 10.8 +/- 19.7 | 0.0 +/- 0.0 | [0.54, 0.98, 1.00, 0.98, 0.96] |

| Comparison | Recovery delta | Tracking delta | Chain delta | Timeout delta |
| --- | --- | --- | --- | --- |
| Full vs parameter-matched single graph | +56.0 [+11.2, +98.8] pp | +58.6 [+16.9, +91.7] pp | +9.4 [+3.6, +15.0] pp | -56.0 [-98.8, -11.2] pp |

## Role-Identity Ablation

This mechanism table removes explicit symbolic role identity while preserving physical platform heterogeneity. It supports the role-conditioned message-passing claim without treating platform dynamics or sensor differences as removed.

| Variant | Recovery | Tracking | Chain | Timeout | Collision | Seed recovery |
| --- | --- | --- | --- | --- | --- | --- |
| w/o explicit role identity | 56.8 +/- 36.5 | 36.8 +/- 32.4 | 8.7 +/- 5.7 | 35.2 +/- 24.1 | 0.0 +/- 0.0 | [0.40, 0.66, 0.02, 0.88, 0.88] |
| Full multi-relation | 87.2 +/- 21.0 | 76.4 +/- 18.3 | 12.9 +/- 3.1 | 12.8 +/- 21.0 | 0.0 +/- 0.0 | [0.50, 0.92, 0.98, 0.96, 1.00] |

| Comparison | Recovery delta | Tracking delta | Chain delta | Timeout delta |
| --- | --- | --- | --- | --- |
| Full vs w/o explicit role identity | +30.4 [+7.2, +64.4] pp | +39.7 [+3.1, +75.5] pp | +4.2 [-0.2, +10.1] pp | -22.4 [-41.6, -7.2] pp |

## Failure-Timing Generalization

This fixed-checkpoint scenario-depth table evaluates early versus nominal relay-failure onset without retraining.

| Scenario | No graph recovery | Single recovery | Full recovery | Full vs Single | Full vs No graph |
| --- | --- | --- | --- | --- | --- |
| Early relay failure | 23.2 | 46.6 | 88.2 | +41.6 [+4.4, +78.6] pp | +65.0 [+27.2, +93.2] pp |
| Nominal relay failure | 21.8 | 53.8 | 88.0 | +34.2 [+0.6, +71.8] pp | +66.2 [+29.4, +93.2] pp |

## Recommended Paper Claim

- The full multi-relation method strongly improves post-failure recovery over no-graph and single-graph baselines.
- Role-pair-conditioned message gating is the cleanest current mechanism ablation; its seed-aware recovery interval separates in favor of the full method.
- Task-support relation removal lowers mean recovery but the seed-aware interval crosses zero, so use it as supportive rather than decisive evidence.
- The fixed-checkpoint early-failure timing test supports limited timing robustness against earlier relay loss; delayed/late failure remains a metric-validity limitation under the current episode termination.
- The parameter-matched capacity-control baseline reduces the risk that the full method's advantage is merely caused by parameter count; report its seed-level variance rather than only the mean.
- The hardened no-role-identity ablation supports explicit role identity as a mechanism: full recovery is higher, but no-role can still solve some seeds, so phrase this as improved reliability rather than absolute necessity.

## Seed-Level Mechanism Figures

The seed-level mechanism figure package is recorded in `docs/gate1_safety_fx60_seed_mechanism_summary.md`.

- Main seed scatter: `results/gate1_safety_fx60_seed_mechanism/main_seed_recovery_scatter.png`
- Mechanism ablation paired seeds: `results/gate1_safety_fx60_seed_mechanism/mechanism_ablation_seed_pairs.png`
- Seed-aware bootstrap forest: `results/gate1_safety_fx60_seed_mechanism/seed_aware_delta_forest.png`

Use these figures to show that the full method's main advantage is seed-level reliability under relay failure, not only a higher aggregate mean.

## Caution

- This package uses the frozen fixed `update_0060` rule. Do not mix these tables with validation-selected results without stating the checkpoint-selection protocol.
- The three-seed no-curriculum diagnostic does not show an independent curriculum benefit, so topology curriculum should remain a training protocol rather than a main contribution.
- The capacity-control table uses validation-selected parameter-matched single-graph checkpoints and should be described as a supplemental credibility result unless promoted by the final paper protocol.
- The role-identity table uses validation-selected no-role checkpoints on a matched test split; keep its checkpoint-selection protocol explicit.

## Artifacts

- Main CSV: `results/gate1_safety_fx60_paper_tables/main_results.csv`
- Ablation CSV: `results/gate1_safety_fx60_paper_tables/ablation_results.csv`
- Bootstrap CSV: `results/gate1_safety_fx60_paper_tables/seed_aware_deltas.csv`
- Capacity-control CSV: `results/gate1_safety_fx60_paper_tables/capacity_control_results.csv`
- Role-identity CSV: `results/gate1_safety_fx60_paper_tables/role_identity_results.csv`
- Main LaTeX: `results/gate1_safety_fx60_paper_tables/main_results_latex.tex`
- Ablation LaTeX: `results/gate1_safety_fx60_paper_tables/ablation_results_latex.tex`
- Bootstrap LaTeX: `results/gate1_safety_fx60_paper_tables/seed_aware_deltas_latex.tex`
- Capacity-control LaTeX: `results/gate1_safety_fx60_paper_tables/capacity_control_latex.tex`
- Capacity-control delta LaTeX: `results/gate1_safety_fx60_paper_tables/capacity_control_deltas_latex.tex`
- Role-identity LaTeX: `results/gate1_safety_fx60_paper_tables/role_identity_latex.tex`
- Role-identity delta LaTeX: `results/gate1_safety_fx60_paper_tables/role_identity_deltas_latex.tex`
- Timing summary CSV: `results/gate1_safety_fx60_failure_timing_generalization_formal_merged/timing_summary.csv`
- Timing LaTeX: `results/gate1_safety_fx60_failure_timing_generalization_formal_merged/timing_generalization_latex.tex`
- Seed-level mechanism long CSV: `results/gate1_safety_fx60_seed_mechanism/seed_level_recovery_long.csv`
