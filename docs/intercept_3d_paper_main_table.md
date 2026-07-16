# 3DOF Paper-Facing Main Table

Generated: 2026-07-16T21:05:02

This table is an evidence triage table for manuscript drafting. It should not be treated as the final paper table until the remaining baselines and ablations are complete.

| Scenario | Role | N | Success single/multi (%) | Success delta pp [95% CI] | Recovery single/multi (%) | Recovery delta pp [95% CI] | Recovery steps single/multi | Recovery steps delta [95% CI] | Episode steps delta [95% CI] | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Relay failure | Main node-failure evidence | 90 | 92.2 / 100.0 | +7.8 [+2.2, +13.3] | 92.2 / 100.0 | +7.8 [+2.2, +13.3] | 21.8 / 5.6 | -16.2 [-28.0, -4.5] | -16.2 [-28.0, -4.5] | Separated recovery evidence |
| Scout failure | Supporting node-failure evidence | 90 | 94.4 / 96.7 | +2.2 [-3.3, +7.8] | 94.4 / 96.7 | +2.2 [-3.3, +7.8] | 17.1 / 12.7 | -4.4 [-16.2, +7.3] | -4.4 [-16.2, +7.3] | Positive trend; CI crosses zero |
| Communication dropout 0.30 | Communication robustness trend | 90 | 93.3 / 96.7 | +3.3 [-2.2, +8.9] | NA / NA | NA | NA / NA | NA | -6.9 [-18.8, +5.0] | Positive trend; CI crosses zero |
| Two-step message delay | Communication robustness trend | 90 | 94.4 / 96.7 | +2.2 [-3.3, +7.8] | NA / NA | NA | NA / NA | NA | -4.5 [-16.3, +7.2] | Positive trend; CI crosses zero |
| Radar dropout 0.25 | Sensing robustness trend | 90 | 92.2 / 94.4 | +2.2 [-4.4, +8.9] | NA / NA | NA | NA / NA | NA | -4.5 [-18.8, +9.7] | Positive trend; CI crosses zero |
| Communication range 0.75 | Stress / boundary case | 90 | 96.7 / 94.4 | -2.2 [-8.9, +3.3] | NA / NA | NA | NA / NA | NA | +5.0 [-6.8, +19.1] | Mixed; keep as stress case |

## Use In Paper

- Main defensible claim: relay-failure recovery, where the multi-relation role graph improves post-failure kill-chain recovery probability and reduces recovery time.
- Supporting claim: scout-failure and other communication/sensing perturbations show positive trends but need larger budgets or stronger baselines before being written as primary conclusions.
- Boundary claim: communication range 0.75 is a stress case and should be reported honestly as mixed rather than forced into a positive result.

## Formal Task-Support Ablation

Full multi-relation is compared against `no_task_support`; positive success/recovery deltas favor the full model, while negative step deltas favor the full model.

| Scenario | N | Success full/no-task | Success delta pp [95% CI] | Recovery full/no-task | Recovery delta pp [95% CI] | Recovery-step delta [95% CI] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| relay_failure | 90 | 100.0 / 88.9 | +11.1 [+5.6, +17.8] | 100.0 / 88.9 | +11.1 [+5.6, +17.8] | -23.5 [-37.7, -11.6] |
| scout_failure | 90 | 96.7 / 87.8 | +8.9 [+3.3, +15.6] | 96.7 / 87.8 | +8.9 [+3.3, +15.6] | -18.8 [-32.9, -7.0] |

## Formal Role-Pair Gate Ablation

Full multi-relation is compared against `no_role_pair_gate`; this keeps relation channels but replaces the learned role-pair message gate with a scale-matched constant gate. Positive success/recovery deltas favor the full model, while negative step deltas favor the full model.

| Scenario | N | Success full/no-gate | Success delta pp [95% CI] | Recovery full/no-gate | Recovery delta pp [95% CI] | Recovery-step delta [95% CI] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| relay_failure | 90 | 100.0 / 95.6 | +4.4 [+1.1, +8.9] | 100.0 / 95.6 | +4.4 [+1.1, +8.9] | -9.8 [-19.2, -2.7] |
| scout_failure | 90 | 96.7 / 93.3 | +3.3 [-1.1, +8.9] | 96.7 / 93.3 | +3.3 [-1.1, +7.8] | -7.5 [-19.0, +2.0] |

## Strict-Sensing Scenario-Depth Table

This table uses the opt-in `--strict-target-sensing` setting, where local observations, shared observations, and graph target nodes do not fall back to true target state before a valid detection. The checkpoints are a budget-labeled scenario-depth pilot: existing node-failure curriculum checkpoints were fine-tuned for 10 PPO updates under strict sensing, then evaluated with 30 episodes per seed and scenario.

Use the relay-failure row as a stronger scenario-depth result. Keep scout failure as supporting trend evidence only.

| Scenario | N | Success single/multi (%) | Success delta pp [95% CI] | Recovery single/multi (%) | Recovery delta pp [95% CI] | Recovery steps single/multi | Recovery-step delta [95% CI] | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Relay failure | 90 | 71.1 / 96.7 | +25.6 [+15.6, +36.7] | 71.1 / 96.7 | +25.6 [+15.6, +36.7] | 67.5 / 13.6 | -53.9 [-75.3, -32.6] | Separated strict-sensing recovery evidence |
| Scout failure | 90 | 78.9 / 85.6 | +6.7 [-4.4, +18.9] | 78.9 / 85.6 | +6.7 [-5.6, +18.9] | 51.0 / 37.0 | -14.0 [-39.9, +12.0] | Positive strict-sensing trend; CI crosses zero |
