"""Audit the frozen semantic/adaptive DRTP ablation before any training exists."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "configs" / "drtp_semantic_ablation_freeze_20260907.json"


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-archive", type=Path, default=ROOT / "output" / "DRTP_STABILIZATION_FINAL_CONFIRMATION_10M.zip")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("explicit --execute is required")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    expected_arms = {
        "utr_sg": ("utr", False, False),
        "fixed_drtp_sg": ("fixed_drtp", True, False),
        "random_drtp_sg": ("random_drtp", False, True),
        "drtp_sg": ("drtp", True, True),
    }
    arm_checks = {
        arm: tuple(freeze["arms"][arm][key] for key in ("sampler_mode", "topology_semantic", "adaptive_update")) == expected
        for arm, expected in expected_arms.items()
    }
    source_checks: dict[str, bool] = {}
    if args.source_archive.is_file():
        with ZipFile(args.source_archive) as archive:
            prefixes = {member.split("/", 1)[0] for member in archive.namelist() if "/" in member}
            if len(prefixes) != 1:
                raise RuntimeError("source archive must have exactly one project root")
            prefix = prefixes.pop()
            for relative, expected_hash in freeze["source_members_sha256"].items():
                member = f"{prefix}/{relative}"
                source_checks[relative] = member in archive.namelist() and digest_bytes(archive.read(member)) == expected_hash
    else:
        source_checks = {relative: False for relative in freeze["source_members_sha256"]}
    controls = set(freeze["identical_controls"])
    required_controls = {
        "environment", "PPO", "actor", "critic", "reward", "observation", "action_interface",
        "failure_condition_library", "nominal_mass", "probability_bounds", "training_budget", "endpoint_evaluation_protocol",
    }
    configuration_valid = all(arm_checks.values()) and controls == required_controls and freeze["training"] == {
        "updates": 39063, "num_envs": 4, "rollout_steps": 64, "environment_steps": 10000128,
    }
    source_exact = all(source_checks.values())
    fresh_seed_registry_frozen = isinstance(freeze.get("fresh_seed_registry"), list) and len(freeze["fresh_seed_registry"]) > 0
    report = {
        "protocol": freeze["protocol"],
        "verdict": "DRTP_SEMANTIC_ABLATION_READY_FOR_SEED_FREEZE" if configuration_valid and source_exact and not fresh_seed_registry_frozen else (
            "DRTP_SEMANTIC_ABLATION_READY_FOR_EXECUTION" if configuration_valid and source_exact and fresh_seed_registry_frozen else "DRTP_SEMANTIC_ABLATION_PREFLIGHT_BLOCKED"
        ),
        "configuration_valid": configuration_valid,
        "exact_source_archive_verified": source_exact,
        "fresh_seed_registry_frozen": fresh_seed_registry_frozen,
        "training_authorized": False,
        "evaluation_authorized": False,
        "arm_checks": arm_checks,
        "source_checks": source_checks,
        "only_reset_side_mechanism_varies": True,
        "output_schema": freeze["output_schema"],
        "automatic_algorithm_revision": False,
        "automatic_continuation": False,
    }
    encoded = json.dumps(report, indent=2) + "\n"
    if args.output:
        if args.output.exists():
            raise FileExistsError(f"refusing to overwrite {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")


if __name__ == "__main__":
    main()
