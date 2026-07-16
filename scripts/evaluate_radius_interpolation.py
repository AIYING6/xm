from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.evaluate_final_comm_300 import FINAL_RUNS, evaluate_run


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def std(values: list[float]) -> float:
    m = mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / len(values))


def write_rows(rows: list[dict], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def read_existing_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def row_key(row: dict) -> tuple[str, int, float]:
    return row["method"], int(row["seed"]), float(row["radius"])


def summarize(rows: list[dict]) -> list[dict]:
    summary = []
    methods = list(dict.fromkeys(row["method"] for row in rows))
    radii = sorted({float(row["radius"]) for row in rows})
    for method in methods:
        for radius in radii:
            group = [row for row in rows if row["method"] == method and float(row["radius"]) == radius]
            summary.append(
                {
                    "method": method,
                    "episodes": group[0]["episodes"],
                    "radius": radius,
                    "success_mean": mean([float(row["success_rate"]) for row in group]),
                    "success_std": std([float(row["success_rate"]) for row in group]),
                    "collision_mean": mean([float(row["collision_rate"]) for row in group]),
                    "collision_std": std([float(row["collision_rate"]) for row in group]),
                    "timeout_mean": mean([float(row["timeout_rate"]) for row in group]),
                    "timeout_std": std([float(row["timeout_rate"]) for row in group]),
                    "avg_steps_mean": mean([float(row["avg_steps"]) for row in group]),
                    "avg_steps_std": std([float(row["avg_steps"]) for row in group]),
                    "n": len(group),
                }
            )
    return summary


def fmt(mean_value: float, std_value: float) -> str:
    return f"{mean_value:.3f}$\\pm${std_value:.3f}"


def write_latex(summary: list[dict], out_tex: Path) -> None:
    episodes = int(summary[0]["episodes"]) if summary else 0
    lines = [
        "\\begin{table*}[t]",
        "\\centering",
        f"\\caption{{Communication-radius interpolation diagnostic at unseen radii. Results are reported as mean$\\pm$std over three seeds with {episodes} episodes per seed.}}",
        "\\label{tab:radius_interpolation}",
        "\\begin{tabular}{lccc}",
        "\\toprule",
        "Method & Radius & Success $\\uparrow$ & Collision $\\downarrow$ \\\\",
        "\\midrule",
    ]
    current = None
    for row in summary:
        if current is not None and row["method"] != current:
            lines.append("\\midrule")
        current = row["method"]
        lines.append(
            f"{row['method']} & {float(row['radius']):.0f} & "
            f"{fmt(float(row['success_mean']), float(row['success_std']))} & "
            f"{fmt(float(row['collision_mean']), float(row['collision_std']))} \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table*}", ""])
    out_tex.parent.mkdir(parents=True, exist_ok=True)
    out_tex.write_text("\n".join(lines), encoding="utf-8")


def write_notes(summary: list[dict], notes_md: Path) -> None:
    notes_md.parent.mkdir(parents=True, exist_ok=True)
    by_key = {(row["method"], float(row["radius"])): row for row in summary}
    lines = [
        "# Communication-Radius Interpolation Diagnostic",
        "",
        "Purpose:",
        "",
        "```text",
        "Evaluate fixed trained checkpoints at unseen communication radii 5, 7, and 9.",
        "This is a lightweight appendix diagnostic and does not replace the 300-episode main table at radii 4, 6, 8, and 10.",
        "```",
        "",
        "## Summary",
        "",
        "| Method | Radius | Success | Collision | Timeout |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            f"| {row['method']} | {float(row['radius']):.0f} | "
            f"{float(row['success_mean']):.3f} +/- {float(row['success_std']):.3f} | "
            f"{float(row['collision_mean']):.3f} +/- {float(row['collision_std']):.3f} | "
            f"{float(row['timeout_mean']):.3f} +/- {float(row['timeout_std']):.3f} |"
        )
    lines.extend(["", "## Key Checks", "", "```text"])
    for radius in sorted({float(row["radius"]) for row in summary}):
        ea = by_key[("EA-RG-MAPPO-S", radius)]
        mappo = by_key[("MAPPO", radius)]
        gat = by_key[("GAT-MAPPO", radius)]
        lines.append(
            f"radius={radius:.0f}: EA collision={float(ea['collision_mean']):.3f}, "
            f"MAPPO collision={float(mappo['collision_mean']):.3f}, "
            f"GAT collision={float(gat['collision_mean']):.3f}."
        )
    lines.extend(
        [
            "```",
            "",
            "Use boundary:",
            "",
            "```text",
            "Can write: unseen-radius diagnostics support the cross-radius stability trend.",
            "Do not write: this small-budget diagnostic replaces the final 300-episode main evaluation.",
            "```",
            "",
        ]
    )
    notes_md.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate final checkpoints at unseen communication radii.")
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--target-policy", type=str, default="mixed")
    parser.add_argument("--target-speed", type=float, default=0.75)
    parser.add_argument("--radii", type=float, nargs="+", default=[5.0, 7.0, 9.0])
    parser.add_argument("--out-csv", type=Path, default=Path("results/radius_interpolation_eval.csv"))
    parser.add_argument("--summary-csv", type=Path, default=Path("results/radius_interpolation_summary.csv"))
    parser.add_argument("--notes-md", type=Path, default=Path("results/radius_interpolation_notes.md"))
    parser.add_argument("--latex-table", type=Path, default=Path("results/latex_radius_interpolation_table.tex"))
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = read_existing_rows(args.out_csv) if args.resume else []
    completed = {row_key(row) for row in rows}
    for run in FINAL_RUNS:
        for radius in args.radii:
            key = (run["method"], int(run["seed"]), float(radius))
            if key in completed:
                print(f"skip existing: {key}", flush=True)
                continue
            row = evaluate_run(run, args.episodes, radius, args.target_policy, args.target_speed)
            rows.append(row)
            completed.add(key)
            print(row, flush=True)
            write_rows(rows, args.out_csv)
    summary = summarize(rows)
    write_rows(summary, args.summary_csv)
    write_latex(summary, args.latex_table)
    write_notes(summary, args.notes_md)
    print(f"saved: {args.out_csv}")
    print(f"saved: {args.summary_csv}")
    print(f"saved: {args.latex_table}")
    print(f"saved: {args.notes_md}")


if __name__ == "__main__":
    main()
