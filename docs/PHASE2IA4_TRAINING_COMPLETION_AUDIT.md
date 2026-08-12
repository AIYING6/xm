# Phase 2I-A4 training completion audit

**Artifact class:** DEVELOPMENT_ONLY

Generated: 2026-08-12T17:51:51.701300+00:00

## Result

**PASS** — six fixed-budget cloud runs completed with reloadable final checkpoints.

## Provenance

- Cloud archive SHA256: `e220e91ba1d560de266ff665e654dce7fb3371b6fc45ecdfbce092736538ff4c`.
- Cloud package contained no `.git` directory; run manifests record `git_sha=packaged-source`. This provenance limitation is retained explicitly.
- Checkpoint hashes and configuration hashes are verified below.

## Per-run evidence

| Arm | Seed | Updates | Steps | Checkpoint reload | Telemetry | SHA256 | Status |
|---|---:|---:|---:|---|---|---|---|
| full_gate | 101 | 3907 | 1000192 | True | True | 3ba615adecd48baad3b91da72155455988338c914ac1fa41a8b2add652a04026 | PASS |
| full_gate | 202 | 3907 | 1000192 | True | True | fdf8833409cec8c6c0ddba90af67b9134dee5fd156d738098a8d11515d05b1ab | PASS |
| full_gate | 303 | 3907 | 1000192 | True | True | d0df7c0d85c3ecb9e958102cc6f522daa65422bc642cbdf584e17e2090120157 | PASS |
| no_role_gate | 101 | 3907 | 1000192 | True | True | a3c50bc931f83c1546f4091d0f977f42fadc0f26c0c7eb052083bb68baee7a8f | PASS |
| no_role_gate | 202 | 3907 | 1000192 | True | True | 44c9b3117086824742b56070e3b0b03443c950d5abdf6ea868c157853978e7a0 | PASS |
| no_role_gate | 303 | 3907 | 1000192 | True | True | f82aebac5b4ccf946cb5c4bb9cafed0fe62f0a0c95d20d5816030f6a965a6a3e | PASS |

## Boundary

This audit inspects completion and artifact integrity only. It does not compare performance. Fixed-final-checkpoint development validation may proceed only because this audit is PASS.
