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


def row_key(row: dict) -> tuple[str, int, float, float]:
    return (
        row["method"],
        int(row["seed"]),
        float(row["radius"]),
        float(row["target_speed"]),
    )


def summarize(rows: list[dict]) -> list[dict]:
    summary = []
    methods = list(dict.fromkeys(row["method"] for row in rows))
    radii = sorted({float(row["radius"]) for row in rows})
    speeds = sorted({float(row["target_speed"]) for row in rows})
    for method in methods:
        for radius in radii:
            for speed in speeds:
                group = [
                    row
                    for row in rows
                    if row["method"] == method
                    and float(row["radius"]) == radius
                    and float(row["target_speed"]) == speed
                ]
                summary.append(
                    {
                        "method": method,
                        "episodes": group[0]["episodes"],
                        "radius": radius,
                        "target_speed": speed,
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


def write_notes(summary: list[dict], notes_md: Path) -> None:
    notes_md.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Target Speed Robustness Evaluation",
        "",
        "说明：该实验不重新训练模型，只改变 mixed target 的速度，用于评估不同目标机动强度下的泛化稳定性。该结果作为附录/稳健性证据，主表仍使用 300-episode communication-radius evaluation。",
        "",
        "| Method | Radius | Target speed | Success | Collision | Timeout | Avg steps |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            "| {method} | {radius:g} | {speed:.2f} | {succ:.3f} ± {succ_std:.3f} | {coll:.3f} ± {coll_std:.3f} | {tout:.3f} ± {tout_std:.3f} | {steps:.1f} ± {steps_std:.1f} |".format(
                method=row["method"],
                radius=float(row["radius"]),
                speed=float(row["target_speed"]),
                succ=float(row["success_mean"]),
                succ_std=float(row["success_std"]),
                coll=float(row["collision_mean"]),
                coll_std=float(row["collision_std"]),
                tout=float(row["timeout_mean"]),
                tout_std=float(row["timeout_std"]),
                steps=float(row["avg_steps_mean"]),
                steps_std=float(row["avg_steps_std"]),
            )
        )
    lines.extend(
        [
            "",
            "论文使用边界：",
            "",
            "```text",
            "可以写：在轻量速度泛化测试中，EA-RG-MAPPO-S 在有限通信半径下保持较低碰撞率，说明其稳定性不只来自单一 target_speed 设置。",
            "谨慎写：该实验是 100-episode 附录级评估，不替代 300-episode 主结果；更高速度下的性能变化应按具体数值描述。",
            "```",
            "",
        ]
    )
    notes_md.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate final methods under multiple target speeds.")
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--target-policy", default="mixed")
    parser.add_argument("--target-speeds", type=float, nargs="+", default=[0.60, 0.75, 0.90])
    parser.add_argument("--radii", type=float, nargs="+", default=[4.0, 8.0])
    parser.add_argument("--out-csv", type=Path, default=Path("results/speed_robustness_eval.csv"))
    parser.add_argument("--summary-csv", type=Path, default=Path("results/speed_robustness_summary.csv"))
    parser.add_argument("--notes-md", type=Path, default=Path("results/speed_robustness_notes.md"))
    parser.add_argument("--resume", action="store_true", help="Skip rows already present in --out-csv.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = read_existing_rows(args.out_csv) if args.resume else []
    completed = {row_key(row) for row in rows}
    for run in FINAL_RUNS:
        for radius in args.radii:
            for speed in args.target_speeds:
                key = (run["method"], int(run["seed"]), float(radius), float(speed))
                if key in completed:
                    print(f"skip existing: {key}", flush=True)
                    continue
                row = evaluate_run(run, args.episodes, radius, args.target_policy, speed)
                rows.append(row)
                completed.add(key)
                print(row, flush=True)
                write_rows(rows, args.out_csv)
    summary = summarize(rows)
    write_rows(summary, args.summary_csv)
    write_notes(summary, args.notes_md)
    print(f"saved: {args.out_csv}")
    print(f"saved: {args.summary_csv}")
    print(f"saved: {args.notes_md}")


if __name__ == "__main__":
    main()
