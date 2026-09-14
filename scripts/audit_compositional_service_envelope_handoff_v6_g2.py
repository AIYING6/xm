"""Frozen V6 G2 learnability gate with stage-stratified behavior checks."""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.timed_handoff_intercept_3d_env import SERVICE_ENVELOPE_PROFILES


PROTOCOL = "COMMITMENT-HANDOFF-3D-V6-G2-LEARNABILITY-AUDIT-V1"
TRAINING_PROTOCOL = "COMMITMENT-HANDOFF-3D-V6-PLAIN-MAPPO-G2-DEVELOPMENT-V1"
# V6.1 is a pre-registered baseline-stability replication: it keeps the
# V6 task, endpoint, and G2 rule fixed, and changes only PPO entropy from
# 0.01 to 0.03 after V6 directly diagnosed deterministic relay-action
# collapse.  It remains development-only and is deliberately reported as a
# distinct source protocol rather than silently treated as V6.
ALLOWED_TRAINING_PROTOCOLS = {
    TRAINING_PROTOCOL,
    "COMMITMENT-HANDOFF-3D-V6.1-PLAIN-MAPPO-G2-DEVELOPMENT-V1",
    "COMMITMENT-HANDOFF-3D-V6.2-PLAIN-MAPPO-G2-DEVELOPMENT-V1",
}
MIN_SUCCESS, MAX_SUCCESS, MIN_SEEDS = 0.10, 0.90, 2
MIN_STAGE_ACTION_SEPARATION = 0.15


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-dir", action="append", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def read_seed(seed_dir: Path) -> tuple[dict[str, object], list[dict[str, str]]]:
    manifest = json.loads((seed_dir / "run_manifest.json").read_text(encoding="utf-8"))
    endpoint = json.loads((seed_dir / "profile_stratified_endpoint.json").read_text(encoding="utf-8"))
    if manifest.get("protocol") not in ALLOWED_TRAINING_PROTOCOLS or manifest.get("status") != "completed":
        raise ValueError(f"{seed_dir}: not a completed registered V6/V6.1 G2 run")
    if endpoint.get("service_envelope_mode") != "compositional_v6_staged" or set(endpoint.get("summary", {})) != set(SERVICE_ENVELOPE_PROFILES):
        raise ValueError(f"{seed_dir}: incomplete V6 profile endpoint")
    with (seed_dir / "profile_stratified_endpoint.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    # The first V6.1 launch began before the runner itself had a distinct
    # manifest label.  Its parent launch manifest was persisted before the
    # child processes wrote their own manifests.  Verify every frozen command
    # rather than retroactively overwriting the child metadata.
    registered_protocol = str(manifest["protocol"])
    parent_launch = seed_dir.parent / "launch_manifest.json"
    if registered_protocol == TRAINING_PROTOCOL and parent_launch.exists():
        entries = json.loads(parent_launch.read_text(encoding="utf-8-sig"))
        matching = [entry for entry in entries if int(entry.get("seed", -1)) == int(manifest["seed"])]
        if len(matching) == 1:
            command = str(matching[0].get("command", ""))
            tokens = {
                "entropy": bool(re.search(r"(?:^|\s)--entropy-coef\s+0\.03(?:\s|$)", command)),
                "mode": bool(re.search(r"(?:^|\s)--service-envelope-mode\s+compositional_v6_staged(?:\s|$)", command)),
                "updates": bool(re.search(r"(?:^|\s)--updates\s+64(?:\s|$)", command)),
                "num_envs": bool(re.search(r"(?:^|\s)--num-envs\s+4(?:\s|$)", command)),
                "rollout": bool(re.search(r"(?:^|\s)--rollout-steps\s+64(?:\s|$)", command)),
            }
            if all(tokens.values()):
                registered_protocol = "COMMITMENT-HANDOFF-3D-V6.1-PLAIN-MAPPO-G2-DEVELOPMENT-V1"
    return {
        "seed": int(manifest["seed"]),
        "summary": endpoint["summary"],
        "training_protocol": registered_protocol,
        "manifest_protocol": str(manifest["protocol"]),
    }, rows


def main() -> None:
    args = parse_args()
    if not args.execute:
        raise SystemExit("pass --execute")
    if args.out_dir.exists() or len(args.seed_dir) != 3:
        raise ValueError("out-dir must be new and exactly three independent V6 seed directories are required")
    seeds, rows = [], []
    for directory in args.seed_dir:
        item, seed_rows = read_seed(directory); seeds.append(item); rows.extend([{**row, "train_seed": item["seed"]} for row in seed_rows])
    if len({item["seed"] for item in seeds}) != 3:
        raise ValueError("duplicate training seed supplied")
    source_protocols = {str(item["training_protocol"]) for item in seeds}
    if len(source_protocols) != 1:
        raise ValueError("all three seeds must originate from one registered V6/V6.1 protocol")
    profiles: dict[str, dict[str, object]] = {}
    future_profiles = []
    for profile in SERVICE_ENVELOPE_PROFILES:
        summaries = [item["summary"][profile] for item in seeds]
        rates = [float(summary["success_rate"]) for summary in summaries]
        future = bool(summaries[0]["future_service_required"])
        profiles[profile] = {
            "future_service_required": int(future),
            "per_seed_success_rate": dict(zip((item["seed"] for item in seeds), rates)),
            "mean_success_rate": sum(rates) / len(rates),
            "moderate_seed_count": sum(MIN_SUCCESS <= rate <= MAX_SUCCESS for rate in rates),
        }
        if future:
            future_profiles.append(profile)
    future_pass = all(int(profiles[p]["moderate_seed_count"]) >= MIN_SEEDS for p in future_profiles)
    pre = [float(item["summary"][p]["mean_prebranch_reconstruct_fraction"]) for item in seeds for p in future_profiles]
    post = [float(item["summary"][p]["mean_postbranch_reconstruct_fraction"]) for item in seeds for p in future_profiles]
    stage_separation = (sum(post) / len(post)) - (sum(pre) / len(pre))
    current_pass = all(float(profiles[p]["mean_success_rate"]) > 0.0 for p in SERVICE_ENVELOPE_PROFILES if not int(profiles[p]["future_service_required"]))
    passed = future_pass and current_pass and stage_separation >= MIN_STAGE_ACTION_SEPARATION
    report = {
        "protocol": PROTOCOL, "artifact_class": "DEVELOPMENT_ONLY_TASK_LEARNABILITY_GATE", "paper_evidence": False,
        "training_seeds": [item["seed"] for item in seeds],
        "source_training_protocol": next(iter(source_protocols)), "profiles": profiles,
        "frozen_future_success_interval": [MIN_SUCCESS, MAX_SUCCESS],
        "frozen_future_requirement": "At least 2/3 seeds in the interval for each future-required profile.",
        "mean_future_prebranch_reconstruct_fraction": sum(pre) / len(pre),
        "mean_future_postbranch_reconstruct_fraction": sum(post) / len(post),
        "stage_action_separation": stage_separation, "minimum_stage_action_separation": MIN_STAGE_ACTION_SEPARATION,
        "verdict": "V6_G2_PLAIN_MAPPO_LEARNABLE_NOT_SATURATED_PASS" if passed else "V6_G2_NOT_YET_ESTABLISHED",
        "interpretation": "A pass permits a candidate-method pilot only; it is not candidate-method or formal paper evidence.",
    }
    args.out_dir.mkdir(parents=True)
    with (args.out_dir / "v6_g2_profile_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    (args.out_dir / "v6_g2_learnability_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
