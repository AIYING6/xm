# Phase 2I-A2 training completion audit

**Artifact class:** DEVELOPMENT_ONLY

Generated: 2026-08-12T12:45:37.994974+00:00

## Result

**PASS** — all six fixed-budget runs are complete and their final artifacts are valid.

## Per-run evidence

| Arm | Seed | Updates | Environment steps | Final checkpoint reload | Checkpoint SHA256 | Telemetry schema | Status |
|---|---:|---:|---:|---|---|---|---|
| full_gate | 101 | 782 | 200192 | True | 4d4e5caab244f6d2f65b78816b3de89454c787b91fba82136f4695d9e13d3d19 | True | PASS |
| full_gate | 202 | 782 | 200192 | True | 7aa4968ab63f568748e5619af8a147a7a83ee7a9e73af2e95d36542f029169b6 | True | PASS |
| full_gate | 303 | 782 | 200192 | True | fc3e9bce4cdf2a1ec18558d2b85b84dfa05d61393f4e43ff6f22c61d1c4b2a8c | True | PASS |
| no_role_gate | 101 | 782 | 200192 | True | 22bfc7a35b0b132ac538f48ad8591dc71ca586bbacbbbe235cb5b6cf7dcee053 | True | PASS |
| no_role_gate | 202 | 782 | 200192 | True | a5aea90f74fabdc6e51df726ade01fdcb8b54be5db1b099e42227a9bad92cd23 | True | PASS |
| no_role_gate | 303 | 782 | 200192 | True | 7751d1fa28cdb6b7e65102f96e9a1df4d9339e1eb27ea9f964349406c68d9e83 | True | PASS |

## Incidents

Recorded incidents: 1. The only recorded incident occurred before any run artifact was created; no completed result was discarded.

## Boundary

This audit does not inspect training performance. Fixed-final-checkpoint development validation may proceed only because this completion audit is PASS.
