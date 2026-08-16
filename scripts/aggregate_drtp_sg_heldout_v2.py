"""Apply v2 held-out hard gates; self-reference ratios remain descriptive only."""
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
from run_drtp_sg_heldout_v2_single import ARMS, SEEDS  # noqa: E402


PROTOCOL = "DRTP-SG-MAPPO-HELDOUT-CONFIRMATION-V2-AGGREGATION-V1"
FINAL_LABEL = "10m"


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def render_report(result: dict) -> str:
    final = result["pooled_final"]
    lines = [
        "# DRTP-SG-MAPPO Held-Out Confirmation v2 Report", "",
        f"**Final verdict: `{result['heldout_verdict']}`.**", "",
        "The primary inference unit is the training seed (`n=3`).", "",
        "## Pooled final-10M performance", "",
        "| arm | J nominal | J F0 | J OOD mean | J OOD worst | collision | timeout | constraint | exposure |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm, cell in final.items():
        lines.append(f"| {arm} | {cell['J_nominal']:.6g} | {cell['J_F0']:.6g} | {cell['J_OOD_mean']:.6g} | {cell['J_OOD_worst']:.6g} | {cell['collision_failure_mean']:.6g} | {cell['timeout_failure_mean']:.6g} | {cell['constraint_failure_mean']:.6g} | {cell['failure_exposure_mean']:.6g} |")
    lines += ["", "## v2 hard gates", ""]
    for name, passed in result["hard_gate_rows"].items():
        lines.append(f"- `{name}`: {'PASS' if passed else 'FAIL'}")
    lines += ["", "## Descriptive self-reference diagnostics (not gates)", ""]
    for arm, metrics in result["descriptive_self_reference"].items():
        lines.append(f"- `{arm}`: `R_OOD_mean={metrics['R_OOD_mean']:.6g}`, `R_OOD_worst={metrics['R_OOD_worst']:.6g}`")
    lines += ["", "No canonical, formal five-seed, ablation, or follow-on OOD study is started by this controller.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True)
    args = parser.parse_args()
    tape = json.loads((args.results_root / "heldout_tape_manifest.json").read_text(encoding="utf-8"))
    if tape.get("episode_ids") != list(range(430000, 430100)) or tape.get("canonical") is not False:
        raise RuntimeError("invalid v2 held-out tape")
    expected = [item["name"] for item in tape["conditions"]]
    if expected[:2] != ["nominal", "f0_seen_44_80"] or len(expected) != 12:
        raise RuntimeError("invalid held-out condition table")
    eval_root = args.results_root / "evaluations" / "heldout_v2"
    manifest = json.loads((eval_root / "evaluation_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "completed" or manifest.get("tape_hash") != tape["tape_hash"]:
        raise RuntimeError("incomplete or mismatched held-out evaluation")
    if manifest.get("inference_unit") != "training_seed":
        raise RuntimeError("held-out inference unit must be training_seed")
    rows = base.rows_from(eval_root / "per_seed_condition_summary.csv")
    ood = tuple(expected[2:])
    cells = [base.metrics(rows, arm, seed, FINAL_LABEL, ood) for arm in ARMS for seed in SEEDS]
    write_csv(eval_root / "per_seed_final_metrics.csv", cells)
    by_arm = {arm: [cell for cell in cells if cell["arm"] == arm] for arm in ARMS}
    pooled_final = {arm: base.pooled(by_arm[arm]) for arm in ARMS}
    utr, drtp = pooled_final["utr_sg"], pooled_final["drtp_sg"]
    ratios = {key: drtp[key] / utr[key] if utr[key] else math.nan for key in
              ("J_nominal", "J_F0", "J_OOD_mean", "J_OOD_worst")}
    directions = {key: [next(cell for cell in by_arm["drtp_sg"] if cell["seed"] == seed)[key] -
                        next(cell for cell in by_arm["utr_sg"] if cell["seed"] == seed)[key] for seed in SEEDS]
                  for key in ("J_OOD_mean", "J_OOD_worst")}
    safety = []
    for seed in SEEDS:
        for condition in expected[1:]:
            u = base.condition_row(rows, "utr_sg", seed, FINAL_LABEL, condition)
            d = base.condition_row(rows, "drtp_sg", seed, FINAL_LABEL, condition)
            safety.append({"seed": seed, "condition": condition,
                           "collision_difference": base.value(d, "collision") - base.value(u, "collision"),
                           "timeout_difference": base.value(d, "timeout") - base.value(u, "timeout")})
    gates = {
        "nominal_retention": ratios["J_nominal"] >= .95 and all(
            cell["J_nominal"] / next(ref for ref in by_arm["utr_sg"] if ref["seed"] == cell["seed"])["J_nominal"] >= .90
            for cell in by_arm["drtp_sg"]),
        "F0_retention": ratios["J_F0"] >= .98 and all(
            cell["J_F0"] / next(ref for ref in by_arm["utr_sg"] if ref["seed"] == cell["seed"])["J_F0"] >= .90
            for cell in by_arm["drtp_sg"]),
        "OOD_mean": ratios["J_OOD_mean"] >= 1.05 and sum(delta >= 0 for delta in directions["J_OOD_mean"]) >= 2,
        "OOD_worst": ratios["J_OOD_worst"] >= 1.05 and sum(delta >= 0 for delta in directions["J_OOD_worst"]) >= 2,
        "constraints": drtp["constraint_failure_mean"] == 0.0,
        "collision_safety": drtp["collision_failure_mean"] - utr["collision_failure_mean"] <= .05 and all(row["collision_difference"] <= .10 for row in safety),
        "timeout_safety": drtp["timeout_failure_mean"] - utr["timeout_failure_mean"] <= .05 and all(row["timeout_difference"] <= .10 for row in safety),
        "all_planned_pairs_reported": True,
    }
    verdict = "HELD_OUT_PASS" if all(gates.values()) else "HELD_OUT_FAIL"
    result = {
        "protocol": PROTOCOL, "complete": True, "final_budget": "10m", "tape_hash": tape["tape_hash"],
        "primary_inference_unit": "training_seed", "n_training_seeds": len(SEEDS),
        "pooled_final": pooled_final, "absolute_ratios_drtp_over_utr": ratios,
        "per_seed_directions_drtp_minus_utr": directions, "seed_condition_safety": safety,
        "hard_gate_rows": gates,
        "descriptive_self_reference": {arm: {"R_OOD_mean": pooled_final[arm]["R_OOD_mean"], "R_OOD_worst": pooled_final[arm]["R_OOD_worst"]} for arm in ARMS},
        "self_reference_is_hard_gate": False, "heldout_verdict": verdict,
        "canonical_seeds_used": False, "formal_five_seed_started": False, "ablation_started": False,
        "follow_on_ood_started": False,
    }
    (eval_root / "DRTP_HELDOUT_V2_DECISION.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (eval_root / "DRTP_HELDOUT_V2_REPORT.md").write_text(render_report(result), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
