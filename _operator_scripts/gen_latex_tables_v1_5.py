# gen_latex_tables_v1_5.py — generate paper_latex_3d_en/tables/*.tex from
# canonical_results_v1_5.csv (single source of truth). No hand-typed numbers.
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "docs" / "paper_assets_v1_5" / "canonical_results_v1_5.csv"
OUT = ROOT / "paper_latex_3d_en" / "tables"

HO_ORDER = ["full_ea_rg", "w_o_gate_prior", "w_o_task_support", "w_o_role_pair_gate",
            "no_graph", "single_graph", "param_matched_single", "happo", "mappo"]
RB_ORDER = ["full_ea_rg", "w_o_gate_prior", "w_o_task_support", "w_o_role_pair_gate",
            "param_matched_single", "happo", "mappo"]
RB_COND = [f"R{i:02d}" for i in range(10)]
SHORT = {"full_ea_rg": "EA-RG Full", "w_o_gate_prior": "w/o Gate Prior",
         "w_o_task_support": "w/o Task-Support", "w_o_role_pair_gate": "w/o Role-Pair Gate",
         "no_graph": "no-graph", "single_graph": "single-graph",
         "param_matched_single": "wider single-graph", "happo": "HAPPO", "mappo": "MAPPO"}


def load():
    rows = {}
    with CANON.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows[(r["table"], r["method"], r["condition"], r["metric"])] = r
    return rows


def fmt(row):
    m, s = row["mean"], row["sd"]
    if not s or s == "":
        return f"${m}$"
    return f"${m} \\pm {s}$"


def msd(v):
    return f"${v:.4f} \\pm {v:.4f}$"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    R = load()

    def get(table, m, c, metric):
        return R.get((table, m, c, metric), {}).get("mean", "—")

    # ---- Table 1: held-out ----
    lines = ["\\begin{table*}[t]", "\\centering", "\\small",
             "\\caption{Held-out performance (3 training seeds; mean $\\pm$ sample SD; "
             "10{,}800 episodes; base seed 745669). Arrows denote the direction of improvement. "
             "Wilson95 is the 95\\% lower bound of the recovery rate.",
             "\\label{tab:held_out}",
             "\\begin{tabular}{lcccccc}", "\\toprule",
             "Method & Success $\\uparrow$ & Recovery $\\uparrow$ & Wilson95 $\\uparrow$ "
             "& $t_{\\mathrm{succ}}$ $\\downarrow$ & $t_{\\mathrm{rec}}$ $\\downarrow$ & Collision $\\downarrow$ \\\\",
             "\\midrule"]
    for m in HO_ORDER:
        row = [SHORT[m],
               fmt(R[("table1_held_out", m, "-", "success")]),
               fmt(R[("table1_held_out", m, "-", "recovery")]),
               fmt(R[("table1_held_out", m, "-", "wilson")]),
               f"${float(R[('table1_held_out', m, '-', 't_succ')]['mean']):.1f} \\pm {float(R[('table1_held_out', m, '-', 't_succ')]['sd']):.1f}$",
               f"${float(R[('table1_held_out', m, '-', 't_rec')]['mean']):.1f} \\pm {float(R[('table1_held_out', m, '-', 't_rec')]['sd']):.1f}$",
               fmt(R[("table1_held_out", m, "-", "collision")])]
        lines.append(" & ".join(row) + " \\\\")
    lines += ["\\midrule",
              "\\multicolumn{7}{l}{\\footnotesize Internal ablations: w/o Gate Prior, w/o Task-Support, "
              "w/o Role-Pair Gate. Graph baselines: no-graph, single-graph, param-matched graph. "
              "External MARL baselines: MAPPO, HAPPO.} \\\\",
              "\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    (OUT / "table1_held_out.tex").write_text("\n".join(lines), encoding="utf-8")

    # ---- Table 2: ablation ----
    lines = ["\\begin{table}[t]", "\\centering", "\\small",
             "\\caption{Ablation study on held-out (3 seeds). Removing Gate Prior causes the largest "
             "reliability degradation; Task-Support contributes empirically; the Role-Pair Gate shows "
             "no consistent independent benefit.",
             "\\label{tab:ablation}",
             "\\begin{tabular}{lcccc}", "\\toprule",
             "Variant & Recovery $\\uparrow$ & $t_{\\mathrm{rec}}$ $\\downarrow$ "
             "& Success $\\uparrow$ & $t_{\\mathrm{succ}}$ $\\downarrow$ \\\\", "\\midrule"]
    for m in ("full_ea_rg", "w_o_gate_prior", "w_o_task_support", "w_o_role_pair_gate"):
        row = [SHORT[m],
               fmt(R[("table1_held_out", m, "-", "recovery")]),
               f"${float(R[('table1_held_out', m, '-', 't_rec')]['mean']):.1f} \\pm {float(R[('table1_held_out', m, '-', 't_rec')]['sd']):.1f}$",
               fmt(R[("table1_held_out", m, "-", "success")]),
               f"${float(R[('table1_held_out', m, '-', 't_succ')]['mean']):.1f} \\pm {float(R[('table1_held_out', m, '-', 't_succ')]['sd']):.1f}$"]
        lines.append(" & ".join(row) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (OUT / "table2_ablation.tex").write_text("\n".join(lines), encoding="utf-8")

    # ---- Table 3: robustness delta summary ----
    # need R00 baselines; recover from canonical table3 rows is delta-only, so read
    # robustness_absolute_recovery_v1_5.csv for absolutes
    abs_path = ROOT / "docs" / "paper_assets_v1_5" / "robustness_absolute_recovery_v1_5.csv"
    absv = {}
    with abs_path.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            absv[(r["method"], r["condition"])] = float(r["recovery_mean"])
    rb_delta = {}
    for (t, m, c, met), r in R.items():
        if t == "table3_robustness" and met == "delta_recovery_from_R00":
            rb_delta[(m, c)] = float(r["mean"])
    lines = ["\\begin{table*}[t]", "\\centering", "\\small",
             "\\caption{Robustness summary: recovery degradation $\\Delta$ relative to the R00 "
             "condition (3-seed means; unstable-exposure cells excluded and marked \\emph{n/a}). "
             "R02/R04/R09 ($^*$) support the preregistered Role-Pair Gate robustness verdict.",
             "\\label{tab:robustness}",
             "\\begin{tabular}{lcccccc}", "\\toprule",
             "Method & R01 & R02$^*$ & R03 & R04$^*$ & R05 & R06 & R07 & R08 & R09$^*$ \\\\",
             "\\midrule"]
    for m in RB_ORDER:
        cells = []
        for c in RB_COND[1:]:
            d = rb_delta.get((m, c), float("nan"))
            cells.append("\\emph{n/a}" if d != d else f"{d:+.3f}")
        lines.append(SHORT[m] + " & " + " & ".join(cells) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table*}"]
    (OUT / "table3_robustness.tex").write_text("\n".join(lines), encoding="utf-8")

    # ---- Table 4: efficiency ----
    eff = {}
    for (t, m, c, met), r in R.items():
        if t == "table4_efficiency":
            eff[(m, met)] = r["mean"]
    lines = ["\\begin{table}[t]", "\\centering", "\\small",
             "\\caption{Computational and communication cost (locked profiling, batch-1 joint "
             "decision; n=1 profile). EA-RG is computationally heavier; its benefit is task-level "
             "recovery speed, not per-forward efficiency.",
             "\\label{tab:efficiency}",
             "\\begin{tabular}{lrrrr}", "\\toprule",
             "Method & Params & Joint dec. ms & env-steps/s & Train mem (MB) \\\\", "\\midrule"]
    for m in ("full_ea_rg", "w_o_role_pair_gate", "happo", "param_matched_single", "mappo"):
        lines.append(f"{SHORT[m]} & {eff[(m, 'params')]} & {float(eff[(m, 'joint_decision_ms')]):.2f} "
                     f"& {float(eff[(m, 'env_steps_per_sec')]):.1f} & {float(eff[(m, 'train_peak_mem_mb')]):.1f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (OUT / "table4_efficiency.tex").write_text("\n".join(lines), encoding="utf-8")

    print(f"tables written to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
