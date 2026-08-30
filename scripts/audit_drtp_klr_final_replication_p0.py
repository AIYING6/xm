"""Zero-training P0 audit for the one-time exact Full-Rollback KLR replication."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import run_drtp_stable_v2_pilot_single as legacy  # noqa: E402

FREEZE = ROOT / "configs" / "drtp_klr_final_replication_freeze.json"
TAPE = ROOT / "configs" / "drtp_klr_final_replication_tape.json"
SOURCE = ROOT / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py"
TEST = ROOT / "tests" / "test_drtp_stable_v2_kl_guard.py"

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing overwrite: {args.output}")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    text = SOURCE.read_text(encoding="utf-8")
    klr = freeze["arms"]["drtp_klr_sg"]
    checks = {
        "legacy_arm_exact": legacy.ARMS["drtp_klr_sg"] == {"sampler":"drtp", "guard":"post_step_actor_rollback", "target_kl":0.02},
        "frozen_arm_exact": klr == {"sampler":"drtp", "policy_update_guard_mode":"post_step_actor_rollback", "target_kl":0.02},
        "actor_parameters_restored": "agent.actor.load_state_dict(actor_state_before, strict=True)" in text,
        "actor_adam_slots_restored": "_restore_optimizer_parameter_states(optimizer, actor_optimizer_state_before)" in text,
        "critic_step_retained": "critic_step_retained_after_actor_rollback = True" in text,
        "remaining_epochs_stopped": "stop_ppo = True" in text,
        "full_rollout_kl_formula": "current_log_ratio = current_logp - old_logp" in text and "current_kl = ((current_ratio - 1.0) - current_log_ratio).mean()" in text,
        "nonfinite_full_restore": "non-finite Stable-v2 policy update transaction" in text,
        "no_backtrack_selected": klr["policy_update_guard_mode"] != "post_step_actor_backtrack",
        "no_training_authorized": freeze["authorization"]["training_authorized"] is False,
        "no_checkpoint_evaluation_authorized": freeze["authorization"]["checkpoint_evaluation_authorized"] is False,
    }
    run = subprocess.run([sys.executable, "-m", "pytest", "-q", str(TEST.relative_to(ROOT))], cwd=ROOT, text=True, capture_output=True, check=False)
    checks["synthetic_guard_replay"] = run.returncode == 0
    status = "KLR_FINAL_REPLICATION_READY_FOR_AUTHORIZATION" if all(checks.values()) else "KLR_FINAL_REPLICATION_NOT_READY"
    payload = {"status":status,"zero_training":True,"environment_rollout_executed":False,"checkpoint_evaluation_executed":False,"algorithm_modification":False,"checks":checks,"pytest_stdout":run.stdout.strip(),"pytest_stderr":run.stderr.strip(),"hashes":{"freeze":digest(FREEZE),"tape":digest(TAPE),"source":digest(SOURCE),"test":digest(TEST)},"next_action":"human authorization required before any 30-trajectory cloud run"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"status":status,"output":str(args.output)}, ensure_ascii=False))
    raise SystemExit(0 if status.endswith("READY_FOR_AUTHORIZATION") else 1)

if __name__ == "__main__":
    main()
