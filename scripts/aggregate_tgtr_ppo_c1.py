"""Apply the frozen TGTR C1 gate to five source-state result files."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GROUPS = ("N", "F0", "TE", "TL", "DS", "DL", "CP")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, default=ROOT / "configs" / "tgtr_ppo_c1_freeze.json")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute required")
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    gate = freeze["gate"]
    report = args.output_root / "diagnostics" / "tgtr_c1_gate"
    report.mkdir(parents=True, exist_ok=False)
    rows = []
    payloads = []
    for seed in freeze["source"]["training_seeds"]:
        payload = json.loads((args.output_root / "runs" / f"seed{seed}" / "TGTR_C1_SOURCE_RESULT.json").read_text(encoding="utf-8"))
        if payload.get("status") != "completed":
            raise RuntimeError(f"incomplete TGTR C1 source state {seed}")
        payloads.append(payload)
        ordinary = payload["ordinary"]["metrics"]["certificate"]
        tgtr = payload["tgtr"]["metrics"]["certificate"]
        harmed = [group for group in GROUPS if ordinary["groups"][group]["surrogate_change"] < 0.0]
        tgtr_group_nonharm = all(tgtr["groups"][group]["surrogate_change"] >= 0.0 for group in GROUPS)
        tgtr_kl_ok = all(tgtr["groups"][group]["full_categorical_kl"] <= payload["tgtr"]["kl_cap"] for group in GROUPS)
        rows.append({
            "seed": seed,
            "ordinary_harmed_groups": ";".join(harmed),
            "ordinary_overall_surrogate": ordinary["overall_surrogate_change"],
            "tgtr_overall_surrogate": tgtr["overall_surrogate_change"],
            "tgtr_group_nonharm": tgtr_group_nonharm,
            "tgtr_pooled_failure_nonharm": tgtr["pooled_failure_surrogate_change"] >= 0.0,
            "tgtr_kl_ok": tgtr_kl_ok,
            "critic_exact": payload["critic_state_exact_vs_ordinary"],
            "nonzero_actor_step": payload["tgtr"]["nonzero_step_count"] > 0,
            "zero_step_fraction": payload["tgtr"]["zero_step_count"] / freeze["source"]["ppo_epochs"],
            "wall_time_ratio": payload["tgtr"]["wall_seconds"] / payload["ordinary"]["wall_seconds"],
            "peak_gpu_memory_bytes": max(payload["tgtr"]["peak_gpu_memory_bytes"], payload["ordinary"]["peak_gpu_memory_bytes"]),
        })
    harm_states = sum(bool(row["ordinary_harmed_groups"]) for row in rows)
    exact_batches = len({payload["batch_sha256"] for payload in payloads}) == len(payloads)
    counts_ok = all(
        payload["group_counts"] == {"N": 768, "F0": 128, "TE": 128, "TL": 128, "DS": 128, "DL": 128, "CP": 128}
        for payload in payloads
    )
    legality = all(
        row["tgtr_group_nonharm"] and row["tgtr_pooled_failure_nonharm"] and row["tgtr_kl_ok"]
        and row["critic_exact"] for row in rows
    )
    nonzero_states = sum(row["nonzero_actor_step"] for row in rows)
    total_zero = sum(payload["tgtr"]["zero_step_count"] for payload in payloads)
    total_epochs = len(payloads) * freeze["source"]["ppo_epochs"]
    overall_noninferior = sum(row["tgtr_overall_surrogate"] >= row["ordinary_overall_surrogate"] for row in rows)
    cost_ok = all(
        row["wall_time_ratio"] <= gate["maximum_wall_time_ratio"]
        and row["peak_gpu_memory_bytes"] <= gate["maximum_peak_gpu_memory_bytes"]
        for row in rows
    )
    checks = {
        "five_exact_complete_batch_pairs": exact_batches and counts_ok,
        "ordinary_harm_actuation_evidence": harm_states >= gate["minimum_ordinary_harm_states"],
        "tgtr_group_certificate_legality": legality,
        "nonzero_actor_step_rate": nonzero_states >= gate["minimum_states_with_nonzero_actor_step"] and total_zero / total_epochs <= gate["maximum_zero_step_fraction"],
        "overall_surrogate_retention": overall_noninferior >= gate["minimum_overall_surrogate_noninferior_states"],
        "cost_and_memory": cost_ok,
        "formal_evaluation_absent": all(not payload["formal_evaluation_used"] for payload in payloads),
    }
    if not checks["ordinary_harm_actuation_evidence"] and all(value for key, value in checks.items() if key != "ordinary_harm_actuation_evidence"):
        verdict = "TGTR_C1_INCONCLUSIVE"
    elif all(checks.values()):
        verdict = "TGTR_C1_MECHANISM_PASS"
    else:
        verdict = "TGTR_C1_NO_GO"
    with (report / "TGTR_C1_SOURCE_SUMMARY.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    decision = {
        "protocol": freeze["protocol"], "verdict": verdict, "checks": checks,
        "ordinary_harm_states": harm_states, "states_with_nonzero_actor_step": nonzero_states,
        "zero_step_fraction": total_zero / total_epochs,
        "overall_surrogate_noninferior_states": overall_noninferior,
        "formal_evaluation_used": False, "algorithm_performance_claim": False,
        "automatic_development_authorized": False,
    }
    (report / "TGTR_C1_GATE_DECISION.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# TGTR-PPO C1 final verdict", "", f"`{verdict}`", "",
        "This is a training-only same-rollout mechanism and cost audit. It is not a policy-performance evaluation.", "",
        "| seed | ordinary harmed groups | ordinary overall | TGTR overall | TGTR group legal | nonzero step | zero-step fraction | wall ratio |",
        "| ---: | :--- | ---: | ---: | :---: | :---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['seed']} | {row['ordinary_harmed_groups'] or 'none'} | {float(row['ordinary_overall_surrogate']):.6g} | "
            f"{float(row['tgtr_overall_surrogate']):.6g} | {row['tgtr_group_nonharm'] and row['tgtr_kl_ok']} | "
            f"{row['nonzero_actor_step']} | {float(row['zero_step_fraction']):.3f} | {float(row['wall_time_ratio']):.3f} |"
        )
    lines.extend(["", f"Checks: `{json.dumps(checks)}`.", "", "No fresh-seed pilot or automatic continuation is authorized."])
    (report / "TGTR_C1_FINAL_VERDICT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
