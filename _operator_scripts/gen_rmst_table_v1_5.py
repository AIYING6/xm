# gen_rmst_table_v1_5.py — Table II: censor-aware recovery (RMST at 50/80/100/220),
# from locked survival results. Primary methods only.
from __future__ import annotations

import csv
import sys
from pathlib import Path

OUT = Path(r"D:/Code/Codex/ri_gmappo_uav/paper_latex_3d_en/tables/table2_rmst.tex")
SENS = Path(r"D:/Code/Codex/ri_gmappo_uav/docs/statistics/survival_results_v1_1/sensitivity_rmst.csv")

METHODS = ["full_ea_rg", "mappo", "happo", "param_matched_single", "w_o_role_pair_gate"]
LABEL = {"full_ea_rg": "EA-RG Full", "mappo": "MAPPO", "happo": "HAPPO",
         "param_matched_single": "Wider Single-Graph", "w_o_role_pair_gate": "w/o Role-Pair Mod"}
TAUS = ["50", "80", "100", "220"]

rows = list(csv.DictReader(SENS.open(encoding="utf-8")))
by_tau = {r["tau"]: r for r in rows}

lines = [
    "\\begin{table}[t]", "\\centering", "\\small",
    "\\caption{Restricted mean survival time (RMST, steps) at pre-specified horizons under "
    "matched failure exposure (Early+Nominal primary population; mean over 3 training seeds). "
    "Lower is better (earlier recovery). $\\tau=80$ equals the active node-failure duration.",
    "\\label{tab:rmst}",
    "\\begin{tabular}{lcccc}", "\\toprule",
    "Method & RMST(50) & RMST(80) & RMST(100) & RMST(220) \\\\", "\\midrule",
]
for m in METHODS:
    cells = [by_tau[t][LABEL[m]] for t in TAUS]
    lines.append(f"{LABEL[m]} & {' & '.join(cells)} \\\\")
lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
OUT.write_text("\n".join(lines), encoding="utf-8")
print("written", OUT)
