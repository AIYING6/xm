"""Zero-training preflight for the frozen RACG C1 execution."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, default=ROOT / "configs" / "racg_ppo_c1_freeze.json")
    args = parser.parse_args()
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    sources_ok, hashes = True, {}
    for seed in freeze["source"]["training_seeds"]:
        source = args.source_root / f"seed{seed}"
        manifest, runtime = source / "run_manifest.json", source / "actor_critic_runtime_state_latest.pt"
        valid = manifest.is_file() and runtime.is_file()
        if valid:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            valid = payload.get("status") == "completed" and payload.get("arm") == "utr_sg" and int(payload.get("updates", -1)) == 3907
        sources_ok &= valid
        hashes[str(seed)] = sha256(runtime) if runtime.is_file() else "MISSING"
    formula = freeze["formula_freeze"]
    implementation = (ROOT / "algorithms/ri_gmappo/racg_ppo.py").read_text(encoding="utf-8")
    checks = {
        "five_completed_source_states": sources_ok,
        "formula_config_hash_exact": sha256(ROOT / formula["config"]) == formula["config_sha256"],
        "formula_contract_hash_exact": sha256(ROOT / formula["contract"]) == formula["contract_sha256"],
        "twenty_four_fixed_stream_contract": freeze["source"]["num_envs"] == 24 and freeze["source"]["graphs_per_update"] == 1536,
        "continuous_reliability_implemented": "pooled_agreement * np.dot(GROUP_MASSES, agreements)" in implementation,
        "seven_dimensional_solver_implemented": "method=\"SLSQP\"" in implementation,
        "exact_ordinary_fallback_implemented": "ordinary_fallback" in implementation,
        "hard_certificate_and_zero_rejection_absent": not freeze["candidate"]["hard_certificate"] and not freeze["candidate"]["zero_step_rejection"],
        "fresh_training_and_evaluation_forbidden": not any(freeze["authorization"][key] for key in ("fresh_seed_training", "formal_evaluation", "heldout_evaluation", "hyperparameter_sweep", "automatic_development")),
    }
    status = "RACG_C1_PREFLIGHT_PASS" if all(checks.values()) else "RACG_C1_PREFLIGHT_FAIL"
    result = {"protocol": freeze["protocol"], "status": status, "checks": checks, "source_runtime_sha256": hashes, "training_started": False, "evaluation_started": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if status.endswith("FAIL"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
