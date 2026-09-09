"""Zero-training preflight for the frozen epistemic-commitment P2 pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.epistemic_commitment import parameter_count
from scripts.run_epistemic_commitment_p2_pilot import (
    CommitmentPilotRunner,
    FREEZE_PATH,
    load_freeze,
    run_aggregate,
    run_evaluate,
    run_train,
)


PRIOR_RESULTS = {
    "P1B_ANALYTIC_RESULT.json": "P1B_ANALYTIC_COUNTEREXAMPLE_PASS",
    "P1C_RESULT.json": "P1C_UAV_COMMITMENT_SEMANTIC_PASS",
    "P1D_KERNEL_AUDIT_RESULT.json": "P1D_COMMITMENT_KERNEL_AUDIT_PASS",
    "P1E_RESULT.json": "P1E_TRAINABLE_CONTRACT_AUDIT_PASS",
    "P1F_RESULT.json": "P1F_OBJECTIVE_AND_FAIRNESS_AUDIT_PASS",
    "P1G_RESULT.json": "P1G_LOCAL_OPTIMIZER_AND_RESUME_SMOKE_PASS",
}

SOURCE_FILES = (
    "algorithms/epistemic_commitment.py",
    "algorithms/epistemic_commitment_objective.py",
    "envs/epistemic_commitment_trainable_env.py",
    "envs/epistemic_commitment_uav_shadow_env.py",
    "envs/uav_intercept_3d_env.py",
    "scripts/run_epistemic_commitment_p1g_smoke.py",
    "scripts/run_epistemic_commitment_p2_pilot.py",
    "scripts/verify_epistemic_commitment_p2_preflight.py",
    "scripts/launch_epistemic_commitment_p2_pilot_autodl.sh",
    "configs/epistemic_commitment_p2_pilot_freeze_20260909.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    freeze = load_freeze()
    output = args.output_root / "preflight"
    if output.exists():
        raise FileExistsError(f"refusing to overwrite preflight: {output}")
    for child in ("runs", "evaluations", "diagnostics"):
        if (args.output_root / child).exists():
            raise FileExistsError(f"pilot output already contains {child}")

    evidence_root = ROOT / "docs" / "strong_q2_clean_sheet_p0_20260909"
    prior_checks = {}
    for name, verdict in PRIOR_RESULTS.items():
        value = json.loads((evidence_root / name).read_text(encoding="utf-8"))
        prior_checks[name] = value.get("verdict") == verdict

    package_manifest_path = ROOT / "PACKAGE_MANIFEST.json"
    package_integrity = True
    if package_manifest_path.is_file():
        package_manifest = json.loads(package_manifest_path.read_text(encoding="utf-8"))
        package_integrity = package_manifest.get("protocol") == (
            "EPISTEMIC-COMMITMENT-P2-PILOT-PACKAGE-V1"
        ) and all(
            (ROOT / name).is_file() and sha256(ROOT / name) == expected
            for name, expected in package_manifest.get("files", {}).items()
        )

    candidate = CommitmentPilotRunner(freeze["methods"][0], freeze["training_seeds"][0], freeze)
    baseline = CommitmentPilotRunner(freeze["methods"][1], freeze["training_seeds"][0], freeze)
    dry_root = args.output_root / "__dry_run_only__"
    dry_checks = [
        run_train(freeze["methods"][0], freeze["training_seeds"][0], dry_root, False, False)["status"]
        == "dry_run",
        run_evaluate(freeze["methods"][0], freeze["training_seeds"][0], dry_root, False)["status"]
        == "dry_run",
        run_aggregate(dry_root, False)["status"] == "dry_run",
    ]
    checks = {
        "all_prior_zero_training_gates_pass": all(prior_checks.values()),
        "methods_exact": freeze["methods"]
        == ["information_set_commitment", "capacity_and_risk_matched_recurrent"],
        "fresh_seed_registry_exact": freeze["training_seeds"] == [98101, 98102, 98103],
        "budget_exact": int(freeze["physical_steps_per_run"]) == 1_000_000
        and int(freeze["episodes_per_run"]) == 62_500,
        "total_budget_within_p1d_cap": 2
        * 3
        * int(freeze["physical_steps_per_run"])
        <= 15_000_000,
        "actor_capacity_exact": parameter_count(candidate.actor)
        == parameter_count(baseline.actor)
        == 7_272,
        "dry_run_interfaces_pass": all(dry_checks),
        "fixed_endpoint_only": freeze["fixed_endpoint_only"] is True,
        "checkpoint_selection_forbidden": freeze["checkpoint_selection_forbidden"] is True,
        "package_integrity_if_packaged": package_integrity,
    }
    report = {
        "protocol": "EPISTEMIC-COMMITMENT-P2-PILOT-PREFLIGHT-V1",
        "verdict": "P2_PILOT_PREFLIGHT_PASS" if all(checks.values()) else "P2_PILOT_PREFLIGHT_FAIL",
        "checks": checks,
        "prior_gate_checks": prior_checks,
        "source_sha256": {name: sha256(ROOT / name) for name in SOURCE_FILES},
        "freeze_sha256": sha256(FREEZE_PATH),
        "training_started": False,
        "evaluation_started": False,
        "environment_steps": 0,
        "automatic_continuation": False,
    }
    if args.execute:
        output.mkdir(parents=True)
        (output / "P2_PREFLIGHT_REPORT.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if report["verdict"] != "P2_PILOT_PREFLIGHT_PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
