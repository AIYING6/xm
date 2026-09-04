# CAPD P0.5 teacher-asset and consensus-signal audit proposal

**Status:** `PREPARED_NOT_AUTHORIZED`.

## Question

Before implementing or training a student, determine whether the completed
10M UTR/EGTR archive contains a nontrivial, training-only policy-space signal
that CAPD could consolidate.  P0.5 is allowed to answer only:

1. Are all required UTR and EGTR final checkpoints present, hash-valid and
   exactly architecture-compatible?
2. On one newly frozen fixed-stratified **training-only** state tape, do the
   three-member EGTR groups have regions of low policy disagreement where
   their geometric centroid differs materially from the matched UTR anchor?
3. Does the continuous consensus rule remain numerically stable under the
   real action masks and logits?
4. Is the projected teacher-forward cost acceptable on the intended cloud
   device?

## Frozen exclusions

- No formal, independent, held-out or final-outcome tape.
- No return-based teacher selection, ranking or exclusion.
- No final seed-quality labels.
- No student model, distillation loss, PPO update or parameter change.
- No evaluation claim and no paper modification.
- No automatic transition to formula freeze or training.

## Required outputs

- checkpoint inventory with provenance and SHA-256;
- architecture and actor-input compatibility table;
- per-state/per-role categorical probability ledger;
- EGTR centroid disagreement and UTR-distance distributions;
- a cost benchmark that performs forward passes only;
- one terminal verdict:
  - `CAPD_P05_CONSENSUS_SIGNAL_PRESENT`, or
  - `CAPD_P05_NO_USABLE_CONSENSUS_SIGNAL`, or
  - `CAPD_P05_ASSETS_INCOMPLETE`.

Only `CAPD_P05_CONSENSUS_SIGNAL_PRESENT` would justify a later, separately
authorized numeric formula freeze.  It would not establish policy performance.
