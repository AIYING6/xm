"""Run the rollout-free DRTP-KLR implementation audit and emit a hashed record."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig


SOURCE = ROOT / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py"
TESTS = [
    ROOT / "tests" / "test_drtp_stable_v2_kl_guard.py",
    ROOT / "tests" / "test_tc_sam.py",
    ROOT / "tests" / "test_drtp_utr_q2_formal.py",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs" / "drtp_stable_v2_d1_20260829" / "STABLE_V2_D1_TECHNICAL_AUDIT.json",
    )
    args = parser.parse_args()
    command = [sys.executable, "-m", "pytest", "-q", *[str(path.relative_to(ROOT)) for path in TESTS]]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    source_text = SOURCE.read_text(encoding="utf-8")
    default_cfg = RIGMAPPOConfig()
    static_checks = {
        "default_guard_is_off": default_cfg.policy_update_guard_mode == "none",
        "actor_parameter_transaction_present": "actor_optimizer_state_before" in source_text,
        "critic_step_is_not_rolled_back_on_kl_rejection": "critic_step_retained_after_actor_rollback = True" in source_text,
        "nonfinite_full_transaction_restore_present": "non-finite Stable-v2 policy update transaction" in source_text,
        "accepted_kl_uses_current_rollout_old_logp": "post_log_ratio = post_logp - old_logp" in source_text,
        "cumulative_intervention_telemetry_present": "policy_guard_cumulative_intervention_rate" in source_text,
    }
    status = "D1_TECHNICAL_PASS" if completed.returncode == 0 and all(static_checks.values()) else "D1_TECHNICAL_FAIL"
    payload = {
        "status": status,
        "zero_training": True,
        "environment_rollout_executed": False,
        "checkpoint_evaluation_executed": False,
        "training_authorized": False,
        "candidate": "DRTP-KLR",
        "guard_mode": "post_step_actor_rollback",
        "target_kl": 0.02,
        "target_kl_formula": "clip_coef ** 2 / 2 with clip_coef=0.2",
        "pytest_command": command,
        "pytest_returncode": completed.returncode,
        "pytest_stdout": completed.stdout.strip(),
        "pytest_stderr": completed.stderr.strip(),
        "static_checks": static_checks,
        "sha256": {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path) for path in [SOURCE, *TESTS]},
        "next_gate": "D2_PILOT_CONTRACT_FREEZE_AND_HUMAN_AUTHORIZATION",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "output": str(args.output)}, ensure_ascii=False))
    raise SystemExit(0 if status == "D1_TECHNICAL_PASS" else 1)


if __name__ == "__main__":
    main()
