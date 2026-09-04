# CAPD P0.5 local teacher-asset inventory

**Verdict:** `CAPD_P05_BLOCKED_ASSETS_NOT_LOCAL`.

Found `0/20` required UTR/EGTR teacher runs locally.

A missing local checkpoint is an archival blocker only. It does not mean that the cloud experiment did not run, and it is not evidence against CAPD, EGTR or UTR.

No checkpoint was loaded, no policy output was computed, and no evaluation artifact was read.

## Missing or ambiguous runs

- `utr_sg/seed71011`
- `utr_sg/seed71012`
- `utr_sg/seed71013`
- `utr_sg/seed71014`
- `utr_sg/seed71015`
- `utr_sg/seed71021`
- `utr_sg/seed71022`
- `utr_sg/seed71023`
- `utr_sg/seed71024`
- `utr_sg/seed71025`
- `egtr_sg/seed71011`
- `egtr_sg/seed71012`
- `egtr_sg/seed71013`
- `egtr_sg/seed71014`
- `egtr_sg/seed71015`
- `egtr_sg/seed71021`
- `egtr_sg/seed71022`
- `egtr_sg/seed71023`
- `egtr_sg/seed71024`
- `egtr_sg/seed71025`

## Next boundary

Recover the frozen 10M run assets from the original AutoDL data disk or a previously downloaded result archive. Re-run this inventory against the extracted root. Only an all-complete inventory may proceed to architecture/hash verification and the separately frozen training-only consensus-signal audit.

Student implementation, distillation, PPO training and evaluation remain unauthorized.
