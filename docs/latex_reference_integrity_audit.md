# LaTeX Reference Integrity Audit

Generated: 2026-08-02T01:40:10

Purpose:

```text
Check that Chinese and English LaTeX projects keep required table/figure labels and manuscript references intact.
This audit complements the broader LaTeX static check by recording publishable evidence labels as an explicit artifact.
```

## Summary

```text
reference_checks = 86
failures = 0
chinese_tex_files = 19
chinese_labels = 22
english_tex_files = 19
english_labels = 22
```

## Rows

| Project | Type | Item | Status | Notes |
|---|---|---|---|---|
| english | duplicate_labels | `all_labels` | ok | no duplicate labels |
| english | missing_ref_targets | `all_refs` | ok | all refs resolve to labels |
| english | required_label | `tab:training_settings` | ok | label present |
| english | required_label | `tab:final_comm_300_results` | ok | label present |
| english | required_label | `tab:ablation_results` | ok | label present |
| english | required_label | `tab:final_300_paired_ci` | ok | label present |
| english | required_label | `tab:comm_dropout_robustness` | ok | label present |
| english | required_label | `tab:comm_dropout_paired_ci` | ok | label present |
| english | required_label | `tab:aggregate_robustness` | ok | label present |
| english | required_label | `tab:radius_interpolation` | ok | label present |
| english | required_label | `tab:speed_robustness` | ok | label present |
| english | required_label | `tab:edge_feature_masking` | ok | label present |
| english | required_label | `fig:method_overview_en` | ok | label present |
| english | required_label | `fig:final_success_en` | ok | label present |
| english | required_label | `fig:final_collision_en` | ok | label present |
| english | required_label | `fig:comm_dropout_success_en` | ok | label present |
| english | required_label | `fig:comm_dropout_collision_en` | ok | label present |
| english | required_label | `fig:radius_interp_success_en` | ok | label present |
| english | required_label | `fig:radius_interp_collision_en` | ok | label present |
| english | required_label | `fig:speed_success_r4_en` | ok | label present |
| english | required_label | `fig:speed_collision_r4_en` | ok | label present |
| english | required_label | `fig:speed_success_r8_en` | ok | label present |
| english | required_label | `fig:speed_collision_r8_en` | ok | label present |
| english | required_label | `fig:edge_feature_delta_en` | ok | label present |
| english | required_ref | `tab:training_settings` | ok | reference present |
| english | required_ref | `tab:final_comm_300_results` | ok | reference present |
| english | required_ref | `tab:ablation_results` | ok | reference present |
| english | required_ref | `tab:final_300_paired_ci` | ok | reference present |
| english | required_ref | `tab:comm_dropout_robustness` | ok | reference present |
| english | required_ref | `tab:comm_dropout_paired_ci` | ok | reference present |
| english | required_ref | `tab:aggregate_robustness` | ok | reference present |
| english | required_ref | `tab:radius_interpolation` | ok | reference present |
| english | required_ref | `tab:speed_robustness` | ok | reference present |
| english | required_ref | `tab:edge_feature_masking` | ok | reference present |
| english | required_ref | `fig:method_overview_en` | ok | reference present |
| english | required_ref | `fig:final_success_en` | ok | reference present |
| english | required_ref | `fig:final_collision_en` | ok | reference present |
| english | required_ref | `fig:comm_dropout_success_en` | ok | reference present |
| english | required_ref | `fig:comm_dropout_collision_en` | ok | reference present |
| english | required_ref | `fig:radius_interp_success_en` | ok | reference present |
| english | required_ref | `fig:radius_interp_collision_en` | ok | reference present |
| english | required_ref | `fig:speed_success_r4_en` | ok | reference present |
| english | required_ref | `fig:speed_collision_r8_en` | ok | reference present |
| english | required_ref | `fig:edge_feature_delta_en` | ok | reference present |
| chinese | duplicate_labels | `all_labels` | ok | no duplicate labels |
| chinese | missing_ref_targets | `all_refs` | ok | all refs resolve to labels |
| chinese | required_label | `tab:training_settings` | ok | label present |
| chinese | required_label | `tab:final_comm_300_results` | ok | label present |
| chinese | required_label | `tab:ablation_results` | ok | label present |
| chinese | required_label | `tab:final_300_paired_ci` | ok | label present |
| chinese | required_label | `tab:comm_dropout_robustness` | ok | label present |
| chinese | required_label | `tab:comm_dropout_paired_ci` | ok | label present |
| chinese | required_label | `tab:aggregate_robustness` | ok | label present |
| chinese | required_label | `tab:radius_interpolation` | ok | label present |
| chinese | required_label | `tab:speed_robustness` | ok | label present |
| chinese | required_label | `tab:edge_feature_masking` | ok | label present |
| chinese | required_label | `fig:method_overview` | ok | label present |
| chinese | required_label | `fig:final_success` | ok | label present |
| chinese | required_label | `fig:final_collision` | ok | label present |
| chinese | required_label | `fig:comm_dropout_success` | ok | label present |
| chinese | required_label | `fig:comm_dropout_collision` | ok | label present |
| chinese | required_label | `fig:radius_interp_success` | ok | label present |
| chinese | required_label | `fig:radius_interp_collision` | ok | label present |
| chinese | required_label | `fig:speed_success_r4` | ok | label present |
| chinese | required_label | `fig:speed_collision_r4` | ok | label present |
| chinese | required_label | `fig:speed_success_r8` | ok | label present |
| chinese | required_label | `fig:speed_collision_r8` | ok | label present |
| chinese | required_label | `fig:edge_feature_delta` | ok | label present |
| chinese | required_ref | `tab:final_comm_300_results` | ok | reference present |
| chinese | required_ref | `tab:final_300_paired_ci` | ok | reference present |
| chinese | required_ref | `tab:comm_dropout_robustness` | ok | reference present |
| chinese | required_ref | `tab:comm_dropout_paired_ci` | ok | reference present |
| chinese | required_ref | `tab:aggregate_robustness` | ok | reference present |
| chinese | required_ref | `tab:radius_interpolation` | ok | reference present |
| chinese | required_ref | `tab:speed_robustness` | ok | reference present |
| chinese | required_ref | `tab:edge_feature_masking` | ok | reference present |
| chinese | required_ref | `fig:method_overview` | ok | reference present |
| chinese | required_ref | `fig:final_success` | ok | reference present |
| chinese | required_ref | `fig:final_collision` | ok | reference present |
| chinese | required_ref | `fig:comm_dropout_success` | ok | reference present |
| chinese | required_ref | `fig:comm_dropout_collision` | ok | reference present |
| chinese | required_ref | `fig:radius_interp_success` | ok | reference present |
| chinese | required_ref | `fig:radius_interp_collision` | ok | reference present |
| chinese | required_ref | `fig:speed_success_r4` | ok | reference present |
| chinese | required_ref | `fig:speed_collision_r8` | ok | reference present |
| chinese | required_ref | `fig:edge_feature_delta` | ok | reference present |

## Use Boundary

```text
Passing this audit means key evidence table/figure labels and references exist in source LaTeX.
It does not replace PDF compilation and visual layout inspection.
```
