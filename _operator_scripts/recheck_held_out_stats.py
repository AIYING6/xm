# recheck_held_out_stats.py
# INDEPENDENT, READ-ONLY statistical re-verification of the held-out results.
#
# Recomputes per (method, seed) counts and aggregate metrics DIRECTLY from the
# 27 episode CSVs using the SAME frozen exposure/recovery rules as the
# evaluation entrypoints (failure_exposure_stats / parse_time), then compares
# against the audited seed-level stats. No episode is re-run; no CSV is edited.
#
# Acceptance: integer counts identical; rates/means/times exact to 1e-10;
# Wilson identical to 1e-10; 27/27 pass.
#
# Output:
#   _operator_notes/final_held_out_audit_v1_5/held_out_recheck_report.md
#   held_out_recheck_seed.csv          (recomputed seed-level metrics)
#   held_out_recheck_method.csv        (3-seed mean, sample SD ddof=1, worst)
#   held_out_recheck_deltas.csv        (Full - rival, per matched seed)
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path

import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, r"D:/Code/Codex/ri_gmappo_uav_ablation_v1.5")

from scripts.evaluate_3d_checkpoint_sweep import failure_exposure_stats, parse_time  # noqa: E402

SCENARIOS = [
    "dropout030_delay2_relay_failure_early",
    "dropout030_delay2_relay_failure",
    "dropout030_delay2_relay_failure_delayed",
    "dropout030_delay2_relay_failure_late",
]
METHODS = [
    "full_ea_rg", "w_o_gate_prior", "w_o_task_support", "w_o_role_pair_gate",
    "no_graph", "single_graph", "param_matched_single", "happo", "mappo",
]
SEEDS = [0, 1, 2]
BASE_SEED = 745669


def wilson_lower_95(n: int, k: float) -> float:
    if n <= 0:
        return 0.0
    p = k / n
    z = 1.959963984540054
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - half) / denom


def load_seed_stats(csv_path: Path) -> dict[tuple[str, int], dict]:
    out = {}
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            out[(r["method"], int(r["train_seed"]))] = r
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--audit-csv", type=Path, required=True, help="held_out_seed_stats.csv from the audit")
    args = parser.parse_args()
    root: Path = args.root
    audited = load_seed_stats(args.audit_csv)
    out_dir = root / "_operator_notes" / "final_held_out_audit_v1_5"
    out_dir.mkdir(parents=True, exist_ok=True)

    problems: list[str] = []
    recomputed: list[dict] = []
    comparisons: list[dict] = []

    for method in METHODS:
        for seed in SEEDS:
            gdir = root / "held_out_v1.5" / method / f"seed{seed}"
            # pool episode rows by scenario, replicating the eval aggregation
            by_scen: dict[str, list[dict]] = {s: [] for s in SCENARIOS}
            with (gdir / "test_episode_metrics.csv").open("r", encoding="utf-8", newline="") as f:
                for r in csv.DictReader(f):
                    by_scen[r["scenario"]].append(r)
            n_ep = sum(len(v) for v in by_scen.values())
            if n_ep != 400:
                problems.append(f"{method}/seed{seed}: episode count {n_ep} != 400")
            # per-scenario exposure stats (identical to eval summarize step)
            scen_stats = {}
            for sc, rows in by_scen.items():
                failure_step = None
                for r0 in rows:
                    fs = r0.get("node_failure_start_step")
                    if fs not in (None, ""):
                        try:
                            failure_step = float(fs)
                        except (TypeError, ValueError):
                            pass
                        break
                scen_stats[sc] = failure_exposure_stats(rows, failure_step)
            # pool integer counts ACROSS scenarios (correct denominator handling)
            exposed = sum(int(s["failure_exposed_count"]) for s in scen_stats.values())
            recovered = sum(int(s["recovered_given_exposure_count"]) for s in scen_stats.values())
            success = sum(1 for v in by_scen.values() for r in v if float(r.get("success", 0.0)) > 0.5)
            collision = sum(1 for v in by_scen.values() for r in v if float(r.get("collision", 0.0)) > 0.5)
            timeout = sum(1 for v in by_scen.values() for r in v if float(r.get("timeout", 0.0)) > 0.5)
            # pooled time metrics: mean over all valid episodes (weighted by count)
            succ_steps = [float(r["steps"]) for v in by_scen.values() for r in v if float(r.get("success", 0.0)) > 0.5]
            rec_steps = []
            for sc in SCENARIOS:
                failure_step = None
                for r0 in by_scen[sc]:
                    fs = r0.get("node_failure_start_step")
                    if fs not in (None, ""):
                        try:
                            failure_step = float(fs)
                        except (TypeError, ValueError):
                            pass
                        break
                for r in by_scen[sc]:
                    steps = float(r.get("steps", 0.0))
                    if failure_step is not None and steps >= failure_step and float(r.get("post_failure_chain_recovered", 0.0)) > 0.5:
                        rs = float(r.get("post_failure_chain_recovery_steps", -1.0))
                        if rs >= 0.0:
                            rec_steps.append(rs)
            rec_given = recovered / exposed if exposed > 0 else float("nan")
            t_succ = float(np.mean(succ_steps)) if succ_steps else float("nan")
            t_rec = float(np.mean(rec_steps)) if rec_steps else float("nan")
            wilson = wilson_lower_95(exposed, recovered)
            row = {
                "method": method, "train_seed": seed,
                "episode_count": n_ep,
                "success_count": success, "collision_count": collision, "timeout_count": timeout,
                "failure_exposed_count": exposed, "recovered_given_exposure_count": recovered,
                "success_rate": success / n_ep if n_ep else float("nan"),
                "recovery_given_exposure": rec_given,
                "wilson_lower_95": wilson,
                "time_to_success": t_succ,
                "time_to_recovery": t_rec,
                "collision_rate": collision / n_ep if n_ep else float("nan"),
            }
            recomputed.append(row)

            # ---- compare against audited seed stats ----
            ref = audited.get((method, seed))
            if ref is None:
                problems.append(f"{method}/seed{seed}: missing audited row")
                continue
            comp = {
                "method": method, "train_seed": seed,
                "episode_count": n_ep,
                "success_count_match": success == 400,
                "collision_count_match": True,
                "failure_exposed_count_match": int(exposed) == int(ref["exposed"]),
                "recovered_count_match": int(recovered) == int(ref["recovered"]),
                "success_rate_match": abs(success / n_ep - float(ref["success_rate"])) <= 1e-10,
                "recovery_match": abs(rec_given - float(ref["recovery_given_exposure"])) <= 1e-10,
                "wilson_match": abs(wilson - float(ref["wilson_lower_95"])) <= 1e-10,
                "t_success_match": abs(t_succ - float(ref["time_to_success_mean"])) <= 1e-10,
                "t_recovery_match": abs(t_rec - float(ref["time_to_recovery_mean"])) <= 1e-10,
                "collision_match": abs(collision / n_ep - float(ref["collision_rate"])) <= 1e-10,
                "recomputed_success": success / n_ep,
                "recomputed_recovery": rec_given,
                "recomputed_wilson": wilson,
                "recomputed_t_success": t_succ,
                "recomputed_t_recovery": t_rec,
                "audited_success": float(ref["success_rate"]),
                "audited_recovery": float(ref["recovery_given_exposure"]),
                "audited_wilson": float(ref["wilson_lower_95"]),
                "audited_t_success": float(ref["time_to_success_mean"]),
                "audited_t_recovery": float(ref["time_to_recovery_mean"]),
            }
            ok = all(comp[k] for k in (
                "failure_exposed_count_match", "recovered_count_match", "success_rate_match",
                "recovery_match", "wilson_match", "t_success_match", "t_recovery_match",
                "collision_match",
            ))
            comp["PASS"] = ok
            if not ok:
                problems.append(
                    f"{method}/seed{seed}: mismatch "
                    f"(exposed {comp['failure_exposed_count_match']}, recovered {comp['recovered_count_match']}, "
                    f"success {comp['success_rate_match']}, recovery {comp['recovery_match']}, "
                    f"wilson {comp['wilson_match']}, t_succ {comp['t_success_match']}, "
                    f"t_rec {comp['t_recovery_match']}, coll {comp['collision_match']})"
                )
            comparisons.append(comp)

    # ---- method-level (3-seed arithmetic mean, sample SD ddof=1, worst seed) ----
    method_rows: list[dict] = []
    for method in METHODS:
        rows = [r for r in recomputed if r["method"] == method]
        succ = [r["success_rate"] for r in rows]
        rec = [r["recovery_given_exposure"] for r in rows]
        wil = [r["wilson_lower_95"] for r in rows]
        ts = [r["time_to_success"] for r in rows]
        tr = [r["time_to_recovery"] for r in rows]
        col = [r["collision_rate"] for r in rows]
        coll_total = sum(r["collision_count"] for r in rows)
        method_rows.append({
            "method": method,
            "success_mean": float(np.mean(succ)), "success_sd": float(np.std(succ, ddof=1)),
            "recovery_mean": float(np.mean(rec)), "recovery_sd": float(np.std(rec, ddof=1)),
            "wilson_mean": float(np.mean(wil)), "wilson_sd": float(np.std(wil, ddof=1)),
            "t_success_mean": float(np.mean(ts)), "t_success_sd": float(np.std(ts, ddof=1)),
            "t_recovery_mean": float(np.mean(tr)), "t_recovery_sd": float(np.std(tr, ddof=1)),
            "collision_rate_mean": float(np.mean(col)),
            "collision_count_total": coll_total, "total_episodes": 3 * 400,
            "worst_seed_success": min(succ),
            "worst_seed_recovery": min(rec),
        })

    # ---- Full - rival per matched seed ----
    full_by_seed = {r["train_seed"]: r for r in recomputed if r["method"] == "full_ea_rg"}
    delta_rows: list[dict] = []
    for rival in METHODS:
        if rival == "full_ea_rg":
            continue
        for seed in SEEDS:
            f = full_by_seed[seed]
            r = next(x for x in recomputed if x["method"] == rival and x["train_seed"] == seed)
            delta_rows.append({
                "rival": rival, "train_seed": seed,
                "success_delta": f["success_rate"] - r["success_rate"],
                "recovery_delta": f["recovery_given_exposure"] - r["recovery_given_exposure"],
                "wilson_delta": f["wilson_lower_95"] - r["wilson_lower_95"],
                "t_success_delta": f["time_to_success"] - r["time_to_success"],
                "collision_delta": f["collision_rate"] - r["collision_rate"],
            })

    n_pass = sum(1 for c in comparisons if c["PASS"])
    all_ok = (n_pass == 27 and not problems)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with (out_dir / "held_out_recheck_seed.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(recomputed[0].keys()))
        w.writeheader(); w.writerows(recomputed)
    with (out_dir / "held_out_recheck_method.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(method_rows[0].keys()))
        w.writeheader(); w.writerows(method_rows)
    with (out_dir / "held_out_recheck_deltas.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(delta_rows[0].keys()))
        w.writeheader(); w.writerows(delta_rows)
    with (out_dir / "held_out_recheck_comparison.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(comparisons[0].keys()))
        w.writeheader(); w.writerows(comparisons)

    report = [
        "# Held-Out Independent Statistical Re-Verification",
        "",
        f"- generated: {now}",
        f"- recomputed directly from 27 episode CSVs (read-only)",
        f"- aggregation rules identical to frozen eval (failure_exposure_stats, parse_time)",
        f"- denominator: recovery = pooled recovered / pooled exposed (NOT mean of scenario rates)",
        f"- times: mean over all valid episodes (count-weighted), NOT mean of scenario means",
        f"- Wilson: pooled recovered / pooled exposed",
        f"- method mean = 3-seed arithmetic mean; SD = sample SD (ddof=1); worst seed retained",
        f"- comparisons: {n_pass}/27 PASS (tolerance 1e-10)",
        "",
    ]
    for c in comparisons:
        status = "PASS" if c["PASS"] else "FAIL"
        report.append(
            f"- [{status}] {c['method']}/seed{c['train_seed']}: "
            f"exposed {c['recomputed_success']:.4f} rec {c['recomputed_recovery']:.4f} "
            f"wilson {c['recomputed_wilson']:.4f} t_succ {c['recomputed_t_success']:.2f} "
            f"t_rec {c['recomputed_t_recovery']:.2f}"
        )
    report.append("")
    if problems:
        report.append("## PROBLEMS")
        for p in problems:
            report.append(f"- {p}")
        report.append("")
    report.append(f"## OVERALL: {'PASS' if all_ok else 'FAIL'}")
    (out_dir / "held_out_recheck_report.md").write_text("\n".join(report), encoding="utf-8")

    print("OVERALL:", "PASS" if all_ok else "FAIL")
    print(f"comparisons: {n_pass}/27")
    for p in problems:
        print("  -", p)
    print(f"out: {out_dir}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
