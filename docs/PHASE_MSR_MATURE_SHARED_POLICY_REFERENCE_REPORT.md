# Phase MSR — Mature Shared-Policy Reference Report

## Scope and frozen status

This report completes **Stage MSR only** under `POST_FL_MATURE_SHARED_POLICY_AND_FINAL_ALGORITHM_PLAN.md`. It establishes the 1M-step equal-mixture shared-policy reference; it is neither a canonical result nor a final-algorithm selection. No ENMM, canonical seed, OOD, ablation, or formal five-seed run was started.

- Implementation commit: `dcc9d6b6b03da22802c3c8f67d98dd8d056ba966`
- Branch: `codex/relation-aware-single-graph-v1`
- Protocol: `PHASE-MSR-V1`
- SG architecture: unchanged matched Single-Graph MAPPO
- Trainable parameters: **116,728**
- Mixed-50 configuration hash: `8070df64e0d145b022d17b12cdfe2dbf3406d93133fb697d43fe871e24c547ab`

## Training integrity

| arm | cell | final checkpoint SHA256 | realized nominal / F0 episodes |
|---|---|---|---|
| mixed50_sg | seed1801 | `114fda2e0fd7ea2db04daf785e76d52e0fdea514435ed6795363698326e3a2d9` | 1972 / 1887 |
| mixed50_sg | seed1802 | `144c6d56ca61c44d580156a3a5f5aa0d7b5ff3d1da7a9473defdd9dcced51ee9` | 1953 / 1928 |

Both cells trained from scratch for 3,907 updates = 1,000,192 environment steps with 4 environments × 64 rollout steps. Milestones at 300,032, 499,968, 750,080, and 1,000,192 steps were verified present and are used only for learning-curve analysis; the final checkpoint is the only evaluated checkpoint.

## Fresh paired evaluation tape

- Development-only IDs: `380000–380099`
- Cases per condition: 100
- F0: relay node 1, onset step 44, duration 80
- Tape SHA256: `b403239d849cc9d80730c34248483fff77407d53111010d747649e0b89270d01`
- Every one of the six checkpoints was evaluated on the same 100 nominal/F0 pairs; exposure is reported and no rows are discarded.

## Six-checkpoint unified evaluation

| group | seed | J_nominal | J_failure | Delta_J | collision (F0) | timeout (F0) | constraint (F0) | exposure |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fl_nominal_expert | 1801 | 103.712179 | 34.921951 | 68.790228 | 0.000000 | 1.000000 | 0.000000 | 1.000000 |
| fl_nominal_expert | 1802 | 22.510347 | 10.384699 | 12.125648 | 0.000000 | 0.960000 | 0.000000 | 1.000000 |
| fl_f0_expert | 1801 | 80.724363 | 65.558993 | 15.165370 | 0.010000 | 0.990000 | 0.000000 | 1.000000 |
| fl_f0_expert | 1802 | 38.479867 | 63.387111 | -24.907243 | 0.030000 | 0.970000 | 0.000000 | 1.000000 |
| mixed50_sg | 1801 | 91.941832 | 104.633138 | -12.691306 | 0.050000 | 0.920000 | 0.000000 | 0.990000 |
| mixed50_sg | 1802 | 183.381681 | 171.978675 | 11.403006 | 0.050000 | 0.780000 | 0.000000 | 1.000000 |

## Pooled metrics and normalized competence

| group | J_nominal | J_failure | Delta_J | collision (F0) | timeout (F0) | constraint (F0) | exposure |
|---|---:|---:|---:|---:|---:|---:|---:|
| fl_nominal_expert | 63.111263 | 22.653325 | 40.457938 | 0.000000 | 0.980000 | 0.000000 | 1.000000 |
| fl_f0_expert | 59.602115 | 64.473052 | -4.870937 | 0.020000 | 0.980000 | 0.000000 | 1.000000 |
| mixed50_sg | 137.661757 | 138.305907 | -0.644150 | 0.050000 | 0.850000 | 0.000000 | 0.995000 |

The empirical mature specialist references on this **new** tape are:

- `J_N_star` = 63.111263 (pooled nominal-expert nominal score)
- `J_F_star` = 64.473052 (pooled F0-expert failure score)

For Mixed-50 SG:

- `C_N` = 2.181255
- `C_F` = 2.145174
- `C_min` = 2.145174
- Classification: **M1 — already_balanced**

This is a descriptive mature shared-policy classification, not a gradient-conflict claim and not a GO/NO-GO decision.

## Safety and telemetry

Failure-condition collision, timeout, constraint, exposure, episode-length, path-switch, direct/relay-path, task-support, legal-information, cache-age, traveled-distance, and control-effort metrics are retained in `six_checkpoint_per_seed_metrics.csv`. The pooled safety comparison is shown above; no safety metric was silently omitted.

## Mixed-50 milestone learning curves

| cell | milestone | environment steps | train average reward | PPO loss | approx. KL | entropy |
|---|---|---:|---:|---:|---:|---:|
| seed1801 | 300k | 300032 | -0.004168 | 0.075324 | 0.000691 | 2.395613 |
| seed1801 | 500k | 499968 | 0.161070 | 0.660203 | 0.001086 | 2.832385 |
| seed1801 | 750k | 750080 | 0.127439 | 0.135793 | 0.000464 | 2.301538 |
| seed1801 | 1m | 1000192 | 0.101657 | 0.160945 | 0.001290 | 2.295321 |
| seed1802 | 300k | 300032 | 0.033174 | 0.367235 | 0.000278 | 2.325403 |
| seed1802 | 500k | 499968 | 0.094725 | 0.138648 | 0.000461 | 2.349838 |
| seed1802 | 750k | 750080 | 0.154268 | 0.679725 | 0.001058 | 2.661050 |
| seed1802 | 1m | 1000192 | 0.174120 | 0.420480 | 0.003012 | 2.471149 |

The full machine-readable curve table is `mixed50_milestone_learning_curves.csv`. Milestones were not inspected for, or used in, checkpoint selection.

## Stop condition

Stage MSR is complete. `enmm_started = false`, `ood_started = false`, `ablation_started = false`, and `formal_five_seed_started = false` are asserted in `MSR_RESULT.json`. No new algorithm or training is authorized by this report.
