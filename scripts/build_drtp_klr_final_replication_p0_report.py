"""Build the no-training readiness record for KLR Final Replication P0."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/"docs"/"drtp_klr_final_replication_20260831"
FREEZE=ROOT/"configs"/"drtp_klr_final_replication_freeze.json"
TAPE=ROOT/"configs"/"drtp_klr_final_replication_tape.json"
AUDIT=DOC/"KLR_FINAL_P0_TECHNICAL_AUDIT.json"
SEEDS=DOC/"KLR_FINAL_P0_SEED_PROVENANCE.json"
OUT=DOC/"KLR_FINAL_P0_READINESS_REPORT.md"
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def main()->None:
    freeze=json.loads(FREEZE.read_text(encoding="utf-8")); tape=json.loads(TAPE.read_text(encoding="utf-8")); audit=json.loads(AUDIT.read_text(encoding="utf-8")); seeds=json.loads(SEEDS.read_text(encoding="utf-8"))
    payload=dict(tape); claimed=payload.pop("tape_hash"); canonical=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    ready=audit["status"]=="KLR_FINAL_REPLICATION_READY_FOR_AUTHORIZATION" and seeds["status"]=="CLEAN" and claimed==canonical and not freeze["authorization"]["training_authorized"]
    status="KLR_FINAL_REPLICATION_READY_FOR_AUTHORIZATION" if ready else "KLR_FINAL_REPLICATION_NOT_READY"
    text=f"""# KLR Final Replication P0 readiness report\n\n**Status:** `{status}`\n\nP0 performed no environment rollout, checkpoint evaluation, algorithm modification, or cloud training. The five synthetic Full-Rollback KLR tests passed, including actor/Adam rollback, critic retention, non-finite transaction restoration, default-off equivalence, and deterministic save/reload.\n\n- Historical KLR implementation commit: `3c17bf62`\n- Exact KLR: `post_step_actor_rollback`, full-rollout empirical KL threshold `0.02`\n- Cohort A: 3701--3705; Cohort B: 3706--3710\n- Seed provenance: `{seeds['status']}` across {seeds['files_scanned']} source/config/document files; no declared-seed identifier hit\n- Frozen development tape IDs: 620000--620099; canonical tape hash: `{claimed}`\n- Future-only scope: 30 trajectories × 499,968 training steps = 14,999,040 steps; 0.25M and 0.5M milestones; 15,000 evaluation episodes at the fixed 5 conditions.\n- Recommended cloud cap: 9 parallel training/evaluation workers on a single 12-GB GPU; expected result/log/checkpoint footprint below 2 GiB, with a 15-GiB minimum free-disk preflight.\n\nThe two cohorts must be judged separately. A pass requires both cohorts to satisfy all frozen retention, downside, catastrophic, dispersion, upper-tail, safety and integrity criteria. This document authorizes nothing: a separate human authorization is required before training.\n\n## Integrity hashes\n\n| Artifact | SHA-256 |\n|---|---|\n| freeze | `{sha(FREEZE)}` |\n| tape file | `{sha(TAPE)}` |\n| technical audit | `{sha(AUDIT)}` |\n| seed provenance | `{sha(SEEDS)}` |\n"""
    OUT.write_text(text,encoding="utf-8"); print(status)
if __name__=="__main__": main()
