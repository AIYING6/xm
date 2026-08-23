# DRTP REL-A0 — Checkpoint Manifest

The machine-readable source of truth is
`artifacts/drtp_reliability_a0/checkpoint_recovery_manifest.json`.

It records all ten archived final checkpoints, their paired seed, 10,000,128
environment steps, 39,063 updates, 116,728 parameters, method configuration
hash, final model SHA256, final runtime-state SHA256, and archive SHA256.

Recovery gate: **PASS — 5/5 complete paired seeds**, exceeding the frozen
minimum of four. No model bytes were modified.
