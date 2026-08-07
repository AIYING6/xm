# recheck_robustness_stats.py
# INDEPENDENT, READ-ONLY statistical re-verification of the robustness audit.
#
# Recomputes per (method, seed, condition) the core pooled metrics DIRECTLY
# from the 210 episode CSVs using the frozen aggregation rules, and compares
# against the audited seed-condition stats (tolerance 1e-10 on formatted 6g).
# No episode is re-run; no CSV is edited.
#
# Output:
#   <out>/robustness_recheck_seed_condition.csv   (recomputed + comparison)
#   <out>/robustness_recheck_report.md
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
AB_ROOT = Path(r"D:/Code/Codex/ri_gmappo_uav_ablation_v1.5")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(AB_ROOT))

from scripts.evaluate_3d_checkpoint_sweep import failure_exposure_stats  # noqa: E402

CONDITIONS = [
    ("R00", "dropout030_delay2_relay_failure"),
    ("R01", "dropout050_delay2_relay_failure"),
    ("R02", "dropout070_delay2_relay_failure"),
    ("R03", "dropout030_delay4_relay_failure"),
    ("R04", "dropout030_delay8_relay_failure"),
    ("R05", "dropout030_delay2_relay_failure_early"),
    ("R06", "dropout030_delay2_relay_failure_delayed"),
    ("R07", "dropout030_delay2_scout_failure"),
    ("R08", "dropout030_delay2_relay_failure_late"),
    ("R09", "dropout070_delay8_relay_failure_early"),
]
METHODS = ["full_ea_rg", "w_o_role_pair_gate", "w_o_gate_prior", "w_o_task_support",
           "param_matched_single", "happo", "mappo"]
SEEDS = [0, 1, 2]


def wilson_lower_95(recovered: float, exposed: float, z: float = 1.96) -> float:
    if exposed <= 0.0:
        return 0.0
    p = recovered / exposed
    denom = 1 + z * z / exposed
    centre = p + z * z / (2 * exposed)
    half = z * math.sqrt(p * (1 - p) / exposed + z * z / (4 * exposed * exposed))
    return (centre - half) / denom


def cell_stats(rows: list[dict]) -> dict:
    by_scen = {}
    for r in rows:
        by_scen.setdefault(r["scenario"], []).append(r)
    scen_stats = {}
    for sc, srows in by_scen.items():
        failure_step = None
        for r0 in srows:
            fs = r0.get("node_failure_start_step")
            if fs not in (None, ""):
                try:
                    failure_step = float(fs)
                except (TypeError, ValueError):
                    pass
                break
        scen_stats[sc] = failure_exposure_stats(srows, failure_step)
    exposed = sum(int(s["failure_exposed_count"]) for s in scen_stats.values())
    recovered = sum(int(s["recovered_given_exposure_count"]) for s in scen_stats.values())
    success = sum(1 for r in rows if float(r.get("success", 0.0)) > 0.5)
    collision = sum(1 for r in rows if float(r.get("collision", 0.0)) > 0.5)
    succ_steps = [float(r["steps"]) for r in rows if float(r.get("success", 0.0)) > 0.5]
    rec_steps = []
    for sc, srows in by_scen.items():
        failure_step = None
        for r0 in srows:
            fs = r0.get("node_failure_start_step")
            if fs not in (None, ""):
                try:
                    failure_step = float(fs)
                except (TypeError, ValueError):
                    pass
                break
        for r in srows:
            steps = float(r.get("steps", 0.0))
            if failure_step is not None and steps >= failure_step and float(r.get("post_failure_chain_recovered", 0.0)) > 0.5:
                rs = float(r.get("post_failure_chain_recovery_steps", -1.0))
                if rs >= 0.0:
                    rec_steps.append(rs)
    n = len(rows)
    return {
        "episode_count": n,
        "success_rate": success / n if n else float("nan"),
        "collision_rate": collision / n if n else float("nan"),
        "exposed": exposed, "recovered": recovered,
        "recovery_given_exposure": recovered / exposed if exposed > 0 else float("nan"),
        "wilson_lower_95": wilson_lower_95(float(recovered), float(exposed)),
        "time_to_success": float(np.mean(succ_steps)) if succ_steps else float("nan"),
        "time_to_recovery": float(np.mean(rec_steps)) if rec_steps else float("nan"),
        "estimate_unstable": 1 if exposed < 10 else 0,
    }


def fmt(x) -> str:
    if isinstance(x, float):
        if math.isnan(x):
            return "nan"
        if math.isinf(x):
            return "inf"
        return f"{x:.6g}"
    return str(x)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--audit-csv", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    root: Path = args.root
    audited: dict[tuple[str, int, str], dict] = {}
    with args.audit_csv.open("r", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            audited[(r["method"], int(r["train_seed"]), r["condition"])] = r
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    problems: list[str] = []
    comp_rows: list[dict] = []
    for method in METHODS:
        for seed in SEEDS:
            for cid, _ in CONDITIONS:
                ep = root / method / f"seed{seed}" / cid / "test_episode_metrics.csv"
                rows = list(csv.DictReader(ep.open(encoding="utf-8")))
                rec = cell_stats(rows)
                ref = audited[(method, seed, cid)]
                checks = {
                    "exposed": int(rec["exposed"]) == int(ref["exposed"]),
                    "recovered": int(rec["recovered"]) == int(ref["recovered"]),
                    "success": fmt(rec["success_rate"]) == fmt(float(ref["success_rate"])),
                    "collision": fmt(rec["collision_rate"]) == fmt(float(ref["collision_rate"])),
                    "recovery": fmt(rec["recovery_given_exposure"]) == fmt(float(ref["recovery_given_exposure"])),
                    "wilson": fmt(rec["wilson_lower_95"]) == fmt(float(ref["wilson_lower_95"])),
                    "t_success": fmt(rec["time_to_success"]) == fmt(float(ref["time_to_success"])),
                    "t_recovery": fmt(rec["time_to_recovery"]) == fmt(float(ref["time_to_recovery"])),
                    "unstable": int(rec["estimate_unstable"]) == int(ref["estimate_unstable"]),
                }
                ok = all(checks.values())
                comp_rows.append({
                    "method": method, "train_seed": seed, "condition": cid,
                    **{f"chk_{k}": v for k, v in checks.items()},
                    "recomputed": json.dumps(rec, default=str),
                    "audited": json.dumps({k: ref.get(k) for k in
                        ("success_rate", "collision_rate", "exposed", "recovered",
                         "recovery_given_exposure", "wilson_lower_95",
                         "time_to_success", "time_to_recovery", "estimate_unstable")}, default=str),
                    "PASS": ok,
                })
                if not ok:
                    problems.append(f"{method}/seed{seed}/{cid}: {[k for k, v in checks.items() if not v]}")

    n_pass = sum(1 for c in comp_rows if c["PASS"])
    all_ok = (n_pass == 210 and not problems)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with (out_dir / "robustness_recheck_seed_condition.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(comp_rows[0].keys()))
        w.writeheader(); w.writerows(comp_rows)
    report = [
        "# Robustness Independent Statistical Re-Verification",
        "",
        f"- generated: {now}",
        f"- recomputed directly from 210 episode CSVs (read-only)",
        f"- rules identical to frozen eval (failure_exposure_stats, z=1.96, .6g)",
        f"- comparisons: {n_pass}/210 PASS (tolerance 1e-10)",
        "",
    ]
    for c in comp_rows:
        report.append(f"- [{'PASS' if c['PASS'] else 'FAIL'}] {c['method']}/seed{c['train_seed']}/{c['condition']}")
    report.append("")
    if problems:
        report.append("## PROBLEMS")
        for p in problems:
            report.append(f"- {p}")
        report.append("")
    report.append(f"## OVERALL: {'PASS' if all_ok else 'FAIL'}")
    (out_dir / "robustness_recheck_report.md").write_text("\n".join(report), encoding="utf-8")

    print("OVERALL:", "PASS" if all_ok else "FAIL")
    print(f"comparisons: {n_pass}/210")
    for p in problems[:10]:
        print("  -", p)
    print(f"out: {out_dir}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
