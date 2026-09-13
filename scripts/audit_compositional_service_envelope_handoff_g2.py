"""Frozen G2 gate for V5 plain-MAPPO service-envelope learning."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from envs.timed_handoff_intercept_3d_env import SERVICE_ENVELOPE_PROFILES


PROTOCOL = "COMMITMENT-HANDOFF-3D-V5-G2-LEARNABILITY-AUDIT-V1"
TRAINING_PROTOCOL = "COMMITMENT-HANDOFF-3D-V5-PLAIN-MAPPO-G2-DEVELOPMENT-V1"
MIN_SUCCESS, MAX_SUCCESS = 0.10, 0.90
MIN_SEEDS = 2
MIN_ACTION_SEPARATION = 0.15


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-dir", action="append", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def read_seed(seed_dir: Path) -> tuple[dict[str, object], list[dict[str, str]]]:
    manifest = json.loads((seed_dir / "run_manifest.json").read_text(encoding="utf-8"))
    endpoint = json.loads((seed_dir / "profile_stratified_endpoint.json").read_text(encoding="utf-8"))
    if manifest.get("protocol") != TRAINING_PROTOCOL or manifest.get("status") != "completed":
        raise ValueError(f"{seed_dir}: not a completed frozen V5 G2 run")
    if endpoint.get("service_envelope_mode") != "compositional_v5" or set(endpoint.get("summary", {})) != set(SERVICE_ENVELOPE_PROFILES):
        raise ValueError(f"{seed_dir}: incomplete V5 profile endpoint")
    with (seed_dir / "profile_stratified_endpoint.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {"seed": int(manifest["seed"]), "summary": endpoint["summary"], "run_dir": str(seed_dir)}, rows


def main() -> None:
    args = parse_args()
    if not args.execute:
        raise SystemExit("pass --execute because this writes a development audit")
    if args.out_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.out_dir}")
    if len(args.seed_dir) < 3:
        raise ValueError("G2 requires three independent training seeds")
    seeds, rows = [], []
    for directory in args.seed_dir:
        item, seed_rows = read_seed(directory)
        seeds.append(item)
        rows.extend([{**row, "train_seed": item["seed"]} for row in seed_rows])
    if len({item["seed"] for item in seeds}) != len(seeds):
        raise ValueError("duplicate training seed supplied")
    profiles: dict[str, dict[str, object]] = {}
    for profile in SERVICE_ENVELOPE_PROFILES:
        rates = [float(item["summary"][profile]["success_rate"]) for item in seeds]
        profiles[profile] = {
            "future_service_required": int(seeds[0]["summary"][profile]["future_service_required"]),
            "per_seed_success_rate": dict(zip((item["seed"] for item in seeds), rates)),
            "mean_success_rate": sum(rates) / len(rates),
            "moderate_seed_count": sum(MIN_SUCCESS <= rate <= MAX_SUCCESS for rate in rates),
        }
    current_actions, future_actions = [], []
    for item in seeds:
        for profile in SERVICE_ENVELOPE_PROFILES:
            value = float(item["summary"][profile]["mean_relay_reconstruct_fraction"])
            (future_actions if int(item["summary"][profile]["future_service_required"]) else current_actions).append(value)
    action_separation = (sum(future_actions) / len(future_actions)) - (sum(current_actions) / len(current_actions))
    profiles_pass = all(int(profiles[p]["moderate_seed_count"]) >= MIN_SEEDS for p in SERVICE_ENVELOPE_PROFILES)
    # A baseline may be imperfect, but it must exploit more than a constant
    # relay commitment if it is to be considered a learnable comparison.
    behavior_pass = action_separation >= MIN_ACTION_SEPARATION
    passed = profiles_pass and behavior_pass
    report = {
        "protocol": PROTOCOL,
        "artifact_class": "DEVELOPMENT_ONLY_TASK_LEARNABILITY_GATE",
        "paper_evidence": False,
        "training_seeds": [item["seed"] for item in seeds],
        "profiles": profiles,
        "frozen_success_interval": [MIN_SUCCESS, MAX_SUCCESS],
        "frozen_requirement": f"At least {MIN_SEEDS}/3 seeds in the interval for every profile.",
        "mean_reconstruct_fraction_current_profiles": sum(current_actions) / len(current_actions),
        "mean_reconstruct_fraction_future_profiles": sum(future_actions) / len(future_actions),
        "reconstruct_action_separation": action_separation,
        "minimum_action_separation": MIN_ACTION_SEPARATION,
        "verdict": "V5_G2_PLAIN_MAPPO_LEARNABLE_NOT_SATURATED_PASS" if passed else "V5_G2_NOT_YET_ESTABLISHED",
        "interpretation": "A pass permits a candidate-method pilot only; it is neither a method result nor formal paper evidence.",
    }
    args.out_dir.mkdir(parents=True)
    with (args.out_dir / "v5_g2_profile_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    (args.out_dir / "v5_g2_learnability_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
