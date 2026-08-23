# DRTP-SEED-S1-A Post-Run Evaluation and Causal Audit

Protocol: `DRTP-SEED-S1-A-V1`  
Status: `POST-RUN AUDIT COMPLETED`  

## Scope

This report uses only the seven registered final checkpoints, fixed milestone training logs, sampler logs, and the development-only `440000–440099` evaluation tape. No training, checkpoint promotion, held-out evaluation, or canonical evaluation was performed.

## Evaluation completeness

- Unified raw records: **3500** (`7 × 5 conditions × 100 episodes`).
- Tape hash: `a7baa7dfeb802167d311b687a6ad18b87dd0e8dca18b7bb3ea47b37bf4280af6`.
- Final-checkpoint-only evaluation: **True**.
- Seven completed trajectories: **PASS**.
- Milestone checkpoints: **PASS**.
- Frozen-milestone per-step trajectory telemetry: **MISSING**.

## Primary metrics

| run | J_nominal | J_F0 | J_OOD_mean | J_OOD_worst | timeout_F0 | timeout_OOD_mean | collision_F0 | exposure_F0 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| R0_G_REFERENCE | 84.7106 | 64.2437 | 65.2985 | 59.2277 | 0.9500 | 0.9300 | 0.0500 | 1.0000 |
| R1_B_REFERENCE | 107.9433 | 93.7900 | 84.8554 | 74.1004 | 0.8000 | 0.9000 | 0.0400 | 0.9600 |
| R2_I_INIT | 181.6632 | 152.0058 | 154.6831 | 142.8434 | 0.9700 | 0.9433 | 0.0000 | 1.0000 |
| R3_I_ENV | 83.6781 | 72.8466 | 81.3564 | 76.8066 | 1.0000 | 0.9833 | 0.0000 | 1.0000 |
| R4_I_ACTION | 74.1924 | 63.0353 | 65.2317 | 56.8556 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| R5_I_MINIBATCH | 88.5870 | 87.6692 | 84.3543 | 70.6319 | 0.8700 | 0.9567 | 0.1300 | 1.0000 |
| R6_I_TOPOLOGY | 51.1490 | 87.8401 | 98.9147 | 74.8990 | 0.8400 | 0.8900 | 0.1600 | 1.0000 |

## Pre-registered causal interpretation

The intervention table is written to `rng_intervention_effects.csv`. Gap closure uses the frozen good-minus-weak reference gap and reverses timeout sign so higher is favorable. A final metric difference is not treated as a causal result without the pre-registered temporal and replication gates.

### Reference-pair audit

The registered R0/R1 good-versus-weak ordering is not reproduced on the final tape: R1 is higher than R0 on J_F0, J_OOD_mean, and J_OOD_worst, and R1 has lower F0 timeout. Therefore the numerical gap-closure rows are retained for provenance but are not interpretable as valid good-to-weak causal gaps.

| intervention | outcomes with absolute gap closure ≥ 0.5 | provisional factor signal |
|---|---:|---|
| R2_I_INIT | 4 / 4 | True |
| R3_I_ENV | 2 / 4 | True |
| R4_I_ACTION | 4 / 4 | True |
| R5_I_MINIBATCH | 0 / 4 | False |
| R6_I_TOPOLOGY | 1 / 4 | False |

## Sampler and learning-curve evidence

Fixed milestone rows are in `milestone_learning_curves.csv`; final sampler distributions are in `sampler_final_summary.csv`. They are descriptive only and do not replace the required per-step frozen-milestone trajectory telemetry.

## Final decision

**F_TECHNICAL_INVALID**

Required frozen-milestone per-step trajectory telemetry is absent, and the registered R0 good/R1 weak ordering is reversed on the frozen final tape; causal S1-A gates cannot be adjudicated from these assets.

Historical DRTP development conclusions are unchanged. No algorithm design or subsequent training is authorized by this report.
