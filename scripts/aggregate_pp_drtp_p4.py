"""Apply the frozen PP-DRTP P4 independent validation gate without continuation."""
from __future__ import annotations
import argparse, csv, hashlib, json, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARMS = ("utr_sg", "drtp_sg", "pp_drtp_sg")
SEEDS = (3501, 3502, 3503, 3504, 3505)
CONDITIONS = ("nominal", "F0_44_80", "T28_28_80", "D120_44_120", "C28_120")
FAILURES = CONDITIONS[1:]
ENDPOINTS = ("J_nominal", "J_F0", "J_pert_mean", "J_pert_worst")
TAPE = ROOT / "configs" / "pp_drtp_p4_validation_tape.json"
FREEZE = ROOT / "configs" / "pp_drtp_p4_validation_freeze.json"
PROTOCOL = "PP-DRTP-P4-INDEPENDENT-VALIDATION-V1"

def mean(values):
    values = list(values)
    return sum(values) / len(values)

def dispersion(values):
    values = list(values); med = statistics.median(values)
    ordered = sorted(values)
    return {"range": max(values) - min(values), "sample_sd": statistics.stdev(values),
            "mad": statistics.median(abs(value - med) for value in values),
            "iqr": ordered[3] - ordered[1]}

def cell(index, arm, seed):
    rows = index[arm, seed]
    value = lambda condition, key: float(rows[condition][key])
    return {"J_nominal": value("nominal", "J"), "J_F0": value("F0_44_80", "J"),
            "J_pert_mean": mean(value(c, "J") for c in FAILURES),
            "J_pert_worst": min(value(c, "J") for c in FAILURES),
            "collision": mean(value(c, "collision") for c in FAILURES),
            "timeout": mean(value(c, "timeout") for c in FAILURES),
            "constraint_violation": max(value(c, "constraint_violation") for c in FAILURES)}

def retention_ratio(candidate, reference, scale_floor):
    if reference > 0:
        return candidate / reference
    return 1.0 + (candidate - reference) / max(abs(reference), scale_floor)

def catastrophic(candidate, reference, scale_floor):
    f0_ratio = retention_ratio(candidate["J_F0"], reference["J_F0"], scale_floor)
    worst_ratio = retention_ratio(candidate["J_pert_worst"], reference["J_pert_worst"], scale_floor)
    collapse = ((f0_ratio < .70 and worst_ratio < .85) or
                (worst_ratio < .70 and f0_ratio < .85))
    safety_collapse = (candidate["timeout"] - reference["timeout"] > .20 and
                       (f0_ratio < .85 or worst_ratio < .85))
    return collapse or safety_collapse

def probe_integrity(output_root):
    per_seed, total_steps = [], 0
    for seed in SEEDS:
        run = output_root / "runs" / "pp_drtp_sg" / f"seed{seed}"
        probes = list(csv.DictReader((run / "pp_drtp_probe_log.csv").open(newline="", encoding="utf-8")))
        sampler = [row for row in csv.DictReader((run / "drtp_topology_sampler_log.csv").open(newline="", encoding="utf-8"))
                   if row["record_type"] == "weight_update" and row["reason"] == "paired_probe_bounded_exponentiated_gradient"]
        by_update = {}
        for row in probes:
            by_update.setdefault(int(row["update"]), []).append(row)
        exact = bool(by_update) and all(len(rows) == 28 and
            {row["group"] for row in rows} == {"N", "F0", "TE", "TL", "DS", "DL", "CP"} and
            len({row["base_id"] for row in rows}) == 4 and
            all(len({row["initial_state_hash"] for row in rows if row["base_id"] == base}) == 1
                for base in {row["base_id"] for row in rows}) for rows in by_update.values())
        q_nonuniform = 0
        for row in sampler:
            q = [float(row[f"q_{group}"]) for group in ("F0", "TE", "TL", "DS", "DL", "CP")]
            if abs(sum(q) - 1.0) > 1e-9 or min(q) < .05 - 1e-9 or max(q) > .35 + 1e-9:
                exact = False
            q_nonuniform += int(sum(abs(value - 1 / 6) for value in q) > 1e-9)
        steps = sum(int(row["steps"]) for row in probes); total_steps += steps
        per_seed.append({"seed": seed, "probe_boundaries": len(by_update),
                         "probe_records": len(probes), "exact_paired_probe": exact,
                         "nonuniform_boundaries": q_nonuniform, "probe_environment_steps": steps})
    passed = all(row["exact_paired_probe"] and row["probe_boundaries"] > 0 and
                 row["nonuniform_boundaries"] > 0 for row in per_seed)
    return passed, per_seed, total_steps

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute required")
    freeze = json.loads(FREEZE.read_text()); eps = float(freeze["epsilon_J"])
    summary_path = args.output_root / "evaluations" / "final_05m" / "condition_summary.csv"
    rows = list(csv.DictReader(summary_path.open(newline="", encoding="utf-8")))
    if len(rows) != len(ARMS) * len(SEEDS) * len(CONDITIONS):
        raise RuntimeError("invalid P4 condition summary size")
    index = {}
    for row in rows:
        index.setdefault((row["method"], int(row["train_seed"])), {})[row["condition"]] = row
    if any(set(index[arm, seed]) != set(CONDITIONS) for arm in ARMS for seed in SEEDS):
        raise RuntimeError("incomplete P4 condition cells")
    tape_hash = hashlib.sha256(TAPE.read_bytes()).hexdigest()
    freeze_hash = hashlib.sha256(FREEZE.read_bytes()).hexdigest()
    manifest_integrity = True
    for arm in ARMS:
        for seed in SEEDS:
            manifest = json.loads((args.output_root / "runs" / arm / f"seed{seed}" / "run_manifest.json").read_text())
            manifest_integrity &= (manifest.get("protocol") == PROTOCOL and manifest.get("status") == "completed" and
                manifest.get("updates") == 1953 and manifest.get("environment_steps") == 499968 and
                manifest.get("tape_sha256") == tape_hash and manifest.get("freeze_sha256") == freeze_hash and
                manifest.get("checkpoint_selection") == "common_final_500k_only" and
                not manifest.get("early_stopping") and not manifest.get("rerun_authorized"))
    metrics = {arm: {seed: cell(index, arm, seed) for seed in SEEDS} for arm in ARMS}
    seed_rows = []
    for seed in SEEDS:
        utr, original, pp = metrics["utr_sg"][seed], metrics["drtp_sg"][seed], metrics["pp_drtp_sg"][seed]
        condition_safety = []
        for condition in FAILURES:
            u, p = index["utr_sg", seed][condition], index["pp_drtp_sg", seed][condition]
            condition_safety.append({"condition": condition,
                "collision_delta": float(p["collision"]) - float(u["collision"]),
                "timeout_delta": float(p["timeout"]) - float(u["timeout"])})
        seed_rows.append({"seed": seed, "G_original": original["J_pert_mean"] - utr["J_pert_mean"],
            "G_pp": pp["J_pert_mean"] - utr["J_pert_mean"],
            "pp_minus_original": pp["J_pert_mean"] - original["J_pert_mean"],
            "original_catastrophic": catastrophic(original, utr, eps), "pp_catastrophic": catastrophic(pp, utr, eps),
            "condition_safety": condition_safety})
    original_gains = [row["G_original"] for row in seed_rows]
    pp_gains = [row["G_pp"] for row in seed_rows]
    d_original, d_pp = dispersion(original_gains), dispersion(pp_gains)
    endpoint_retention = {endpoint: mean(metrics["pp_drtp_sg"][s][endpoint] for s in SEEDS) >=
        mean(metrics["drtp_sg"][s][endpoint] for s in SEEDS) - eps for endpoint in ENDPOINTS}
    upper = [row for row in seed_rows if row["G_original"] > eps]
    upper_assessable = len(upper) >= int(freeze["minimum_original_upper_tail_seeds"])
    upper_retention = upper_assessable and all(row["pp_minus_original"] >= -eps for row in upper)
    pooled_collision = mean(metrics["pp_drtp_sg"][s]["collision"] - metrics["utr_sg"][s]["collision"] for s in SEEDS)
    pooled_timeout = mean(metrics["pp_drtp_sg"][s]["timeout"] - metrics["utr_sg"][s]["timeout"] for s in SEEDS)
    condition_safe = all(item[key] <= float(freeze["seed_condition_safety_margin"])
        for row in seed_rows for item in row["condition_safety"] for key in ("collision_delta", "timeout_delta"))
    safety = (pooled_collision <= float(freeze["pooled_safety_margin"]) and
              pooled_timeout <= float(freeze["pooled_safety_margin"]) and condition_safe and
              all(metrics["pp_drtp_sg"][s]["constraint_violation"] == 0 for s in SEEDS))
    probe_ok, probe_rows, probe_steps = probe_integrity(args.output_root)
    criteria = {
        "advantage_retention_all_endpoints": all(endpoint_retention.values()),
        "downside_protection": min(pp_gains) - min(original_gains) > eps and
            sum(row["pp_catastrophic"] for row in seed_rows) == 0 and
            sum(row["pp_catastrophic"] for row in seed_rows) <= sum(row["original_catastrophic"] for row in seed_rows),
        "seed_reliability_range_sd": d_pp["range"] < d_original["range"] and d_pp["sample_sd"] < d_original["sample_sd"],
        "direction_consistency": sum(gain >= 0 for gain in pp_gains) >= int(freeze["minimum_nonnegative_pp_gains"]),
        "upper_tail_assessable": upper_assessable, "upper_tail_retention": upper_retention,
        "safety": safety, "integrity": bool(manifest_integrity and probe_ok),
    }
    non_upper = [key for key in criteria if key not in ("upper_tail_assessable", "upper_tail_retention")]
    if all(criteria.values()):
        decision = "P4_EARLY_GO"
    elif all(criteria[key] for key in non_upper) and not upper_assessable:
        decision = "P4_INCONCLUSIVE_UPPER_TAIL"
    else:
        decision = "P4_NO_GO"
    result = {"protocol": freeze["protocol"], "decision": decision, "criteria": criteria,
        "endpoint_retention": endpoint_retention, "seed_results": seed_rows,
        "original_dispersion": d_original, "pp_dispersion": d_pp,
        "original_upper_tail_seed_count": len(upper), "probe_integrity": probe_rows,
        "resource_accounting": {"training_environment_steps": len(ARMS) * len(SEEDS) * 499968,
            "pp_probe_environment_steps": probe_steps,
            "total_environment_interactions": len(ARMS) * len(SEEDS) * 499968 + probe_steps,
            "pp_probe_overhead_fraction_of_pp_training": probe_steps / (len(SEEDS) * 499968)},
        "pooled_safety": {"collision_delta": pooled_collision, "timeout_delta": pooled_timeout},
        "automatic_continuation_started": False}
    report_dir = args.output_root / "diagnostics" / "pp_p4_gate"
    report_dir.mkdir(parents=True, exist_ok=False)
    (report_dir / "PP_P4_GATE_DECISION.json").write_text(json.dumps(result, indent=2) + "\n")
    (report_dir / "PP_P4_SEED_RESULTS.csv").write_text("seed,G_original,G_pp,pp_minus_original,original_catastrophic,pp_catastrophic\n" +
        "\n".join(f'{row["seed"]},{row["G_original"]},{row["G_pp"]},{row["pp_minus_original"]},{row["original_catastrophic"]},{row["pp_catastrophic"]}' for row in seed_rows) + "\n")
    lines = ["# PP-DRTP P4 independent validation gate", "", f"**Decision:** `{decision}`.", "",
             "The independent unit is the training seed (`n=5`); evaluation episodes are paired technical repetitions.", "",
             "```json", json.dumps(criteria, indent=2), "```", "", "No continuation was started."]
    (report_dir / "PP_P4_GATE_REPORT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"decision": decision, "report": str(report_dir / "PP_P4_GATE_REPORT.md")}, indent=2))

if __name__ == "__main__":
    main()
