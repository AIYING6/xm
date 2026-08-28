"""Frozen H2 Stage-1 gate: analyze training telemetry without modifying DRTP."""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import fmean

ARMS = ("utr_sg", "drtp_sg")
SEEDS = (2801, 2802, 2803, 2804, 2805)
UPDATES = 1953
MILESTONES = {976: "0.25M", 1953: "0.50M"}
Q_FIELDS = ("q_F0", "q_TE", "q_TL", "q_DS", "q_DL", "q_CP")


def mean(values: list[float]) -> float:
    finite = [value for value in values if math.isfinite(value)]
    return fmean(finite) if finite else math.nan


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def q_l1(row: dict) -> float:
    return sum(abs(float(row[key]) - 1.0 / 6.0) for key in Q_FIELDS)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute required")
    out, report = args.output_root.resolve(), args.report_dir.resolve()
    # The frozen contract and seed registry are packaged in this directory;
    # only a previous *gate output* constitutes a forbidden overwrite.
    if (report / "H2_05M_GATE_REPORT.md").exists():
        raise FileExistsError(f"refusing to overwrite H2 gate: {report}")
    report.mkdir(parents=True, exist_ok=True)

    logs: dict[tuple[str, int], dict[int, dict]] = {}
    q_by_phase: dict[tuple[str, int, str], list[float]] = defaultdict(list)
    behavior: dict[tuple[str, int], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for arm in ARMS:
        for seed in SEEDS:
            run = out / "runs" / arm / f"seed{seed}"
            manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
            if (manifest.get("status"), manifest.get("environment_steps"), manifest.get("protocol")) != (
                "completed", 499_968, "DRTP-B-LINE-H2-CONFIRMATION-STAGE1-V1"):
                raise RuntimeError(f"invalid H2 Stage-1 run: {run}")
            train = {int(row["update"]): row for row in read_csv(run / "train_log.csv")}
            if any(update not in train for update in MILESTONES):
                raise RuntimeError(f"missing milestone log: {run}")
            logs[(arm, seed)] = train
            for row in read_csv(run / "drtp_topology_sampler_log.csv"):
                if row.get("record_type") != "weight_update":
                    continue
                phase = "0-0.25M" if int(row["update"]) <= 976 else "0.25-0.50M"
                q_by_phase[(arm, seed, phase)].append(q_l1(row))
            event = run / "failure_telemetry" / "failure_event_window.jsonl"
            with event.open(encoding="utf-8") as handle:
                for line in handle:
                    if '"failure_relative_step":60' not in line:
                        continue
                    row = json.loads(line)
                    if int(row["update"]) <= 976:
                        continue
                    state = row["direct_information_path"]["state"]
                    values = behavior[(arm, seed)]
                    values["any_path"].append(float(state in {"direct", "relay"}))
                    values["task_support"].append(float(row["task_support_state"].get("chain_support") or 0.0))
                    values["attack_window"].append(float(max(row.get("attack_window_state") or [0.0])))
                    values["cache_age"].append(float(row["cache_freshness"].get("mean_age") or 0.0))

    temporal_rows: list[dict] = []
    summary: list[dict] = []
    signature_count = 0
    for seed in SEEDS:
        d025, d050 = logs[("drtp_sg", seed)][976], logs[("drtp_sg", seed)][1953]
        u025, u050 = logs[("utr_sg", seed)][976], logs[("utr_sg", seed)][1953]
        vgap = float(d025["value_loss"]) - float(u025["value_loss"])
        kl_ratio = float(d050["approx_kl"]) / max(float(u050["approx_kl"]), 1e-12)
        q_early = mean(q_by_phase[("drtp_sg", seed, "0-0.25M")])
        q_late = mean(q_by_phase[("drtp_sg", seed, "0.25-0.50M")])
        q_shift = q_late - q_early
        dbeh, ubeh = behavior[("drtp_sg", seed)], behavior[("utr_sg", seed)]
        path_gap = mean(dbeh["any_path"]) - mean(ubeh["any_path"])
        support_gap = mean(dbeh["task_support"]) - mean(ubeh["task_support"])
        # Frozen from the observed H2 weak candidate, before new seeds run.
        optimization = vgap >= 0.10 or kl_ratio >= 3.0
        adaptive = q_shift >= 0.20
        support = path_gap <= -0.20 and support_gap <= -0.05
        signature = optimization and adaptive and support
        signature_count += int(signature)
        summary.append({
            "seed": seed, "value_loss_gap_025m_drtp_minus_utr": vgap,
            "approx_kl_ratio_050m_drtp_over_utr": kl_ratio,
            "q_l1_0_025m": q_early, "q_l1_025_050m": q_late, "q_l1_shift": q_shift,
            "tau60_any_path_gap_drtp_minus_utr": path_gap,
            "tau60_task_support_gap_drtp_minus_utr": support_gap,
            "optimization_signature": optimization, "adaptive_signature": adaptive,
            "behavior_support_signature": support, "h2_early_signature": signature,
        })
        temporal_rows.extend([
            {"seed": seed, "layer": "early_optimization", "window": "0.25M", "metric": "value_loss_gap", "value": vgap},
            {"seed": seed, "layer": "adaptive_interaction", "window": "0.25-0.50M", "metric": "q_l1_shift", "value": q_shift},
            {"seed": seed, "layer": "behavior_support", "window": "0.25-0.50M,tau=60", "metric": "any_path_gap", "value": path_gap},
            {"seed": seed, "layer": "behavior_support", "window": "0.25-0.50M,tau=60", "metric": "task_support_gap", "value": support_gap},
        ])
    gate = "H2_EARLY_SIGNATURE_REPLICATED" if signature_count >= 2 else "H2_NO_GO"
    write_csv(report / "h2_05m_seed_summary.csv", summary)
    write_csv(report / "h2_05m_temporal_chain.csv", temporal_rows)
    write_csv(report / "h2_05m_paired_utr_control.csv", summary)
    reason = (
        "At least two of five new DRTP seeds satisfy every preregistered early-state, adaptive-interaction, "
        "and paired-UTR behavior/support criterion. The launcher still stops here; a separately frozen strict "
        "continuation command is required before any 1M execution."
        if gate == "H2_EARLY_SIGNATURE_REPLICATED" else
        "Fewer than two of five new DRTP seeds satisfy the complete frozen signature. H2 is closed; no 1M "
        "continuation, rerun, seed replacement, or DRTP modification is authorized."
    )
    (report / "H2_05M_GATE_REPORT.md").write_text(
        f"# H2 0.5M gate report\n\nStatus: `{gate}`\n\n"
        f"Repeated complete early signatures: `{signature_count}/5`.\n\n{reason}\n",
        encoding="utf-8")
    print(json.dumps({"status": gate, "signature_count": signature_count, "report": str(report)}, indent=2))


if __name__ == "__main__":
    main()
