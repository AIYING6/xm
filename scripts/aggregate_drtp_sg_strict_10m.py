"""Aggregate strict-continuous 0→10M curves and final DRTP retention gates."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import aggregate_drtp_sg_development as base  # noqa: E402
from run_drtp_sg_strict_10m_single import ARMS, MILESTONES, SEEDS  # noqa: E402


PROTOCOL = "DRTP-SG-STRICT-CONTINUOUS-10M-AGGREGATION-V1"
LABELS = tuple(MILESTONES.values())
FULL_MILLION = ("1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m", "10m")


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def relative_growth(before: float, after: float) -> float:
    return (after - before) / (abs(before) + 1e-8)


def metrics_by_label(rows: list[dict], ood: tuple[str, ...]) -> list[dict]:
    return [base.metrics(rows, arm, seed, label, ood) for arm in ARMS for seed in SEEDS for label in LABELS]


def curve_growth(cells: list[dict], arm: str, before_label: str, after_label: str) -> dict:
    before = [cell for cell in cells if cell["arm"] == arm and cell["checkpoint_label"] == before_label]
    after = [cell for cell in cells if cell["arm"] == arm and cell["checkpoint_label"] == after_label]
    by_seed = []
    for seed in SEEDS:
        old = next(cell for cell in before if cell["seed"] == seed)["J_OOD_worst"]
        new = next(cell for cell in after if cell["seed"] == seed)["J_OOD_worst"]
        by_seed.append({"seed": seed, "before": old, "after": new,
                        "relative_improvement": relative_growth(old, new), "non_negative": new >= old})
    old_pool = base.pooled(before)["J_OOD_worst"]
    new_pool = base.pooled(after)["J_OOD_worst"]
    pooled_relative = relative_growth(old_pool, new_pool)
    return {
        "from": before_label, "to": after_label, "pooled_before": old_pool,
        "pooled_after": new_pool, "pooled_relative_improvement": pooled_relative,
        "per_seed": by_seed,
        "continuing_growth": pooled_relative >= 0.05 and all(item["non_negative"] for item in by_seed),
    }


def first_stable_plateau(intervals: list[dict]) -> str | None:
    for index in range(1, len(intervals)):
        if not intervals[index - 1]["continuing_growth"] and not intervals[index]["continuing_growth"]:
            return intervals[index]["to"]
    return None


def render_report(result: dict) -> str:
    final = result["pooled_final"]
    lines = [
        "# DRTP Strict-Continuous 0→10M Development Report", "",
        f"**Final development verdict: `{result['development_verdict']}`.**", "",
        "## Final 10M pooled metrics", "",
        "| arm | J nominal | J F0 | J OOD mean | J OOD worst | collision | timeout | constraint | exposure |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm, cell in final.items():
        lines.append(
            f"| {arm} | {cell['J_nominal']:.6g} | {cell['J_F0']:.6g} | {cell['J_OOD_mean']:.6g} | "
            f"{cell['J_OOD_worst']:.6g} | {cell['collision_failure_mean']:.6g} | "
            f"{cell['timeout_failure_mean']:.6g} | {cell['constraint_failure_mean']:.6g} | "
            f"{cell['failure_exposure_mean']:.6g} |"
        )
    lines += ["", "## Maturity", ""]
    for arm, maturity in result["maturity"].items():
        lines.append(f"- `{arm}` first stable plateau: `{maturity['first_stable_plateau']}`.")
    lines.append(f"- 8M→9M→10M maturity unresolved: `{result['maturity_unresolved_at_le_10m']}`.")
    lines += ["", "## Retention matrix", ""]
    for name, passed in result["development_gate_rows"].items():
        lines.append(f"- `{name}`: {'PASS' if passed else 'FAIL'}")
    lines += ["", "Held-out, canonical, and any further training are not started by this controller.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True)
    args = parser.parse_args()
    tape = json.loads((args.results_root / "tape_manifest.json").read_text(encoding="utf-8"))
    if tape.get("episode_ids") != list(range(420000, 420100)) or tape.get("canonical") is not False:
        raise RuntimeError("invalid frozen development tape")
    expected = [item["name"] for item in tape["conditions"]]
    if expected[:2] != ["nominal", "f0_seen_44_80"] or len(expected) != 12:
        raise RuntimeError("invalid frozen condition table")
    eval_root = args.results_root / "evaluations" / "strict_10m"
    manifest = json.loads((eval_root / "evaluation_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "completed" or manifest.get("tape_hash") != tape["tape_hash"]:
        raise RuntimeError("incomplete strict-10M evaluation")
    rows = base.rows_from(eval_root / "per_seed_condition_summary.csv")
    cells = metrics_by_label(rows, tuple(expected[2:]))
    write_csv(eval_root / "per_seed_curve_metrics.csv", cells)
    pooled_curve = []
    for arm in ARMS:
        for label in LABELS:
            pooled_curve.append({"arm": arm, "checkpoint_label": label,
                                 **base.pooled([cell for cell in cells if cell["arm"] == arm and cell["checkpoint_label"] == label])})
    write_csv(eval_root / "pooled_curve_metrics.csv", pooled_curve)
    maturity = {}
    for arm in ARMS:
        intervals = [curve_growth(cells, arm, FULL_MILLION[index - 1], FULL_MILLION[index])
                     for index in range(1, len(FULL_MILLION))]
        maturity[arm] = {"primary_metric": "J_OOD_worst", "intervals": intervals,
                         "first_stable_plateau": first_stable_plateau(intervals)}
    unresolved = any(
        next(item for item in maturity[arm]["intervals"] if item["to"] == "9m")["continuing_growth"]
        and next(item for item in maturity[arm]["intervals"] if item["to"] == "10m")["continuing_growth"]
        for arm in ARMS
    )
    final_by_arm = {arm: [cell for cell in cells if cell["arm"] == arm and cell["checkpoint_label"] == "10m"] for arm in ARMS}
    pooled_final = {arm: base.pooled(final_by_arm[arm]) for arm in ARMS}
    utr, drtp = pooled_final["utr_sg"], pooled_final["drtp_sg"]
    ratios = {key: drtp[key] / utr[key] if utr[key] else math.nan for key in
              ("J_nominal", "J_F0", "J_OOD_mean", "J_OOD_worst", "R_OOD_mean", "R_OOD_worst")}
    directions = {key: [next(cell for cell in final_by_arm["drtp_sg"] if cell["seed"] == seed)[key] -
                        next(cell for cell in final_by_arm["utr_sg"] if cell["seed"] == seed)[key] for seed in SEEDS]
                  for key in ("J_OOD_mean", "J_OOD_worst")}
    safety = []
    for seed in SEEDS:
        for condition in expected[1:]:
            u = base.condition_row(rows, "utr_sg", seed, "10m", condition)
            d = base.condition_row(rows, "drtp_sg", seed, "10m", condition)
            safety.append({"seed": seed, "condition": condition,
                           "collision_difference": base.value(d, "collision") - base.value(u, "collision"),
                           "timeout_difference": base.value(d, "timeout") - base.value(u, "timeout")})
    gates = {
        "nominal_retention": ratios["J_nominal"] >= .95 and all(
            cell["J_nominal"] / next(ref for ref in final_by_arm["utr_sg"] if ref["seed"] == cell["seed"])["J_nominal"] >= .90
            for cell in final_by_arm["drtp_sg"]),
        "F0_retention": ratios["J_F0"] >= .98 and all(
            cell["J_F0"] / next(ref for ref in final_by_arm["utr_sg"] if ref["seed"] == cell["seed"])["J_F0"] >= .90
            for cell in final_by_arm["drtp_sg"]),
        "OOD_mean": ratios["J_OOD_mean"] >= 1.05 and all(delta >= 0 for delta in directions["J_OOD_mean"]),
        "OOD_worst": ratios["J_OOD_worst"] >= 1.05 and all(delta >= 0 for delta in directions["J_OOD_worst"]),
        "self_reference": ratios["R_OOD_mean"] >= 1.0 and ratios["R_OOD_worst"] >= 1.0,
        "constraints": drtp["constraint_failure_mean"] == 0.0,
        "collision_safety": drtp["collision_failure_mean"] - utr["collision_failure_mean"] <= .05 and all(row["collision_difference"] <= .10 for row in safety),
        "timeout_safety": drtp["timeout_failure_mean"] - utr["timeout_failure_mean"] <= .05 and all(row["timeout_difference"] <= .10 for row in safety),
        "all_planned_pairs_reported": True,
    }
    retention_pass = all(gates.values())
    if unresolved:
        verdict = "TRAINING_MATURITY_UNRESOLVED_AT_LE_10M"
    elif retention_pass:
        verdict = "DEVELOPMENT_RETENTION_PASS_HELD_OUT_REQUIRES_SEPARATE_AUTHORIZATION"
    else:
        verdict = "DEVELOPMENT_RETENTION_NO_GO"
    result = {
        "protocol": PROTOCOL, "complete": True, "final_budget": "10m", "tape_hash": tape["tape_hash"],
        "primary_maturity_metric": "J_OOD_worst", "maturity": maturity,
        "maturity_unresolved_at_le_10m": unresolved, "pooled_final": pooled_final,
        "performance_at": {label: {arm: base.pooled([cell for cell in cells if cell["arm"] == arm and cell["checkpoint_label"] == label]) for arm in ARMS}
                           for label in ("1m", "3m", "5m", "10m")},
        "ratios_drtp_over_utr": ratios, "per_seed_ood_directions_drtp_minus_utr": directions,
        "seed_condition_safety": safety, "development_gate_rows": gates,
        "development_verdict": verdict, "held_out_started": False, "canonical_seeds_used": False,
    }
    (eval_root / "DRTP_STRICT_10M_DEVELOPMENT_DECISION.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (eval_root / "DRTP_STRICT_10M_DEVELOPMENT_REPORT.md").write_text(render_report(result), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
