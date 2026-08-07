# render_paper_figures_v1_5.py — publication-quality rendering of the five key figures
# (vector PDF + high-res PNG), unified style + grayscale-friendly marker identity.
# Data read only from locked assets.
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "paper_latex_3d_en" / "figures"
HO = Path(r"D:/Code/Codex/ri_gmappo_uav_mappo_v1.5/results/paper_config_runs/formal_held_out_v1_5_10800_20260807/held_out_v1.5")
CANON = ROOT / "docs" / "paper_assets_v1_5" / "canonical_results_v1_5.csv"
RBA = ROOT / "docs" / "paper_assets_v1_5" / "robustness_absolute_recovery_v1_5.csv"
GP = ROOT / "docs" / "gate_prior_v1_5_assets" / "gate_prior_gate_summary.csv"

METHODS = ["full_ea_rg", "w_o_gate_prior", "w_o_task_support", "w_o_role_pair_gate",
           "no_graph", "single_graph", "param_matched_single", "happo", "mappo"]
RB_METHODS = ["full_ea_rg", "w_o_gate_prior", "w_o_task_support", "w_o_role_pair_gate",
              "param_matched_single", "happo", "mappo"]
SEEDS = ["0", "1", "2"]
PRIMARY_SC = ["dropout030_delay2_relay_failure_early", "dropout030_delay2_relay_failure"]

# method identity (marker + line style + color); grayscale-safe
IDENTITY = {
    "full_ea_rg": dict(marker="o", ls="-", c="#1f77b4"),
    "w_o_gate_prior": dict(marker="s", ls="--", c="#ff7f0e"),
    "w_o_task_support": dict(marker="^", ls=":", c="#2ca02c"),
    "w_o_role_pair_gate": dict(marker="v", ls="-.", c="#999999"),
    "no_graph": dict(marker="x", ls=":", c="#d62728"),
    "single_graph": dict(marker="+", ls="--", c="#8c564b"),
    "param_matched_single": dict(marker="D", ls="-.", c="#9467bd"),
    "happo": dict(marker="^", ls=":", c="#e377c2"),
    "mappo": dict(marker="s", ls="--", c="#7f7f7f"),
}
LABEL = {"full_ea_rg": "EA-RG Full", "w_o_gate_prior": "w/o Gate Prior",
         "w_o_task_support": "w/o Task-Support", "w_o_role_pair_gate": "w/o Role-Pair Mod",
         "no_graph": "No Graph", "single_graph": "Single Graph",
         "param_matched_single": "Wider Single-Graph", "happo": "HAPPO", "mappo": "MAPPO"}

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.linewidth": 1.1, "xtick.direction": "in", "ytick.direction": "in",
    "legend.frameon": True, "legend.framealpha": 0.9, "figure.dpi": 150,
})


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"{name}.{ext}", bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


def load_surv():
    """primary (Early+Nominal) T/event arrays per (method, seed)."""
    out = {}
    for m in METHODS:
        for s in SEEDS:
            T, E = [], []
            rows = list(csv.DictReader((HO / m / f"seed{s}" / "test_episode_metrics.csv").open(encoding="utf-8")))
            for r in rows:
                if r["scenario"] not in PRIMARY_SC:
                    continue
                fs = int(float(r["node_failure_start_step"]))
                steps = int(float(r["steps"]))
                if steps < fs:
                    continue
                if float(r["post_failure_chain_recovered"]) > 0.5:
                    T.append(float(r["post_failure_chain_recovery_steps"])); E.append(1)
                else:
                    T.append(float(steps - fs)); E.append(0)
            out[(m, s)] = (np.array(T), np.array(E))
    return out


def km_step(T, E):
    order = np.argsort(T); ts = T[order]; es = E[order]
    u = np.unique(ts)
    S, n_at_risk, i = [], len(T), 0
    for t in u:
        d = 0
        while i < len(ts) and ts[i] == t:
            d += es[i]; i += 1
        S.append(1 - d / n_at_risk)
        n_at_risk -= d
    return u, np.cumprod(S)


def fig_km():
    surv = load_surv()
    fig, ax = plt.subplots(figsize=(7.5, 5))
    for m in METHODS:
        T = np.concatenate([surv[(m, s)][0] for s in SEEDS])
        E = np.concatenate([surv[(m, s)][1] for s in SEEDS])
        u, S = km_step(T, E)
        idn = IDENTITY[m]
        ax.step(u, S, where="post", color=idn["c"], ls=idn["ls"], lw=1.8,
                label=LABEL[m], marker=idn["marker"], markevery=max(1, len(u) // 14),
                ms=4)
    ax.set_xlim(0, 220); ax.set_ylim(0, 1.05)
    ax.set_xlabel("steps after failure onset (t)"); ax.set_ylabel(r"$S(t)=P(T>t)$")
    ax.set_title("KM of post-failure recovery (Early+Nominal, n=600/method)")
    ax.legend(fontsize=7, ncol=2, loc="upper right"); ax.grid(alpha=0.3, ls=":")
    save(fig, "km_recovery_curve_primary")


def fig_pareto(xk, yk, xlab, ylab, name):
    rows = {}
    with CANON.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["table"] == "table1_held_out":
                rows.setdefault(r["method"], {})[r["metric"]] = r
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    for m in METHODS:
        r = rows.get(m)
        if not r:
            continue
        xm, xs = float(r[xk]["mean"]), float(r[xk]["sd"])
        ym, ys = float(r[yk]["mean"]), float(r[yk]["sd"])
        idn = IDENTITY[m]
        hl = m == "full_ea_rg"
        ax.errorbar(xm, ym, xerr=xs, yerr=ys, fmt="none", ecolor=idn["c"],
                    elinewidth=1, capsize=3, alpha=0.9)
        ax.plot(xm, ym, marker=idn["marker"], ls="none", color=idn["c"],
                ms=9 if hl else 6.5, mec="black", mew=0.6 if hl else 0.3)
        ax.annotate(LABEL[m], (xm, ym), textcoords="offset points",
                    xytext=(7, 6), fontsize=7.5)
    ax.set_xlabel(xlab); ax.set_ylabel(ylab)
    ax.grid(alpha=0.3, ls=":")
    ax.set_title(f"{xlab.split(' (')[0]} vs {ylab.split(' (')[0]} (n=3 seeds)")
    save(fig, name)


def fig_robustness():
    vals = {}
    with RBA.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            vals.setdefault(r["method"], {})[r["condition"]] = float(r["recovery_mean"])
    conds = [f"R{i:02d}" for i in range(1, 10)]
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for m in RB_METHODS:
        r00 = vals[m]["R00"]
        ys = [vals[m][c] - r00 for c in conds]
        idn = IDENTITY[m]
        ax.plot(range(len(conds)), ys, color=idn["c"], ls=idn["ls"], lw=1.6,
                marker=idn["marker"], ms=4.5, label=LABEL[m])
    ax.axhline(0, color="gray", ls="--", lw=1)
    ax.set_xticks(range(len(conds))); ax.set_xticklabels(conds, rotation=45, fontsize=8)
    ax.set_ylabel(r"$\Delta$Recovery vs R00"); ax.grid(alpha=0.3, ls=":")
    ax.legend(fontsize=7, ncol=2, loc="lower left")
    save(fig, "fig_robustness_degradation")


def fig_gate():
    rows = {}
    with GP.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.setdefault(r["method"], []).append((int(r["update"]), float(r["mean_gate"])))
    fig, ax = plt.subplots(figsize=(7.5, 5))
    for m in ("full_ea_rg", "w_o_gate_prior"):
        data = sorted(rows.get(m, []))
        if not data:
            continue
        u = [x[0] for x in data]; g = [x[1] for x in data]
        idn = IDENTITY[m]
        ax.plot(u, g, color=idn["c"], ls=idn["ls"], lw=1.8, marker=idn["marker"],
                ms=4, label=LABEL[m])
        ax.axhline(0.5987 if m == "full_ea_rg" else 0.5, color=idn["c"], ls=":",
                   lw=1, alpha=0.7)
    ax.set_xlabel("update"); ax.set_ylabel("sigmoid gate (mean of 150)")
    ax.set_ylim(0.4, 0.9); ax.grid(alpha=0.3, ls=":")
    ax.legend(fontsize=8)
    save(fig, "fig_gate_evolution")


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    fig_km()
    fig_pareto("recovery", "t_rec", "Recovery rate (up)", "t_recovery steps (down)",
               "fig_pareto_recovery")
    fig_pareto("success", "t_succ", "Success rate (up)", "t_success steps (down)",
               "fig_pareto_success")
    fig_robustness()
    fig_gate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
