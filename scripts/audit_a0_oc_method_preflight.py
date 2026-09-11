"""Static preflight for the A0 OC-MAPPO development pilot.

This audit deliberately checks the source-level experimental contract before
any multi-seed method run.  It does not assess learning performance.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "a0_oc_method_pilot_v1.json"
RUNNER = ROOT / "scripts" / "run_a0_plain_mappo_pilot.py"
ENVIRONMENT = ROOT / "envs" / "active_perception_tracking_env.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    runner_text = RUNNER.read_text(encoding="utf-8")
    env_text = ENVIRONMENT.read_text(encoding="utf-8")
    ast.parse(runner_text)
    ast.parse(env_text)
    expected_arms = ("plain", "oc", "shuffled_oc", "zero_oc")
    checks = {
        "arms_exact": tuple(config["training_arms"] + [config["implementation_check_arm"]]) == expected_arms,
        "fresh_seed_count_exact": config["training_seeds"] == [99511, 99512, 99513],
        "weight_frozen": config["marginal_weight"] == 0.25 and "MARGINAL_WEIGHT = 0.25" in runner_text,
        "public_belief_credit_present": "marginal_observability_contributions" in env_text,
        "actor_observation_unchanged_by_credit": (
            '"marginal_observability_contributions": marginal_contributions' in env_text
            and "def actor_observation" in env_text
        ),
        "shuffled_credit_has_separate_rng": "credit_rng = np.random.default_rng(seed + 131)" in runner_text,
        "plain_and_zero_credit_are_zero": 'if arm in {"plain", "zero_oc"}' in runner_text,
        "required_telemetry_present": all(item in runner_text for item in config["telemetry_required"]),
        "checkpoint_arm_binding_present": 'checkpoint and requested arm differ' in runner_text,
        "no_truth_credit_token": "target_truth" not in runner_text,
    }
    payload = {
        "protocol": config["protocol"],
        "verdict": "A0_OC_METHOD_PILOT_PREFLIGHT_PASS" if all(checks.values()) else "A0_OC_METHOD_PILOT_PREFLIGHT_FAIL",
        "checks": checks,
        "source_sha256": {"runner": digest(RUNNER), "environment": digest(ENVIRONMENT), "config": digest(CONFIG)},
        "training_started": False,
        "evaluation_started": False,
        "publication_status": config["publication_status"],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
