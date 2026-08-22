# DRTP-SEED-S1-A Run Manifest

Status: `FROZEN — LONG-RUN SCREEN AUTHORIZED`

Protocol: `DRTP-SEED-S1-A-V1`  
Preparation commit: `00e3ccd`  
Diagnostic tape: `440000–440099`  
Budget per run: `5,859 updates × 4 × 64 = 1,499,904 environment steps`  
Total registered maximum: `10,499,328 environment steps`

Registered runs, in fixed order:

1. `R0_G_REFERENCE`
2. `R1_B_REFERENCE`
3. `R2_I_INIT`
4. `R3_I_ENV`
5. `R4_I_ACTION`
6. `R5_I_MINIBATCH`
7. `R6_I_TOPOLOGY`

`R0` and `R1` are diagnostic good/weak anchors. Each intervention differs from `R1` in exactly one non-evaluation stream, and all runs share the same evaluation stream. No selective extension, seed replacement, early stopping, or automatic S1-B is allowed.

The machine-readable tuple matrix is `artifacts/drtp_seed_s1a/s1a_rng_intervention_matrix.json`.

