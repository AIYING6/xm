# DRTP/UTR Q2 Formal Seed and Tape Provenance Audit

**Audit base commit:** `46e6d5d`  
**Result:** `PASS_BEFORE_FREEZE`

Before adding the formal confirmation contract, the repository was searched
for semantic training-seed uses matching `seed2301` through `seed2305`, JSON
`"seed": 230x`, and seed assignment forms. No prior training, tuning,
confirmation, or method-selection use was found. Numeric appearances as update
indices, coordinates, metrics, or episode fields are not training-seed uses.

The proposed evaluation namespace `490000–490099` was also searched before
freeze. No prior tape/episode namespace used this range. Historical namespaces
340k–480k remain excluded.

Frozen resources:

- prospective paired training seeds: `2301–2305`;
- prospective formal evaluation tape: `490000–490099`;
- canonical seeds `0–4`: not used;
- historical development/held-out checkpoints: not resumed or promoted.

This audit proves repository provenance available at the audit commit. It does
not claim that a number has never appeared outside the archived project.
