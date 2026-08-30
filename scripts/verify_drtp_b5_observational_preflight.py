"""Pure-Python cloud preflight for the frozen B5 observational cohort."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from run_drtp_b5_observational_single import ARMS, SEEDS, training_config  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    freeze_path = ROOT / "configs" / "drtp_b5_observational_freeze.json"
    tape_path = ROOT / "configs" / "drtp_b5_observational_tape.json"
    seed_path = ROOT / "docs" / "drtp_b5_p1_20260830" / "B5_SEED_PROVENANCE_AUDIT.json"
    p0_path = ROOT / "docs" / "drtp_b5_p0_20260830" / "B5_P0_DECISION.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    tape = json.loads(tape_path.read_text(encoding="utf-8"))
    seeds = json.loads(seed_path.read_text(encoding="utf-8"))
    p0 = json.loads(p0_path.read_text(encoding="utf-8"))
    payload = dict(tape)
    expected_hash = payload.pop("tape_hash")
    actual_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    checks = {
        "p0_pass": p0["decision"].startswith("B5_P0_TECHNICAL_PASS"),
        "clean_seeds": seeds["status"] == "CLEAN" and seeds["archive_count"] == 10,
        "frozen_seeds": tuple(freeze["seeds"]) == SEEDS == tuple(tape["training_seed_namespace"]),
        "frozen_arms": freeze["arms"] == ARMS,
        "exact_budget": freeze["updates"] == 3907 and freeze["environment_steps"] == 1000192,
        "tape_namespace": tape["episode_ids"] == list(range(600000, 600100)),
        "tape_hash": expected_hash == actual_hash,
        "preparation_not_authorization": freeze["training_authorized"] is False,
        "mainline_a_untouched": freeze["mainline_a_modified"] is False,
    }
    with tempfile.TemporaryDirectory() as directory:
        for arm in ARMS:
            for seed in SEEDS:
                cfg = training_config(arm, seed, Path(directory) / arm / str(seed))
                checks[f"config_{arm}_{seed}"] = all([
                    cfg.seed == seed,
                    cfg.drtp_sampler_seed == seed,
                    cfg.drtp_sampler_mode == ARMS[arm],
                    cfg.updates == 3907,
                    cfg.group_credit_telemetry is True,
                    cfg.group_credit_telemetry_interval == 20,
                    cfg.failure_aware_telemetry is True,
                    cfg.evaluation_enabled is False,
                ])
    result = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "freeze_sha256": sha256(freeze_path),
        "tape_sha256": sha256(tape_path),
        "seed_audit_sha256": sha256(seed_path),
        "p0_decision_sha256": sha256(p0_path),
    }
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit("B5 observational preflight failed")


if __name__ == "__main__":
    main()
