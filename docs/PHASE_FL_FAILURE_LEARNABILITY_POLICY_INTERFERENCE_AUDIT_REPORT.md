# Phase FL — Failure Learnability & Policy-Interference Audit Report

## Final diagnostic conclusion

```text
Diagnostic category: B
Label: failure_not_shown_learnable_current_formulation
CTP: CLOSED
TP-2: NO-GO
New algorithm: NOT STARTED
Follow-up training: NOT AUTHORIZED
```

The F0-only expert did not produce a consistent failure-performance improvement over the same-seed nominal expert. This does **not** prove that failure is impossible to learn; it means that failure learnability was not demonstrated under the frozen SG observation, reward, PPO configuration, and 300,032-step budget. The next investigation must therefore target the current policy/observation formulation and post-failure behavior, not another curriculum schedule.

## Archive and protocol integrity

- Result archive: `phase_fl_results.tar.gz`
- Archive SHA256: `6EB748BAA4A47FE5F43BE149C28F69D0651373B59E806BC39F12BFA5839E3C79`
- FL tape: paired IDs `370000–370049`
- Tape hash: `1a56599c869e031e2df90ada85942c3298e221b23caa450c005285e739ab0625`
- Arms: `fl_nominal_expert`, `fl_f0_expert`
- Seeds: `1801,1802`
- Completed runs: `4/4`
- Budget per run: `300,032` environment steps = `4 × 64 × 1172`
- Architecture: matched Single-Graph, `116,728` parameters
- F0: relay agent `1`, onset `44`, duration `80`
- Evaluation: 50 paired episodes per seed on the same FL tape
- Canonical seeds/results: not used
- TP-2 and new algorithms: not started

All four manifests report `completed`, `1172` training-log updates, final-checkpoint-only evaluation, `resume=false`, `early_stopping=false`, and `checkpoint_promotion=false`.

## Per-seed primary metrics

| Arm | Seed | J_nominal | J_failure | Delta_J | Collision failure | Timeout failure | Constraint failure | Exposure |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Nominal expert | 1801 | 33.7519 | 31.7324 | 2.0194 | 0.00 | 1.00 | 0.00 | 1.00 |
| Nominal expert | 1802 | 27.3109 | 15.9284 | 11.3825 | 0.00 | 1.00 | 0.00 | 1.00 |
| F0 expert | 1801 | 13.4164 | 11.7001 | 1.7162 | 0.00 | 1.00 | 0.00 | 1.00 |
| F0 expert | 1802 | 38.9011 | 21.0298 | 17.8712 | 0.00 | 1.00 | 0.00 | 1.00 |

The values above are the same-seed paired evaluation means from the archived raw/paired CSVs. Pooled means are:

| Arm | J_nominal | J_failure | Delta_J |
|---|---:|---:|---:|
| Nominal expert | 30.5314 | 23.8304 | 6.7010 |
| F0 expert | 26.1587 | 16.3650 | 9.7937 |

## Expert contrasts and frozen A/B/C rule

The preregistered contrasts are:

```text
G_F = J_failure(F0 expert) - J_failure(nominal expert)
G_N = J_nominal(F0 expert) - J_nominal(nominal expert)
R_F = G_F / abs(J_failure(nominal expert))
R_N = G_N / abs(J_nominal(nominal expert))
```

The frozen thresholds are `R_F >= 0.10` for clear failure improvement and `R_N <= -0.10` for a material nominal decline, with the required seed-wise directions.

| Seed | G_F | R_F | G_N | R_N |
|---:|---:|---:|---:|---:|
| 1801 | -20.0323 | -0.6313 | -20.3355 | -0.6025 |
| 1802 | +5.1014 | +0.3203 | +11.5902 | +0.4244 |
| **Pooled** | **-7.4654** | **-0.3133** | **-4.3727** | **-0.1432** |

Failure improvement is neither positive in the pooled result nor consistent across seeds. Therefore `failure_clearly_improves = FALSE`, and the unique frozen classification is **B**. Although the pooled nominal contrast is below -10%, the seed-wise nominal directions are contradictory, so the frozen material-decline rule is also false; this does not change the B classification.

## Safety, exposure, and behavior telemetry

| Metric | Nominal expert | F0 expert |
|---|---:|---:|
| Collision during failure | 0.00 | 0.00 |
| Timeout during failure | 1.00 | 1.00 |
| Constraint violation | 0.00 | 0.00 |
| Failure exposure | 1.00 | 1.00 |
| Failure episode length | 260.0 | 260.0 |
| Path switches during failure | 3.34 | 4.24 |
| Direct-path fraction | 0.5949 | 0.2540 |
| Relay-path fraction | 0.0000 | 0.0000 |
| Task-support fraction | 0.0014 | 0.0958 |
| Legal-information fraction | 0.5963 | 0.4139 |
| Mean cache age | 35.3955 | 45.9605 |
| Control effort | 1024.20 | 1464.69 |

The F0 expert shows more path switching and control effort, lower direct-path and legal-information fractions, and higher cache age in the pooled diagnostic. These are mechanism diagnostics, not independent evidence of a new algorithmic claim.

## Learning-curve and run validity summary

All final training logs are finite and end at update `1172`. The final diagnostic fields remain stable enough for aggregation, but the two-seed behavior is heterogeneous: seed `1801` favors the nominal expert on failure, while seed `1802` favors the F0 expert. This seed reversal is exactly why the pre-registered rule does not classify the failure condition as clearly learnable.

## Scientific interpretation and boundary

The result closes the current curriculum branch and narrows, but does not solve, the causal question:

```text
F0-only SG failure learnability = NOT DEMONSTRATED
shared nominal/failure interference = NOT ESTABLISHED
```

No claim should be made that nominal–failure policy interference is the confirmed cause. The responsible next diagnostic, if separately authorized, is a formulation audit of temporal partial observability, message age/staleness, post-failure action decisions, and failure-onset behavior using the existing checkpoints and raw timelines where possible. It must not silently become another training round.
