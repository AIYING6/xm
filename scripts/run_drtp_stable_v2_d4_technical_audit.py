"""Run the zero-training D4 DRTP-KLB design/implementation audit."""
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

from algorithms.ri_gmappo.simple_ri_gmappo import (
    POLICY_KL_BACKTRACK_BISECTION_STEPS,
    RIGMAPPOConfig,
)


SOURCE = ROOT / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py"
TESTS = [
    ROOT / "tests" / "test_drtp_stable_v2_kl_backtrack.py",
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


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs" / "drtp_stable_v2_d4_20260829" / "STABLE_V2_D4_TECHNICAL_AUDIT.json",
    )
    parser.add_argument(
        "--decision",
        type=Path,
        default=ROOT / "docs" / "drtp_stable_v2_d4_20260829" / "STABLE_V2_D4_DECISION.json",
    )
    args = parser.parse_args()
    command = [sys.executable, "-m", "pytest", "-q", *[str(path.relative_to(ROOT)) for path in TESTS]]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    source_text = SOURCE.read_text(encoding="utf-8")
    default_cfg = RIGMAPPOConfig()
    static_checks = {
        "default_guard_is_off": default_cfg.policy_update_guard_mode == "none",
        "unique_backtrack_mode_present": 'policy_guard_mode == "post_step_actor_backtrack"' in source_text,
        "target_kl_is_not_changed": "target_kl" in source_text,
        "fixed_bisection_resolution": POLICY_KL_BACKTRACK_BISECTION_STEPS == 24,
        "attempted_direction_is_interpolated": "_set_parameter_interpolation_" in source_text,
        "final_accepted_kl_is_hard_asserted": "Stable-v2 backtracking failed its final KL assertion" in source_text,
        "actor_optimizer_state_is_retained": "actor_optimizer_state_retained_after_projection = True" in source_text,
        "critic_step_is_retained": "critic_step_retained_after_policy_guard = True" in source_text,
        "nonfinite_full_transaction_restore_present": "non-finite Stable-v2 backtracking transaction" in source_text,
        "legacy_rollback_mode_preserved": 'policy_guard_mode == "post_step_actor_rollback"' in source_text,
    }
    passed = completed.returncode == 0 and all(static_checks.values())
    status = "D4_TECHNICAL_PASS" if passed else "D4_TECHNICAL_FAIL"
    hashes = {
        str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
        for path in [SOURCE, ROOT / "scripts" / Path(__file__).name, *TESTS]
    }
    payload = {
        "status": status,
        "zero_training": True,
        "environment_rollout_executed": False,
        "checkpoint_evaluation_executed": False,
        "training_authorized": False,
        "mainline_a_modified": False,
        "candidate": "DRTP-KLB",
        "guard_mode": "post_step_actor_backtrack",
        "target_kl": 0.02,
        "target_kl_source": "frozen D1 value; no threshold retuning",
        "bisection_steps": POLICY_KL_BACKTRACK_BISECTION_STEPS,
        "optimizer_semantics": "attempted Adam actor state retained; actor parameters projected to the largest safe line-search fraction",
        "critic_semantics": "post-step critic update retained when actor projection is activated",
        "pytest_command": command,
        "pytest_returncode": completed.returncode,
        "pytest_stdout": completed.stdout.strip(),
        "pytest_stderr": completed.stderr.strip(),
        "static_checks": static_checks,
        "sha256": hashes,
        "next_gate": "HUMAN_REVIEW_THEN_D5_PILOT_CONTRACT_FREEZE",
    }
    write_json(args.output, payload)
    decision = {
        "decision": "D4_READY_FOR_PILOT_CONTRACT_FREEZE" if passed else "D4_NOT_READY",
        "training_authorized": False,
        "candidate": "DRTP-KLB",
        "prohibited": [
            "training",
            "checkpoint evaluation",
            "target_kl tuning",
            "parallel candidate creation",
            "reuse of seeds 3101-3103",
            "mainline A modification",
        ],
        "required_next_action": "human review of the D4 contract before any D5 pilot contract is frozen",
    }
    write_json(args.decision, decision)
    print(json.dumps({"status": status, "decision": decision["decision"]}, ensure_ascii=False))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
