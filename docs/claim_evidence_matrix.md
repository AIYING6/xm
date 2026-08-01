# Claim Evidence Matrix

Generated: 2026-08-02T01:40:10

Purpose:

```text
Bind each paper-facing claim to concrete result files, figures/tables, quantitative values, and wording boundaries.
This matrix is generated from current result CSVs and should be used while drafting or revising the manuscript.
```

## Summary

```text
claims_checked = 9
failures = 0
```

## Matrix

| ID | Type | Recommended wording | Evidence | Boundary | Status |
|---|---|---|---|---|---|
| C1 | main_result | EA-RG-MAPPO-S improves finite-communication pursuit stability and consistently lowers collision rates against MAPPO and GAT-MAPPO in the simplified 2D UAV pursuit benchmark. | r4 success=0.926, collision=0.054; r6 success=0.919, collision=0.064; r8 success=0.890, collision=0.083; r10 success=0.879, collision=0.086<br>`results/final_comm_300_summary.csv` | Do not claim full 6DOF combat, missile/radar, or human-UAV teaming validation from this result. | ok |
| C2 | statistical_support | Seed-paired descriptive statistics provide effect-direction context across the three tested seeds. | MAPPO r4 collision_reduction: mean_diff=0.173, ci95=[-0.107,0.454]; GAT-MAPPO r4 collision_reduction: mean_diff=0.081, ci95=[0.039,0.123]; GAT-MAPPO r8 success_gain: mean_diff=0.106, ci95=[0.005,0.206]<br>`results/final_300_paired_statistics.csv` | The project uses descriptive paired intervals over three seeds; intervals that cross zero should be reported cautiously and not treated as strong hypothesis-test evidence. | ok |
| C3 | robustness_diagnostic | Under evaluation-time communication dropout, EA-RG-MAPPO-S retains lower collision rates than both baselines at the tested radii. | r4 p=0.5 collision: EA=0.047, MAPPO=0.300, GAT=0.167; r8 p=0.5 collision: EA=0.053, MAPPO=0.293, GAT=0.173<br>`results/comm_dropout_robustness_summary.csv` | This is a 50-episode-per-seed diagnostic, so it should be presented as appendix robustness evidence. | ok |
| C4 | aggregate_diagnostic | Aggregate descriptive metrics summarize that EA-RG-MAPPO-S has the strongest success-collision margin across the evaluated finite-communication conditions. | final_cross_radius: EA mean_success=0.903, mean_collision=0.072, conservative_margin=0.793; dropout_diagnostic: EA mean_success=0.892, mean_collision=0.070, conservative_margin=0.747<br>`results/aggregate_robustness_summary.csv` | The aggregate score is for organization and description only; it is not a new training objective or replacement for per-radius tables. | ok |
| C5 | generalization_diagnostic | On held-out communication radii, the final method preserves lower collision rates than the baselines. | r5 collision: EA=0.067, MAPPO=0.227, GAT=0.113; r7 collision: EA=0.100, MAPPO=0.200, GAT=0.140; r9 collision: EA=0.067, MAPPO=0.153, GAT=0.173<br>`results/radius_interpolation_summary.csv` | This is a 50-episode-per-seed interpolation diagnostic, not the main evaluation table. | ok |
| C6 | robustness_diagnostic | The low-collision behavior remains visible under a stronger mixed-target speed setting. | r4 speed=0.90 collision: EA=0.097, MAPPO=0.240, GAT=0.237; r8 speed=0.90 collision: EA=0.130, MAPPO=0.300, GAT=0.203<br>`results/speed_robustness_summary.csv` | This robustness check uses 100 episodes per seed and should not replace the 300-episode main table. | ok |
| C7 | mechanism_diagnostic | Evaluation-time masking suggests the communication/target edge-feature group has the most consistent diagnostic effect. | r4 comm/target mask: success 0.878->0.867, collision 0.078->0.089; r8 comm/target mask: success 0.867->0.856, collision 0.089->0.100<br>`results/edge_feature_ablation_summary.csv` | This is evaluation-time masking without retraining; do not present it as a structural ablation proof. | ok |
| C8 | extension_boundary | The role-graph interface has been prepared and smoke-tested for LAG-like 6DOF states, but real JSBSim/LAG validation is still blocked by missing runtime assets/imports. | adapter_checks=26, wrapper_checks=11, probe_rows=29, real_lag_blocker_present=True<br>`results/lag_role_graph_adapter_test.csv; results/lag_role_graph_wrapper_test.csv; results/lag_jsbsim_migration_probe.csv` | Use this only as migration-readiness evidence, not as completed 6DOF combat validation. | ok |
| C9 | negative_boundary | The auxiliary target-intent branch is retained only as a diagnostic and should not be used as a main contribution. | plain_accuracy=0.587, balanced_accuracy=0.200<br>`docs/english_experiments_draft.md` | Do not claim high-accuracy intent recognition in the current paper. | ok |

## Use Boundary

```text
Use the recommended wording as a ceiling, not a starting point for stronger claims.
Any new experiment, renamed method, or changed result table should regenerate this matrix before manuscript edits.
```
