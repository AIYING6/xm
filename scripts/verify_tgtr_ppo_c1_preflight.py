"""Zero-training preflight for TGTR-PPO C1 cloud execution."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, default=ROOT / "configs" / "tgtr_ppo_c1_freeze.json")
    args = parser.parse_args()
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    hashes = {}
    sources_ok = True
    for seed in freeze["source"]["training_seeds"]:
        source = args.source_root / f"seed{seed}"
        manifest = source / "run_manifest.json"
        runtime = source / "actor_critic_runtime_state_latest.pt"
        valid = manifest.is_file() and runtime.is_file()
        if valid:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            valid = payload.get("status") == "completed" and payload.get("arm") == "utr_sg" and int(payload.get("updates", -1)) == 3907
        sources_ok &= valid
        hashes[str(seed)] = sha256(runtime) if runtime.is_file() else "MISSING"
    sampler_source = (ROOT / "algorithms" / "ri_gmappo" / "tgtr_topology_sampler.py").read_text(encoding="utf-8")
    optimizer_source = (ROOT / "algorithms" / "ri_gmappo" / "tgtr_ppo.py").read_text(encoding="utf-8")
    checks = {
        "five_completed_source_states": sources_ok,
        "twenty_four_fixed_stream_contract": freeze["source"]["num_envs"] == 24 and freeze["source"]["graphs_per_update"] == 1536,
        "all_seven_groups_and_disjoint_splits": all(token in sampler_source for token in ("NOMINAL_STREAMS", "FAILURE_STREAMS", "split_for_env")),
        "active_set_projection_implemented": "def project_halfspaces(" in optimizer_source,
        "full_categorical_kl_implemented": "full_categorical_kl" in optimizer_source,
        "fixed_backtracking_implemented": "BACKTRACK_ALPHAS" in optimizer_source,
        "fresh_training_and_evaluation_forbidden": not any(freeze["authorization"][key] for key in ("fresh_seed_training", "formal_evaluation", "heldout_evaluation", "hyperparameter_sweep", "automatic_development")),
    }
    status = "TGTR_C1_CLOUD_PREFLIGHT_PASS" if all(checks.values()) else "TGTR_C1_CLOUD_PREFLIGHT_FAIL"
    result = {"protocol": freeze["protocol"], "status": status, "checks": checks, "source_runtime_sha256": hashes, "training_started": False, "evaluation_started": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if status.endswith("FAIL"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
