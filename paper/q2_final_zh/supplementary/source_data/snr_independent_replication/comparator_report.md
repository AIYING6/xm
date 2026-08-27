# DRTP/SNR Q2 Mechanism Comparator Report

**Verdict:** `NO_CLEAR_MECHANISM_SEPARATION`

Training seed is the independent unit (`n=5`). All 15 final checkpoints and 18,000 scheduled evaluation episodes are retained.

## Technical validity

- complete 18,000 raw records: `PASS`
- risk-set trigger validity: `PASS`

## Paired endpoint evidence

### snr_minus_utr

| endpoint | mean | median | wins/5 | worst reversal |
|---|---:|---:|---:|---:|
| J_nominal | -41.058 | -45.337 | 0/5 | -69.6244 |
| J_F0 | -16.3268 | -31.8087 | 1/5 | -54.037 |
| J_OOD_mean | -22.4856 | -33.4773 | 1/5 | -74.089 |
| J_OOD_worst | -22.348 | -24.5054 | 2/5 | -123.637 |
- primary endpoint directional support: `FAIL`
- catastrophic seeds: `1`

### drtp_minus_snr

| endpoint | mean | median | wins/5 | worst reversal |
|---|---:|---:|---:|---:|
| J_nominal | 2.71056 | 22.9167 | 3/5 | -70.0737 |
| J_F0 | -16.9415 | 4.73388 | 3/5 | -107.537 |
| J_OOD_mean | -11.5855 | 8.27049 | 3/5 | -90.3947 |
| J_OOD_worst | -10.0168 | -12.6425 | 2/5 | -106.999 |
- primary endpoint directional support: `FAIL`
- catastrophic seeds: `2`

### drtp_minus_utr

| endpoint | mean | median | wins/5 | worst reversal |
|---|---:|---:|---:|---:|
| J_nominal | -38.3474 | -27.9621 | 1/5 | -115.411 |
| J_F0 | -33.2682 | -25.1035 | 2/5 | -141.573 |
| J_OOD_mean | -34.0711 | -29.1434 | 2/5 | -123.872 |
| J_OOD_worst | -32.3648 | -51.6616 | 2/5 | -131.504 |
- primary endpoint directional support: `FAIL`
- catastrophic seeds: `1`

Historical held-out findings and the seed2002 catastrophic reversal are retained unchanged. No subsequent training is authorized by this aggregation.
