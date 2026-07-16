from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


METHOD_NAMES = {
    "MAPPO": "MAPPO",
    "GAT-MAPPO": "GAT-MAPPO",
    "RI no-edge": "RG-MAPPO",
    "RI edge fixed-r8": "EA-RG-MAPPO",
    "RI edge staged": "EA-RG-MAPPO-S",
}


def fmt(mean: str, std: str) -> str:
    if std == "":
        return f"{float(mean):.3f}"
    return f"{float(mean):.3f}$\\pm${float(std):.3f}"


def load_rows(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def write_table(rows: list[dict], out: Path, caption: str, label: str) -> None:
    lines = [
        "\\begin{table*}[t]",
        "\\centering",
        f"\\caption{{{caption}}}",
        f"\\label{{{label}}}",
        "\\begin{tabular}{lccccc}",
        "\\toprule",
        "Method & Radius & Success $\\uparrow$ & Collision $\\downarrow$ & Timeout $\\downarrow$ & Avg. steps $\\downarrow$ \\\\",
        "\\midrule",
    ]

    current_method = None
    for row in rows:
        method = METHOD_NAMES.get(row["method"], row["method"])
        if current_method is not None and method != current_method:
            lines.append("\\midrule")
        current_method = method
        lines.append(
            f"{method} & {float(row['radius']):.0f} & "
            f"{fmt(row['success_mean'], row['success_std'])} & "
            f"{fmt(row['collision_mean'], row['collision_std'])} & "
            f"{fmt(row['timeout_mean'], row['timeout_std'])} & "
            f"{fmt(row['avg_steps_mean'], row['avg_steps_std'])} \\\\"
        )

    lines.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            "\\end{table*}",
            "",
        ]
    )

    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)


def write_ablation_table(rows: list[dict], out: Path) -> None:
    keep = {"RI no-edge", "RI edge fixed-r8", "RI edge staged"}
    ablation_rows = [row for row in rows if row["method"] in keep]
    write_table(
        ablation_rows,
        out,
        "Ablation study of role graph, edge-aware attention, and staged random-radius fine-tuning. Results are reported as mean$\\pm$std over three seeds.",
        "tab:ablation_results",
    )


def write_speed_robustness_table(rows: list[dict], out: Path) -> None:
    lines = [
        "\\begin{table*}[t]",
        "\\centering",
        "\\caption{Target-speed robustness evaluation. Results are reported as mean$\\pm$std over three seeds with 100 episodes per seed.}",
        "\\label{tab:speed_robustness}",
        "\\begin{tabular}{lccccc}",
        "\\toprule",
        "Method & Radius & Speed & Success $\\uparrow$ & Collision $\\downarrow$ & Timeout $\\downarrow$ \\\\",
        "\\midrule",
    ]
    current_method = None
    for row in rows:
        method = row["method"]
        if current_method is not None and method != current_method:
            lines.append("\\midrule")
        current_method = method
        lines.append(
            f"{method} & {float(row['radius']):.0f} & {float(row['target_speed']):.2f} & "
            f"{fmt(row['success_mean'], row['success_std'])} & "
            f"{fmt(row['collision_mean'], row['collision_std'])} & "
            f"{fmt(row['timeout_mean'], row['timeout_std'])} \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table*}", ""])
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)


def write_edge_feature_ablation_table(rows: list[dict], out: Path) -> None:
    labels = {
        "none": "None",
        "zero_rel_pos": "Position",
        "zero_distance": "Distance",
        "zero_bearing": "Bearing",
        "zero_rel_velocity": "Rel. velocity",
        "zero_comm_target_flags": "Comm./target flags",
        "zero_all_edge_features": "All edge features",
    }
    order = {name: idx for idx, name in enumerate(labels)}
    rows = sorted(rows, key=lambda row: (order.get(row["ablation"], 99), float(row["radius"])))
    baseline = {
        float(row["radius"]): row for row in rows if row["ablation"] == "none"
    }
    lines = [
        "\\begin{table*}[t]",
        "\\centering",
        "\\caption{Evaluation-time edge-feature masking diagnostic. Results are reported as mean$\\pm$std over three seeds with 30 episodes per seed.}",
        "\\label{tab:edge_feature_masking}",
        "\\begin{tabular}{lccccc}",
        "\\toprule",
        "Masked group & Radius & Success $\\uparrow$ & $\\Delta$Success & Collision $\\downarrow$ & $\\Delta$Collision \\\\",
        "\\midrule",
    ]
    current_ablation = None
    for row in rows:
        ablation = row["ablation"]
        if current_ablation is not None and ablation != current_ablation:
            lines.append("\\midrule")
        current_ablation = ablation
        base = baseline[float(row["radius"])]
        delta_success = float(row["success_mean"]) - float(base["success_mean"])
        delta_collision = float(row["collision_mean"]) - float(base["collision_mean"])
        lines.append(
            f"{labels.get(ablation, ablation)} & {float(row['radius']):.0f} & "
            f"{fmt(row['success_mean'], row['success_std'])} & {delta_success:+.3f} & "
            f"{fmt(row['collision_mean'], row['collision_std'])} & {delta_collision:+.3f} \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table*}", ""])
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)


def write_training_settings_table(out: Path) -> None:
    rows = [
        ("Parallel environments", "8", "All training runs"),
        ("Rollout length", "128 steps", "All training runs"),
        ("PPO epochs", "4", "All training runs"),
        ("Discount factor $\\gamma$", "0.99", "All training runs"),
        ("GAE $\\lambda$", "0.95", "All training runs"),
        ("Clip coefficient", "0.2", "All training runs"),
        ("Entropy coefficient", "0.01", "All training runs"),
        ("Value loss coefficient", "0.5", "All training runs"),
        ("Max gradient norm", "0.5", "All training runs"),
        ("Learning rate", "$3\\times10^{-4}$", "Default training; staged fine-tuning may use a lower value"),
        ("Hidden dimension", "128", "Actor, critic, and graph encoders"),
        ("Role embedding dimension", "8", "GAT-MAPPO and EA-RG-MAPPO-S"),
        ("Graph minibatch size", "256 graphs", "GAT-MAPPO and EA-RG-MAPPO-S"),
        ("MAPPO minibatch size", "512 samples", "MAPPO baseline"),
        ("Target policy", "mixed", "Final evaluation and robustness tests"),
        ("Target speed", "0.75", "Final main evaluation"),
        ("Training communication radius", "8", "Fixed-radius stage"),
        ("Staged fine-tuning radius", "$U(4,10)$", "EA-RG-MAPPO-S random-radius stage"),
        ("Final evaluation episodes", "300 per seed", "Main table"),
        ("Evaluation seeds", "3", "All reported mean$\\pm$std tables"),
        ("Python environment", "cac / Python 3.8.20", "Reported runtime"),
        ("PyTorch", "2.4.1+cu124", "Reported runtime"),
        ("GPU", "NVIDIA GTX 1650 Ti", "Reported runtime"),
    ]
    lines = [
        "\\begin{table*}[t]",
        "\\centering",
        "\\caption{Training and evaluation settings used in the reported experiments.}",
        "\\label{tab:training_settings}",
        "\\begin{tabularx}{\\textwidth}{lcl}",
        "\\toprule",
        "Item & Value & Scope \\\\",
        "\\midrule",
    ]
    for item, value, scope in rows:
        lines.append(f"{item} & {value} & {scope} \\\\")
    lines.extend(["\\bottomrule", "\\end{tabularx}", "\\end{table*}", ""])
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)


def main() -> None:
    paper_rows = load_rows(RESULTS / "paper_comm_results.csv")
    write_table(
        paper_rows,
        RESULTS / "latex_main_comm_table.tex",
        "Performance under different communication radii on the mixed-target pursuit task. Results are reported as mean$\\pm$std over three seeds.",
        "tab:comm_radius_results",
    )
    write_ablation_table(paper_rows, RESULTS / "latex_ablation_comm_table.tex")
    write_table(
        load_rows(RESULTS / "final_comm_300_summary.csv"),
        RESULTS / "latex_final_comm_300_table.tex",
        "Final 300-episode evaluation under different communication radii. Results are reported as mean$\\pm$std over three seeds.",
        "tab:final_comm_300_results",
    )
    write_speed_robustness_table(
        load_rows(RESULTS / "speed_robustness_summary.csv"),
        RESULTS / "latex_speed_robustness_table.tex",
    )
    write_edge_feature_ablation_table(
        load_rows(RESULTS / "edge_feature_ablation_summary.csv"),
        RESULTS / "latex_edge_feature_ablation_table.tex",
    )
    write_training_settings_table(RESULTS / "latex_training_settings_table.tex")


if __name__ == "__main__":
    main()
