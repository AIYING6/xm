"""Frozen T4 aggregation for P41 v2 UTR learnability."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.recoverable_service_chain_v2_env import RecoverableServiceChainV2Env
from scripts.p41_v2_rule_task_audit import _actions
from scripts.p41_v2_tapes import scenario_from_dict


SEEDS = (95101, 95102, 95103)


def _family(name: str) -> str:
    if name.startswith("commit_now_"): return "commit_now_like"
    if name.startswith("defer_value_"): return "defer_for_value_like"
    if name.startswith("reroute_"): return "reroute_before_outage_like"
    raise ValueError(f"unknown P41 scenario name: {name}")


def oracle_by_family(tape_path: Path) -> dict[str, float]:
    tape = json.loads(tape_path.read_text(encoding="utf-8"))["episodes"]
    rows = []
    for entry in tape:
        env = RecoverableServiceChainV2Env(scenario_from_dict(entry)); env.reset()
        while not env.done: env.step(_actions(env, "oracle"))
        rows.append((_family(entry["name"]), env.terminal_summary()["completed_value"]))
    return {family: float(np.mean([value for key, value in rows if key == family])) for family in sorted({key for key, _ in rows})}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute: raise SystemExit("refusing to aggregate without --execute")
    diagnostics = args.output_root / "diagnostics"
    diagnostics.mkdir(exist_ok=False)
    oracle = oracle_by_family(args.output_root / "tapes/final_tape.json")
    seed_rows, family_rows = [], []
    for seed in SEEDS:
        utr_summary = json.loads((args.output_root / f"evaluations/utr_seed{seed}/summary.json").read_text(encoding="utf-8"))
        random_summary = json.loads((args.output_root / f"evaluations/random_seed{seed}/summary.json").read_text(encoding="utf-8"))
        episodes = list(csv.DictReader((args.output_root / f"evaluations/utr_seed{seed}/episode_metrics.csv").open(encoding="utf-8")))
        per_family = {family: float(np.mean([float(row["completed_value"]) for row in episodes if _family(row["scenario"]) == family])) for family in oracle}
        for family, value in per_family.items(): family_rows.append({"seed": seed, "family": family, "utr_mean_completed_value": value, "oracle_mean_completed_value": oracle[family]})
        seed_rows.append({
            "seed": seed,
            "utr_mean_completed_value": utr_summary["mean_completed_service_value"],
            "random_mean_completed_value": random_summary["mean_completed_service_value"],
            "uses_service_site_0": int(utr_summary["service_site_0"] > 0),
            "uses_service_site_1": int(utr_summary["service_site_1"] > 0),
            "relay_reconfigurations": utr_summary["relay_reconfigurations"],
            "all_pressure_families_nonzero": int(all(value > 0.0 for value in per_family.values())),
        })
    nominal_learning = sum(row["utr_mean_completed_value"] > row["random_mean_completed_value"] for row in seed_rows) >= 2
    noncollapse = sum(bool(row["all_pressure_families_nonzero"]) for row in seed_rows) >= 2
    nonsaturation = any(row["utr_mean_completed_value"] < float(np.mean(list(oracle.values()))) for row in seed_rows)
    behavioral = all(row["uses_service_site_0"] and row["uses_service_site_1"] and row["relay_reconfigurations"] > 0 for row in seed_rows)
    result = {
        "protocol": "P41-V2-UTR-LEARNABILITY-FREEZE-V1",
        "training_started": True,
        "updates_per_seed": 512,
        "seeds": list(SEEDS),
        "checks": {
            "nominal_learning": nominal_learning,
            "noncollapse": noncollapse,
            "nonsaturation": nonsaturation,
            "behavioral_use": behavioral,
        },
        "seed_rows": seed_rows,
        "oracle_by_pressure_family": oracle,
    }
    result["verdict"] = "P41_V2_T4_PASS" if all(result["checks"].values()) else "P41_V2_T4_STOP"
    with (diagnostics / "P41_V2_T4_SEED_SUMMARY.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=seed_rows[0].keys()); writer.writeheader(); writer.writerows(seed_rows)
    with (diagnostics / "P41_V2_T4_FAMILY_SUMMARY.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=family_rows[0].keys()); writer.writeheader(); writer.writerows(family_rows)
    (diagnostics / "P41_V2_T4_RESULT.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
