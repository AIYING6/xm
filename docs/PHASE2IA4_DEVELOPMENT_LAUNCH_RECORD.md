# Phase 2I-A4 development launch record

- Protocol: `PHASE2IA4_MATURE_POLICY_ROLE_GATE_EFFICACY_PROTOCOL.md`
- Branch: `scientific_recovery_v2`
- Pre-launch commit: `9928d138658d4fdb9c2abe674b1220ec8316b36c`
- Baseline tag: `PHASE2IA4_MATURE_POLICY_BASELINE`
- Development-ready tag: `PHASE2IA4_DEVELOPMENT_READY`
- Host/GPU: configured `cac` environment; launch device `cuda`
- Launcher: `scripts/launch_phase2ia4_development.ps1`
- Output namespace: `results/development/role_gate_phase2ia4/`
- Arms: `full_gate`, `no_role_gate`
- Seeds: `101`, `202`, `303` only
- Updates per run: `3907`
- Environments/rollout: `4 × 64`
- Exact budget per run: `1,000,192` environment steps
- Checkpoint: fixed `actor_critic_latest.pt`
- Configs: `configs/development/phase2ia2_full_gate.json` and `phase2ia2_no_role_gate.json`; hashes are recorded in each run manifest
- Resume: prohibited
- Early stopping: prohibited
- Seed exclusion: prohibited
- Checkpoint promotion: prohibited
- Canonical seeds/test/results: prohibited and unused
- Pre-launch gates: timestep schema PASS; logging invariance PASS; strict endpoint frozen PASS; seed guard PASS; no-resume/early-stop PASS

The launch consists exactly of six fresh DEVELOPMENT_ONLY runs. No outcome-based monitoring or protocol modification is authorized.
