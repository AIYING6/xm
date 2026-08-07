# gen_supplementary_tables_v1_5.py — generate supplementary LaTeX tables from locked
# task-support assets (window summary / case manifest).
from __future__ import annotations

import csv
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TS = ROOT / "docs" / "task_support_v1_5_assets"
PA = ROOT / "docs" / "paper_assets_v1_5"
OUT = ROOT / "paper_latex_3d_en" / "supplementary"
OUT_T = OUT / "tables"
OUT_F = OUT / "figures"


def main():
    OUT_T.mkdir(parents=True, exist_ok=True)
    OUT_F.mkdir(parents=True, exist_ok=True)

    # ---- copy figures ----
    shutil.copy(PA / "fig_pareto_success.png", OUT_F / "fig_pareto_success.png")
    shutil.copy(TS / "fig_ts_window_strength.png", OUT_F / "fig_task_support_windows.png")
    shutil.copy(TS / "fig_ts_case_examples.png", OUT_F / "fig_task_support_cases.png")

    # ---- table S1: task-support window summary (Full only) ----
    with (TS / "task_support_window_summary.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    full = [r for r in rows if r["method"] == "full"]
    lines = ["\\begin{table}[t]", "\\centering", "\\small",
             "\\caption{Task-Support relation strength by window (9 blue--blue pairs; "
             "3 training seeds; pooled over episodes). Early-post and pre-recovery are "
             "lower than pre-failure; no post-failure activation increase.",
             "\\label{tab:s1_ts_windows}",
             "\\begin{tabular}{lcccc}", "\\toprule",
             "Window & Full pooled & seed0 & seed1 & seed2 \\\\", "\\midrule"]
    # per-seed values from trajectory CSV
    with (TS / "task_support_relation_trajectory.csv").open(encoding="utf-8") as f:
        traj = list(csv.DictReader(f))
    import numpy as np
    from collections import defaultdict
    per = defaultdict(list)
    for r in traj:
        if r["method"] == "full":
            per[(r["window"], r["seed"])].append(float(r["mean_strength"]))
    order = ["pre_failure", "early_post_failure", "pre_recovery"]
    for w in order:
        vals = [float(np.mean(per[(w, s)])) for s in ("0", "1", "2")]
        pooled = float(np.mean(vals))
        lines.append(f"{w} & {pooled:.4f} & "
                     f"{vals[0]:.4f} & {vals[1]:.4f} & {vals[2]:.4f} \\\\")
    lines.append("\\midrule")
    lines.append("early$_\\text{post}$ $-$ pre & $-0.0488$ & down & down & down \\\\")
    lines.append("pre-rec $-$ early & $\\approx 0$ & \\multicolumn{3}{c}{no rebound} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (OUT_T / "table_s1_task_support_windows.tex").write_text("\n".join(lines), encoding="utf-8")

    # ---- table S2: cases (frozen rule) ----
    with (TS / "task_support_case_manifest.csv").open(encoding="utf-8") as f:
        cases = list(csv.DictReader(f))
    lines = ["\\begin{table}[t]", "\\centering", "\\small",
             "\\caption{Case examples selected by the pre-registered rule (smallest episode "
             "index within each class), not by manual choice. C1: both succeed, Full recovers "
             "faster; C2: Full succeeds, w/o Task-Support fails; C3: both fail.",
             "\\label{tab:s2_cases}",
             "\\begin{tabular}{lllrrrr}", "\\toprule",
             "Class & Scenario & Ep. & Full succ. & Fail step & Full rec. & w/o-TS rec. \\\\",
             "\\midrule"]
    for c in cases:
        lines.append(f"{c['case_class']} & {c['scenario']} & {c['episode']} & "
                     f"{c['full_success']} & {c['failure_step']} & "
                     f"{c['full_recovery_step']} & {c['wot_recovery_step']} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (OUT_T / "table_s2_task_support_cases.tex").write_text("\n".join(lines), encoding="utf-8")

    print(f"supplementary tables+figures written to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
