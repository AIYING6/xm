# Phase 2I-A2 development launch record

**Artifact class:** DEVELOPMENT_ONLY  
**Branch:** `scientific_recovery_v2`  
**Commit:** `4df63ec`  
**Tag:** `PHASE2IA2_DEVELOPMENT_READY`  
**Date:** 2026-08-12 (Asia/Shanghai)

## Authority and boundary

This record authorizes exactly six Phase 2I-A2 development runs.  Canonical seeds `0–4`, canonical test IDs, canonical results, primary KM/RMST analysis, checkpoint selection, and Phase 3A are not authorized.

## Runtime host

- Device: NVIDIA GeForce GTX 1650 Ti, 4 GB VRAM (CUDA available).
- Python environment: `D:/Anaconda/envs/.conda/envs/cac/python.exe`.
- Launcher: `scripts/launch_phase2ia2_development.ps1`.
- Validation executor: `scripts/run_phase2ia2_development_validation.py`.

## Frozen arms

| Arm | Config | SHA256 |
|---|---|---|
| `full_gate` | `configs/development/phase2ia2_full_gate.json` | `2ba851d8657a4d75d68d5f81eff17c61c36b181c7d049881d80325d8872a6eb3` |
| `no_role_gate` | `configs/development/phase2ia2_no_role_gate.json` | `15f856af29c6a70b337c237a8d994b878599853f274dee9beaa533516d43934b` |

Seeds are exactly `101, 202, 303`. Each run uses 4 environments × 64 rollout steps × 782 updates = **200,192 environment steps**, no resume, no initialization checkpoint, no early stopping, and fixed final checkpoint `actor_critic_latest.pt`.

## Pre-launch gate

- 44 regression tests: PASS.
- seed-909 performance-suppressed engineering smoke: PASS.
- CUDA deterministic development-validation replay and strict endpoint schema: PASS.
- Arm-config/hash and writable telemetry-directory gate: PASS.

The previous seed-0 smoke deviation remains documented separately. It was not used for any architecture decision; this seed-909 smoke emitted no reward, success, recovery, or episode-performance fields.
