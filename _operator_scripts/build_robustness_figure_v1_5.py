# build_robustness_figure_v1_5.py — Fig 3 (robustness degradation) + absolute values for
# R02/R04/R09 RPG preregistered verdict. Reads locked robustness summaries only.
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "paper_assets_v1_5"
RB_BASE = Path(r"D:/Code/Codex/ri_gmappo_uav_mappo_v1.5/results/paper_config_runs/formal_robustness_v1.5_10500_20260807")

RB_METHODS = ["full_ea_rg", "w_o_gate_prior", "w_o_task_support", "w_o_role_pair_gate",
              "param_matched_single", "happo", "mappo"]
RB_COND = [f"R{i:02d}" for i in range(10)]
SEEDS = ["0", "1", "2"]
LABEL = {"full_ea_rg": "Full", "w_o_gate_prior": "w/o Gate Prior",
         "w_o_task_support": "w/o Task-Support", "w_o_role_pair_gate": "w/o RPG",
         "param_matched_single": "param-matched", "happo": "HAPPO", "mappo": "MAPPO"}


def _num(v):
    v = v.strip()
    return None if v in ("", "inf", "nan", "None", "-inf") else float(v)


def cond(m, cond, s):
    p = RB_BASE / m / f"seed{s}" / cond / "test_checkpoint_summary.csv"
    if not p.exists():
        return None
    rows = list(csv.DictReader(p.open(encoding="utf-8")))
    exp = rec = 0
    for r in rows:
        if r.get("estimate_unstable", "0").strip() == "1":
            continue
        exp += int(r["failure_exposed_count"])
        rec += int(r["recovered_given_exposure_count"])
    if exp <= 0:
        return float("nan")
    return rec / exp


def main():
    data = {}
    for m in RB_METHODS:
        data[m] = {}
        for c in RB_COND:
            vals = [cond(m, c, s) for s in SEEDS]
            vals = [v for v in vals if v == v]
            data[m][c] = float(np.mean(vals)) if vals else float("nan")

    # ---- Fig 3: delta-recovery degradation (relative to R00), worst-seed annotated ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 5.5))
    conds = RB_COND[1:]
    for m, c in (("full_ea_rg", "#1f77b4"), ("w_o_role_pair_gate", "#bbbbbb"),
                 ("w_o_task_support", "#2ca02c"), ("w_o_gate_prior", "#ff7f0e"),
                 ("mappo", "#d62728"), ("happo", "#9467bd"),
                 ("param_matched_single", "#8c564b")):
        r00 = data[m]["R00"]
        ys = [data[m][c] - r00 for c in conds]
        ax.plot(range(len(conds)), ys, "o-", color=c, lw=1.8, ms=5,
                label=LABEL[m])
    ax.axhline(0.0, color="gray", ls="--", lw=1)
    ax.set_xticks(range(len(conds)))
    ax.set_xticklabels(conds, rotation=45, fontsize=8)
    ax.set_ylabel(r"$\Delta$Recovery vs R00 (3-seed mean)")
    ax.set_title("Robustness: recovery degradation under perturbations "
                 "(n=3 training seeds; unstable-exposure cells excluded)")
    ax.legend(fontsize=7, ncol=2); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(OUT / "fig_robustness_degradation.png", dpi=150)
    plt.close(fig)

    # ---- absolute values for RPG verdict ----
    print("R00 baseline recovery (mean over 3 seeds):")
    for m in RB_METHODS:
        print(f"  {LABEL[m]:<16} {data[m]['R00']:.4f}")
    print("\nRPG preregistered verdict cells (recovery, 3-seed mean):")
    for c in ("R02", "R04", "R09"):
        print(f"  {c}: Full {data['full_ea_rg'][c]:.4f}  w/o RPG {data['w_o_role_pair_gate'][c]:.4f}  "
              f"(R00: Full {data['full_ea_rg']['R00']:.4f}, w/o RPG {data['w_o_role_pair_gate']['R00']:.4f})")

    # ---- write a supplementary absolute-value CSV ----
    with (OUT / "robustness_absolute_recovery_v1_5.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["method", "condition", "recovery_mean"])
        for m in RB_METHODS:
            for c in RB_COND:
                w.writerow([m, c, f"{data[m][c]:.4f}"])
    print(f"\nfigure + absolute CSV written to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
