"""Zero-training integrity check for the frozen final DRTP confirmation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import make_env  # noqa: E402
from scripts.create_drtp_stabilization_confirmatory_tape import payload as tape_payload  # noqa: E402
from scripts.run_drtp_stabilization_confirmatory_single import ARMS, SEEDS, STEPS, UPDATES, training_config  # noqa: E402
from scripts.drtp_stabilization_confirmation_contracts import cohort_names, cohort_spec  # noqa: E402


PROTOCOL = "DRTP-STABILIZATION-FINAL-CONFIRMATION-PREFLIGHT-V1"
EVIDENCE = ROOT / "configs" / "drtp_stabilization_final_development_evidence.json"
HISTORICAL = {
    *range(1901, 1903), *range(2001, 2004), *range(2301, 2306), *range(2401, 2406),
    2501, 2502, 2503, 2701, 2702, 2703,
    *range(5101, 5111), *range(6201, 6204), *range(65011, 65016), *range(66011, 66016),
    *range(67011, 67016), *range(68011, 68016), *range(71011, 71016), *range(71021, 71026),
    75011, 75012, 75013, 76011, 76012, 76013,
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "package-provenance-only"


def config_hash() -> str:
    config = dict(training_config("global_anchored_egtr_a075_sg", SEEDS[0], Path("frozen-output")).__dict__)
    for key in ("seed", "drtp_sampler_seed", "out_dir", "device"):
        config.pop(key)
    return hashlib.sha256(json.dumps(config, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", choices=cohort_names(), default="A")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("explicit --execute is required")
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_root}")
    spec = cohort_spec(args.cohort)
    freeze = spec["freeze"]
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    prior_seeds = set(HISTORICAL)
    if args.cohort == "B":
        prior_seeds.update(cohort_spec("A")["seeds"])
    if freeze["final_method"]["anchor_alpha"] != 0.75 or freeze["final_method"]["sampler_mode"] != "anchored_egtr":
        raise RuntimeError("final alpha or sampler mode differs from the freeze")
    if set(freeze["frozen_training"]["arms"]) != set(ARMS):
        raise RuntimeError("freeze seed or arm surface differs from source runner")
    if set(spec["seeds"]) & prior_seeds:
        raise RuntimeError("confirmatory seed overlap with a retained historical training seed")
    if evidence["development_seeds"] != [76011, 76012, 76013] or set(spec["seeds"]) & set(evidence["development_seeds"]):
        raise RuntimeError("confirmation reuses a development seed")
    config = training_config("global_anchored_egtr_a075_sg", spec["seeds"][0], Path("frozen-output"))
    env = make_env(config, spec["seeds"][0], training=True)
    obs, share, graph = env.reset()
    checks = {
        "fresh_training_seeds": len(set(spec["seeds"])) == 5 and not (set(spec["seeds"]) & prior_seeds),
        "development_seeds_excluded": not (set(spec["seeds"]) & set(evidence["development_seeds"])),
        "four_matched_arms": set(ARMS) == {"utr_sg", "drtp_sg", "egtr_sg", "global_anchored_egtr_a075_sg"},
        "final_alpha_exact": config.drtp_sampler_anchor_alpha == 0.75,
        "mature_budget_exact": UPDATES == 39063 and STEPS == 10000128,
        "endpoint_only": config.evaluation_enabled is False and config.save_snapshots is False,
        "single_graph_interface": config.graph_encoder == "single" and obs.shape[-1] > 0 and share.shape[-1] > 0 and graph["node_feat"].shape[-1] > 0,
        "fresh_tape_payload": tape_payload(args.cohort)["episode_ids"] == spec["episode_ids"],
        "algorithm_source_present": (ROOT / "algorithms" / "ri_gmappo" / "drtp_topology_sampler.py").is_file(),
    }
    if not all(checks.values()):
        raise RuntimeError(f"preflight check failure: {checks}")
    args.output_root.mkdir(parents=True, exist_ok=False)
    source_hashes = {
        "sampler": digest(ROOT / "algorithms" / "ri_gmappo" / "drtp_topology_sampler.py"),
        "learner": digest(ROOT / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py"),
        "environment": digest(ROOT / "envs" / "uav_intercept_3d_env.py"),
        "freeze": digest(spec["freeze_path"]), "development_evidence": digest(EVIDENCE), "ppo_config": config_hash(),
    }
    protocol = PROTOCOL if args.cohort == "A" else "DRTP-STABILIZATION-INDEPENDENT-REPLICATION-PREFLIGHT-V1"
    verdict = "CONFIRMATORY_PREFLIGHT_PASS" if args.cohort == "A" else "INDEPENDENT_REPLICATION_PREFLIGHT_PASS"
    seeds = {"protocol": protocol, "cohort": args.cohort, "training_seeds": list(spec["seeds"]), "excluded_development_seeds": evidence["development_seeds"], "historical_overlap": False, "seed_replacement_forbidden": True}
    record = {"protocol": protocol, "cohort": args.cohort, "verdict": verdict, "checks": checks, "source_commit": source_commit(), "source_sha256": source_hashes, "final_method": freeze["final_method"], "training": freeze["frozen_training"], "evaluation": freeze["evaluation"], "training_started": False, "evaluation_started": False, "automatic_training": False, "automatic_algorithm_revision": False, "automatic_6uav": False}
    (args.output_root / "CONFIRMATORY_SEEDS.json").write_text(json.dumps(seeds, indent=2) + "\n", encoding="utf-8")
    (args.output_root / "DRTP_STABILIZATION_FINAL_FREEZE.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    (args.output_root / "CONFIRMATORY_PREFLIGHT.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    (args.output_root / "CONFIRMATORY_PREFLIGHT.md").write_text(f"# DRTP cohort {args.cohort} preflight\n\n**Verdict:** `{verdict}`.\n\nThis is a zero-training, zero-evaluation validation of the frozen final method, fresh seed contract and endpoint protocol.\n", encoding="utf-8")
    print(json.dumps(record, indent=2), flush=True)


if __name__ == "__main__":
    main()
