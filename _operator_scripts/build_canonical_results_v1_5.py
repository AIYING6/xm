# build_canonical_results_v1_5.py
# Single-source builder: reads ONLY locked assets, writes
# docs/paper_assets_v1_5/{canonical_results_v1_5.csv, table1..4, fig_pareto_*, audit}.
# All paper numbers for v1.5 must be derived from canonical_results_v1_5.csv.
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "paper_assets_v1_5"
MP = Path(r"D:/Code/Codex/ri_gmappo_uav_mappo_v1.5/results/paper_config_runs")

HO_BASE = MP / "formal_held_out_v1_5_10800_20260807/held_out_v1.5"
RB_BASE = MP / "formal_robustness_v1.5_10500_20260807"
EF_BASE = MP / "formal_efficiency_v1.5_20260807/_operator_notes/final_efficiency_audit_v1_5"

HO_METHODS = ["full_ea_rg", "w_o_gate_prior", "w_o_task_support", "w_o_role_pair_gate",
              "no_graph", "single_graph", "param_matched_single", "happo", "mappo"]
RB_METHODS = ["full_ea_rg", "w_o_gate_prior", "w_o_task_support", "w_o_role_pair_gate",
              "param_matched_single", "happo", "mappo"]
RB_COND = [f"R{i:02d}" for i in range(10)]
SEEDS = ["0", "1", "2"]


def _num(v):
    v = v.strip()
    if v in ("", "inf", "nan", "None", "-inf"):
        return None
    return float(v)


def wilson95(recovered, exposed, z=1.96):
    if exposed <= 0:
        return float("nan")
    p = recovered / exposed
    denom = 1 + z * z / exposed
    centre = p + z * z / (2 * exposed)
    half = z * np.sqrt(p * (1 - p) / exposed + z * z / (4 * exposed * exposed))
    return (centre - half) / denom


def ho_pooled(m, s):
    p = HO_BASE / m / f"seed{s}" / "test_checkpoint_summary.csv"
    if not p.exists():
        return None
    rows = list(csv.DictReader(p.open(encoding="utf-8")))
    ep = succ = coll = exp = rec = 0
    tsucc_n = tsucc_d = trec_n = trec_d = 0.0
    for r in rows:
        e = int(r["episodes"]); sm = _num(r["success_mean"]); cm = _num(r["collision_mean"])
        ex = int(r["failure_exposed_count"]); rc = int(r["recovered_given_exposure_count"])
        ep += e
        if sm is not None:
            succ += e * sm
        if cm is not None:
            coll += e * cm
        exp += ex; rec += rc
        ts = _num(r["time_to_success"])
        if ts is not None and sm is not None:
            tsucc_n += ts * e * sm; tsucc_d += e * sm
        tr = _num(r["time_to_recovery_given_exposure"])
        if tr is not None and rc > 0:
            trec_n += tr * rc; trec_d += rc
    return {
        "success": succ / ep, "recovery": rec / exp if exp else float("nan"),
        "wilson": wilson95(rec, exp),
        "collision": coll / ep,
        "t_succ": tsucc_n / tsucc_d if tsucc_d else float("nan"),
        "t_rec": trec_n / trec_d if trec_d else float("nan"),
        "exposed": exp, "recovered": rec, "episodes": ep,
    }


def msd(vals):
    a = np.array([v for v in vals if v == v], dtype=float)  # drop nan
    if a.size == 0:
        return float("nan"), float("nan")
    return float(a.mean()), float(a.std(ddof=1) if a.size > 1 else 0.0)


def rb_pooled(m, cond, s):
    p = RB_BASE / m / f"seed{s}" / cond / "test_checkpoint_summary.csv"
    if not p.exists():
        return None
    rows = list(csv.DictReader(p.open(encoding="utf-8")))
    succ = coll = exp = rec = 0
    trec_n = trec_d = 0.0
    ep = 0
    for r in rows:
        if r.get("estimate_unstable", "0").strip() == "1":
            continue  # robustness audit convention: exclude unstable cells
        sm = _num(r["success_mean"]); cm = _num(r["collision_mean"])
        ex = int(r["failure_exposed_count"]); rc = int(r["recovered_given_exposure_count"])
        e = int(r["episodes"]); ep += e
        succ += e * (sm if sm is not None else 0.0)
        coll += e * (cm if cm is not None else 0.0)
        exp += ex; rec += rc
        tr = _num(r["time_to_recovery_given_exposure"])
        if tr is not None and rc > 0:
            trec_n += tr * rc; trec_d += rc
    return {
        "success": succ / ep if ep else float("nan"),
        "recovery": rec / exp if exp else float("nan"),
        "collision": coll / ep if ep else float("nan"),
        "t_rec": trec_n / trec_d if trec_d else float("nan"),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    problems: list[str] = []
    canon = []  # rows for canonical_results_v1_5.csv

    # ---------- 1. held-out (Table 1) ----------
    ho_rows = {}
    for m in HO_METHODS:
        per = [ho_pooled(m, s) for s in SEEDS]
        per = [x for x in per if x]
        if len(per) != 3:
            problems.append(f"held-out {m}: {len(per)}/3 seeds")
            continue
        ho_rows[m] = {k: msd([p[k] for p in per]) for k in
                      ("success", "recovery", "wilson", "t_succ", "t_rec", "collision")}
        for k in ("success", "recovery", "wilson", "t_succ", "t_rec", "collision"):
            mu, sd = ho_rows[m][k]
            canon.append({"table": "table1_held_out", "method": m, "condition": "-",
                          "metric": k, "mean": f"{mu:.6f}", "sd": f"{sd:.6f}", "n": 3,
                          "source": "formal-held-out-results-lock-v1.5.1"})

    # ---------- 2. robustness (Table 3: Delta from R00 + worst-seed) ----------
    rb = {}
    for m in RB_METHODS:
        rb[m] = {}
        for cond in RB_COND:
            per = [rb_pooled(m, cond, s) for s in SEEDS]
            per = [x for x in per if x]
            if not per:
                problems.append(f"robust {m} {cond}: no seed data")
                continue
            rec_m, rec_s = msd([p["recovery"] for p in per])
            tr_m, tr_s = msd([p["t_rec"] for p in per])
            worst = float(np.nanmin([p["recovery"] for p in per]))
            rb[m][cond] = {"recovery_mean": rec_m, "recovery_sd": rec_s,
                           "t_rec_mean": tr_m, "t_rec_sd": tr_s, "worst_seed": worst,
                           "n_seed": len(per)}
    # deltas
    for m in RB_METHODS:
        if "R00" not in rb[m]:
            continue
        r00 = rb[m]["R00"]
        for cond in RB_COND[1:]:
            if cond not in rb[m]:
                continue
            d_rec = rb[m][cond]["recovery_mean"] - r00["recovery_mean"]
            d_tr = rb[m][cond]["t_rec_mean"] - r00["t_rec_mean"]
            canon.append({"table": "table3_robustness", "method": m, "condition": cond,
                          "metric": "delta_recovery_from_R00",
                          "mean": f"{d_rec:.6f}", "sd": "", "n": 3,
                          "source": "robustness-results-lock-v1.5.0"})
            canon.append({"table": "table3_robustness", "method": m, "condition": cond,
                          "metric": "delta_t_rec_from_R00",
                          "mean": f"{d_tr:.6f}", "sd": "", "n": 3,
                          "source": "robustness-results-lock-v1.5.0"})
            canon.append({"table": "table3_robustness", "method": m, "condition": cond,
                          "metric": "worst_seed_recovery",
                          "mean": f"{rb[m][cond]['worst_seed']:.6f}", "sd": "", "n": 3,
                          "source": "robustness-results-lock-v1.5.0"})

    # ---------- 3. efficiency (Table 4) ----------
    eff = {}
    if (EF_BASE / "efficiency_params.csv").exists():
        prm = {r["method"]: int(r["params"]) for r in
               csv.DictReader((EF_BASE / "efficiency_params.csv").open(encoding="utf-8"))}
        lat = {}
        jps = {}
        for r in csv.DictReader((EF_BASE / "efficiency_latency.csv").open(encoding="utf-8")):
            if r["batch"] == "1":
                lat[r["method"]] = float(r["mean_ms"])
                jps[r["method"]] = float(r["joint_decisions_per_s"])
        thr = {r["method"]: float(r["env_steps_per_s"]) for r in
               csv.DictReader((EF_BASE / "efficiency_throughput.csv").open(encoding="utf-8"))}
        mem = {}
        for r in csv.DictReader((EF_BASE / "efficiency_memory.csv").open(encoding="utf-8")):
            if r.get("kind") == "training":
                mem[r["method"]] = float(r["peak_allocated_mb"])
        for m, params in prm.items():
            eff[m] = {"params": params, "latency_ms": lat.get(m, float("nan")),
                      "joint_per_s": jps.get(m, float("nan")),
                      "throughput": thr.get(m, float("nan")),
                      "train_mem_mb": mem.get(m, float("nan"))}
            canon.append({"table": "table4_efficiency", "method": m, "condition": "-",
                          "metric": "params", "mean": str(params), "sd": "", "n": 1,
                          "source": "efficiency-results-lock-v1.5.0"})
            canon.append({"table": "table4_efficiency", "method": m, "condition": "-",
                          "metric": "joint_decision_ms", "mean": f"{lat.get(m, float('nan')):.4f}",
                          "sd": "", "n": 1, "source": "efficiency-results-lock-v1.5.0"})
            canon.append({"table": "table4_efficiency", "method": m, "condition": "-",
                          "metric": "joint_decisions_per_s",
                          "mean": f"{jps.get(m, float('nan')):.1f}",
                          "sd": "", "n": 1, "source": "efficiency-results-lock-v1.5.0"})
            canon.append({"table": "table4_efficiency", "method": m, "condition": "-",
                          "metric": "env_steps_per_sec", "mean": f"{thr.get(m, float('nan')):.2f}",
                          "sd": "", "n": 1, "source": "efficiency-results-lock-v1.5.0"})
            canon.append({"table": "table4_efficiency", "method": m, "condition": "-",
                          "metric": "train_peak_mem_mb", "mean": f"{mem.get(m, float('nan')):.2f}",
                          "sd": "", "n": 1, "source": "efficiency-results-lock-v1.5.0"})

    # ---------- write canonical CSV ----------
    with (OUT / "canonical_results_v1_5.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["table", "method", "condition", "metric",
                                          "mean", "sd", "n", "source"])
        w.writeheader(); w.writerows(canon)

    # ---------- Table 1 / 2 md ----------
    def fmt(v, nd=4):
        mu, sd = v
        return "—" if mu != mu else f"{mu:.{nd}f}±{sd:.{nd}f}"

    t1 = ["# Table 1 — Held-out main results (n=3 training seeds, mean ± SD)",
          "", "| method | Success | Recovery | Wilson95 LB | t_success | t_recovery | Collision |",
          "|---|---|---|---|---|---|---|"]
    for m in HO_METHODS:
        if m not in ho_rows:
            continue
        r = ho_rows[m]
        t1.append(f"| {m} | {fmt(r['success'])} | {fmt(r['recovery'])} | {fmt(r['wilson'])} | "
                  f"{fmt(r['t_succ'],1)} | {fmt(r['t_rec'],1)} | {fmt(r['collision'],4)} |")
    (OUT / "table1_held_out.md").write_text("\n".join(t1), encoding="utf-8")

    abl = ["# Table 2 — Ablation (held-out, n=3)",
           "", "| variant | Recovery | t_rec | Success | t_succ |",
           "|---|---|---|---|---|"]
    for m in ("full_ea_rg", "w_o_gate_prior", "w_o_task_support", "w_o_role_pair_gate"):
        r = ho_rows.get(m)
        if not r:
            continue
        abl.append(f"| {m} | {fmt(r['recovery'])} | {fmt(r['t_rec'],1)} | "
                   f"{fmt(r['success'])} | {fmt(r['t_succ'],1)} |")
    abl += ["", "Conclusion: Gate Prior = strong; Task-Support = empirical; RPG = no "
               "consistent independent gain."]
    (OUT / "table2_ablation.md").write_text("\n".join(abl), encoding="utf-8")

    # ---------- Table 3 md (delta summary + R02/R04/R09 flagged) ----------
    t3 = ["# Table 3 — Robustness summary (Δ vs R00, n=3 seeds)", "",
          "R02 / R04 / R09 are flagged (*) — used for the pre-registered RPG verdict.",
          "", "| method | cond | ΔRecovery | Δt_rec | worst-seed recovery |",
          "|---|---|---|---|---|"]
    for m in RB_METHODS:
        for cond in RB_COND[1:]:
            if cond not in rb.get(m, {}):
                continue
            star = "*" if cond in ("R02", "R04", "R09") else ""
            d_rec = rb[m][cond]["recovery_mean"] - rb[m]["R00"]["recovery_mean"]
            d_tr = rb[m][cond]["t_rec_mean"] - rb[m]["R00"]["t_rec_mean"]
            ws = rb[m][cond]["worst_seed"]
            rec_s = "unstable" if d_rec != d_rec else f"{d_rec:+.3f}"
            tr_s = "unstable" if d_tr != d_tr else f"{d_tr:+.1f}"
            ws_s = "unstable" if ws != ws else f"{ws:.3f}"
            t3.append(f"| {m} | {cond}{star} | {rec_s} | {tr_s} | {ws_s} |")
    (OUT / "table3_robustness.md").write_text("\n".join(t3), encoding="utf-8")

    # ---------- Table 4 md ----------
    t4 = ["# Table 4 — Efficiency (locked, n=1 profile)", "",
          "| method | params | joint decision ms | joint decisions/s | e2e env-steps/s | train peak mem (MB) |",
          "|---|---|---|---|---|---|"]
    for m, d in eff.items():
        t4.append(f"| {m} | {d['params']} | {d['latency_ms']:.2f} | {d['joint_per_s']:.0f} | "
                  f"{d['throughput']:.1f} | {d['train_mem_mb']:.1f} |")
    (OUT / "table4_efficiency.md").write_text("\n".join(t4), encoding="utf-8")

    # ---------- Pareto figures ----------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def pareto(ax, xk, yk, xlab, ylab, highlight, weak, fname, xlim, ylim):
        for m in HO_METHODS:
            if m not in ho_rows:
                continue
            xm, xs = ho_rows[m][xk]; ym, ys = ho_rows[m][yk]
            if xm != xm or ym != ym:
                continue
            if m in highlight:
                c, z, lab = "#1f77b4", 120, m
            elif m in weak:
                c, z, lab = "#bbbbbb", 60, m
            else:
                c, z, lab = "#888888", 80, m
            ax.errorbar(xm, ym, xerr=xs, yerr=ys, fmt="o", color=c, zorder=z,
                        markersize=8 if m in highlight else 5, capsize=3, alpha=0.9)
            ax.annotate(lab, (xm, ym), textcoords="offset points", xytext=(6, 6), fontsize=8)
        ax.set_xlabel(xlab); ax.set_ylabel(ylab)
        ax.set_xlim(*xlim); ax.set_ylim(*ylim)
        ax.grid(alpha=0.3)

    fig, ax = plt.subplots(figsize=(8, 6))
    pareto(ax, "recovery", "t_rec", "Recovery rate (↑)", "t_recovery steps (↓)",
           {"full_ea_rg", "mappo", "happo", "param_matched_single"}, {"w_o_role_pair_gate"},
           "fig_pareto_recovery.png", (0.6, 1.02), (0, 95))
    ax.set_title("Reliability–recovery-speed Pareto (n=3 training seeds; error bars = sample SD)")
    fig.tight_layout(); fig.savefig(OUT / "fig_pareto_recovery.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 6))
    pareto(ax, "success", "t_succ", "Success rate (↑)", "t_success steps (↓)",
           {"full_ea_rg", "mappo", "happo", "param_matched_single"}, {"w_o_role_pair_gate"},
           "fig_pareto_success.png", (0.6, 1.02), (40, 110))
    ax.set_title("Task-completion Pareto (n=3 training seeds; error bars = sample SD)")
    fig.tight_layout(); fig.savefig(OUT / "fig_pareto_success.png", dpi=150); plt.close(fig)

    # ---------- consistency audit vs locked audit report ----------
    ref = {  # from held_out_audit_report.md (locked)
        "full_ea_rg": (0.9850, 0.9706, 0.9384, 46.1, 10.8, 0.0),
        "mappo": (0.9708, 0.9471, 0.9114, 51.0, 17.4, 0.0),
        "happo": (1.0, 1.0, 0.9820, 49.9, 16.3, 0.0),
        "param_matched_single": (0.9967, 0.9949, 0.9749, 57.6, 26.2, 0.0),
    }
    audit = ["# Canonical consistency audit", "", "| method | metric | canonical | audit ref | diff |", "|---|---|---|---|---|"]
    n_bad = 0
    for m, refs in ref.items():
        if m not in ho_rows:
            continue
        keys = ("success", "recovery", "wilson", "t_succ", "t_rec", "collision")
        for k, rv in zip(keys, refs):
            mu, _ = ho_rows[m][k]
            diff = abs(mu - rv)
            # step metrics are rounded to 1 decimal in the audit report (tol 0.5);
            # ratio metrics require 1e-3
            tol = 0.5 if k in ("t_succ", "t_rec") else 1e-3
            if diff > tol:
                n_bad += 1
            audit.append(f"| {m} | {k} | {mu:.4f} | {rv:.4f} | {diff:.5f} | tol={tol}")
    audit.append("")
    audit.append(f"mismatches beyond tolerance: {n_bad}")
    if n_bad:
        problems.append(f"canonical vs audit mismatch count: {n_bad}")
    (OUT / "canonical_audit.md").write_text("\n".join(audit), encoding="utf-8")

    print(f"tables written; canonical rows: {len(canon)}")
    print(f"OVERALL: {'PASS' if not problems else 'FAIL'}  problems={problems}")
    sys.exit(0 if not problems else 1)


if __name__ == "__main__":
    main()
