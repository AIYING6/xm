"""Apply the frozen C1 mechanism gate without using evaluation outcomes."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import statistics


ROOT = Path(__file__).resolve().parents[1]
FAILURE_GROUPS = ("F0", "TE", "TL", "DS", "DL", "CP")


def last_row(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise RuntimeError(f"no rows in {path}")
    return rows[-1]


def as_float(row: dict[str, str], key: str) -> float:
    value = float(row[key])
    if not math.isfinite(value):
        raise RuntimeError(f"non-finite {key}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, default=ROOT / "configs" / "drtp_c1_same_rollout_update_audit_freeze.json")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute required")
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    report_dir = args.output_root / "diagnostics" / "c1_same_rollout_gate"
    if report_dir.exists():
        raise FileExistsError("refusing to overwrite a C1 gate")
    report_dir.mkdir(parents=True, exist_ok=False)
    rows = []
    for seed in freeze["source"]["training_seeds"]:
        root = args.output_root / "runs" / f"seed{seed}"
        manifest = json.loads((root / "c1_manifest.json").read_text(encoding="utf-8"))
        if manifest.get("status") != "completed":
            raise RuntimeError(f"incomplete C1 seed: {seed}")
        ordinary = last_row(root / "ordinary" / "train_log.csv")
        weighted = last_row(root / "weighted" / "train_log.csv")
        if ordinary["group_weighted_actor_batch_sha256"] != weighted["group_weighted_actor_batch_sha256"]:
            raise RuntimeError(f"non-matched rollout for seed {seed}")
        active = [group for group in FAILURE_GROUPS if abs(as_float(weighted, f"group_weight_{group}") - 1.0) > 1e-12]
        if not active:
            raise RuntimeError(f"weighting did not actuate for seed {seed}")
        high = max(active, key=lambda group: float(manifest["lagged_td_abs_scores"][group]))
        high_delta = as_float(weighted, f"post_surrogate_{high}") - as_float(ordinary, f"post_surrogate_{high}")
        nominal_delta = as_float(weighted, "post_surrogate_N") - as_float(ordinary, "post_surrogate_N")
        weighted_kl = as_float(weighted, "post_update_actor_kl")
        ordinary_kl = as_float(ordinary, "post_update_actor_kl")
        dynamics_ok = weighted_kl <= float(freeze["gate"]["maximum_post_update_kl"])
        rows.append({
            "seed": seed, "batch_sha256": ordinary["group_weighted_actor_batch_sha256"],
            "high_group": high, "high_group_surrogate_delta": high_delta,
            "nominal_surrogate_delta": nominal_delta,
            "ordinary_post_update_kl": ordinary_kl, "weighted_post_update_kl": weighted_kl,
            "weight_min": as_float(weighted, "group_weight_min"),
            "weight_max": as_float(weighted, "group_weight_max"),
            "dynamics_ok": dynamics_ok,
        })

    gate = freeze["gate"]
    high_wins = sum(row["high_group_surrogate_delta"] > 0.0 for row in rows)
    nominal_nonharm = sum(row["nominal_surrogate_delta"] >= float(gate["nominal_surrogate_floor"]) for row in rows)
    nominal_floor = all(row["nominal_surrogate_delta"] >= float(gate["absolute_nominal_surrogate_floor"]) for row in rows)
    dynamics = all(row["dynamics_ok"] for row in rows)
    exact_pairs = len(rows) == len(freeze["source"]["training_seeds"])
    actuation = all(row["weight_min"] < 1.0 < row["weight_max"] for row in rows)
    passed = (
        exact_pairs and actuation and dynamics and nominal_floor
        and high_wins >= int(gate["minimum_high_group_surrogate_wins"])
        and nominal_nonharm >= int(gate["minimum_nominal_nonharm_seeds"])
    )
    verdict = "C1_PASS" if passed else "C1_NO_GO"
    checks = {
        "five_exact_batch_pairs": exact_pairs,
        "nonuniform_weight_actuation_in_all_five_pairs": actuation,
        "high_group_surrogate_wins": high_wins >= int(gate["minimum_high_group_surrogate_wins"]),
        "nominal_nonharm": nominal_nonharm >= int(gate["minimum_nominal_nonharm_seeds"]) and nominal_floor,
        "finite_and_bounded_ppo_dynamics": dynamics,
    }
    with (report_dir / "C1_SEED_SUMMARY.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    decision = {
        "protocol": freeze["protocol"], "verdict": verdict, "checks": checks,
        "high_group_surrogate_wins": high_wins, "nominal_nonharm_seeds": nominal_nonharm,
        "independent_unit": gate["independent_unit"], "formal_evaluation_used": False,
        "algorithm_performance_claim": False, "automatic_c2_authorized": False,
    }
    (report_dir / "C1_GATE_DECISION.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    table = "\n".join(
        f"| {row['seed']} | {row['high_group']} | {row['high_group_surrogate_delta']:.6g} | {row['nominal_surrogate_delta']:.6g} | {row['ordinary_post_update_kl']:.6g} | {row['weighted_post_update_kl']:.6g} | {row['weight_min']:.3f}-{row['weight_max']:.3f} |"
        for row in rows
    )
    (report_dir / "C1_GATE_REPORT.md").write_text(
        f"# C1 same-rollout update gate\n\n**Verdict:** `{verdict}`.\n\n"
        "This is a same-rollout local-surrogate mechanism audit, not a policy-performance evaluation. "
        "No formal, independent, or held-out tape was read.\n\n"
        "| Seed | high lagged-TD group | weighted−ordinary high-group surrogate | weighted−ordinary nominal surrogate | ordinary KL | weighted KL | active weight range |\n"
        "| ---: | :--- | ---: | ---: | ---: | ---: | :--- |\n"
        f"{table}\n\n"
        f"- High-group local surrogate wins: `{high_wins}/{len(rows)}` (required `{gate['minimum_high_group_surrogate_wins']}`).\n"
        f"- Nominal non-harm: `{nominal_nonharm}/{len(rows)}` (required `{gate['minimum_nominal_nonharm_seeds']}`; absolute floor `{gate['absolute_nominal_surrogate_floor']}`).\n"
        f"- Checks: `{json.dumps(checks)}`.\n\n"
        "No C2 pilot or longer training is authorized automatically.\n",
        encoding="utf-8",
    )
    print(json.dumps({"verdict": verdict, "report": str(report_dir / "C1_GATE_REPORT.md")}, indent=2))


if __name__ == "__main__":
    main()
