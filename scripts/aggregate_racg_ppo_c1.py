"""Apply the frozen RACG C1 mechanism gate to five source-state results."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GROUPS = ("N", "F0", "TE", "TL", "DS", "DL", "CP")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, default=ROOT / "configs" / "racg_ppo_c1_freeze.json")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute required")
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    gate = freeze["gate"]
    report = args.output_root / "diagnostics" / "racg_c1_gate"
    report.mkdir(parents=True, exist_ok=False)
    payloads, rows = [], []
    for seed in freeze["source"]["training_seeds"]:
        payload = json.loads((args.output_root / "runs" / f"seed{seed}" / "RACG_C1_SOURCE_RESULT.json").read_text(encoding="utf-8"))
        if payload.get("status") != "completed":
            raise RuntimeError(f"incomplete RACG C1 source state {seed}")
        payloads.append(payload)
        ordinary = payload["ordinary"]["metrics"]["certificate"]
        racg = payload["racg"]["metrics"]["certificate"]
        ordinary_worst = min(ordinary["groups"][group]["surrogate_change"] for group in GROUPS)
        racg_worst = min(racg["groups"][group]["surrogate_change"] for group in GROUPS)
        max_correction_ratio = max(epoch["correction_ratio"] for epoch in payload["racg"]["epochs"])
        min_nonfreeze_ratio = min(epoch["nonfreeze_ratio"] for epoch in payload["racg"]["epochs"])
        min_realized = min(epoch["realized_actor_displacement_l2"] for epoch in payload["racg"]["epochs"])
        rows.append({
            "seed": seed,
            "ordinary_worst_group_surrogate": ordinary_worst,
            "racg_worst_group_surrogate": racg_worst,
            "worst_group_delta": racg_worst - ordinary_worst,
            "ordinary_overall_surrogate": ordinary["overall_surrogate_change"],
            "racg_overall_surrogate": racg["overall_surrogate_change"],
            "overall_delta": racg["overall_surrogate_change"] - ordinary["overall_surrogate_change"],
            "max_correction_ratio": max_correction_ratio,
            "mean_reliability": sum(epoch["reliability"] for epoch in payload["racg"]["epochs"]) / len(payload["racg"]["epochs"]),
            "min_nonfreeze_ratio": min_nonfreeze_ratio,
            "min_realized_actor_displacement": min_realized,
            "solver_fallback_count": payload["racg"]["solver_fallback_count"],
            "critic_exact": payload["critic_state_exact_vs_ordinary"],
            "wall_time_ratio": payload["racg"]["wall_seconds"] / payload["ordinary"]["wall_seconds"],
            "peak_gpu_memory_bytes": max(payload["racg"]["peak_gpu_memory_bytes"], payload["ordinary"]["peak_gpu_memory_bytes"]),
        })

    tolerance = float(gate["surrogate_numerical_tolerance"])
    expected_counts = {"N": 768, "F0": 128, "TE": 128, "TL": 128, "DS": 128, "DL": 128, "CP": 128}
    material_states = sum(row["max_correction_ratio"] >= gate["material_correction_ratio"] for row in rows)
    harm_reduction_states = sum(row["worst_group_delta"] >= tolerance for row in rows)
    retained_states = sum(row["overall_delta"] >= -tolerance for row in rows)
    checks = {
        "five_exact_complete_batch_pairs": len(payloads) == 5 and all(payload["group_counts"] == expected_counts for payload in payloads),
        "material_nonordinary_correction": material_states >= gate["minimum_material_correction_states"],
        "worst_group_harm_reduction": harm_reduction_states >= gate["minimum_worst_group_harm_reduction_states"],
        "overall_surrogate_retention": retained_states >= gate["minimum_overall_surrogate_retention_states"],
        "nonfreezing_and_realized_motion": all(
            row["min_nonfreeze_ratio"] >= 0.5 - 1e-6
            and row["min_realized_actor_displacement"] > gate["minimum_realized_actor_displacement"]
            for row in rows
        ),
        "critic_exact_vs_ordinary": all(row["critic_exact"] for row in rows),
        "finite_and_solver_safe": all(payload["all_racg_parameters_finite"] and payload["racg"]["zero_realized_step_count"] == 0 for payload in payloads),
        "cost_and_memory": all(row["wall_time_ratio"] <= gate["maximum_wall_time_ratio"] and row["peak_gpu_memory_bytes"] <= gate["maximum_peak_gpu_memory_bytes"] for row in rows),
        "formal_evaluation_absent": all(not payload["formal_evaluation_used"] for payload in payloads),
    }
    verdict = "RACG_C1_MECHANISM_PASS" if all(checks.values()) else "RACG_C1_NO_GO"
    with (report / "RACG_C1_SOURCE_SUMMARY.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    decision = {
        "protocol": freeze["protocol"], "verdict": verdict, "checks": checks,
        "material_correction_states": material_states,
        "worst_group_harm_reduction_states": harm_reduction_states,
        "overall_surrogate_retention_states": retained_states,
        "formal_evaluation_used": False, "algorithm_performance_claim": False,
        "automatic_development_authorized": False,
    }
    (report / "RACG_C1_GATE_DECISION.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# RACG-PPO C1 final verdict", "", f"`{verdict}`", "",
        "This is a training-only same-rollout mechanism and cost audit, not a policy-performance evaluation.", "",
        "| seed | worst-group delta | overall delta | max correction ratio | mean reliability | min liveness ratio | wall ratio |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['seed']} | {row['worst_group_delta']:.6g} | {row['overall_delta']:.6g} | "
            f"{row['max_correction_ratio']:.3f} | {row['mean_reliability']:.3f} | "
            f"{row['min_nonfreeze_ratio']:.3f} | {row['wall_time_ratio']:.3f} |"
        )
    lines.extend(["", f"Checks: `{json.dumps(checks)}`.", "", "No fresh-seed training or automatic continuation is authorized."])
    (report / "RACG_C1_FINAL_VERDICT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
