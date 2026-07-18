from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inventory fair source checkpoints for strict-sensing baselines.")
    parser.add_argument("--seeds", nargs="+", type=int, default=(0, 1, 2))
    parser.add_argument(
        "--single-root",
        type=Path,
        default=ROOT / "results" / "intercept_3d_node_failure_curriculum_pilot_seed0" / "runs" / "single",
    )
    parser.add_argument(
        "--multi-root",
        type=Path,
        default=ROOT / "results" / "intercept_3d_node_failure_curriculum_pilot_seed0" / "runs" / "multi_relation",
    )
    parser.add_argument(
        "--no-graph-root",
        type=Path,
        default=ROOT / "results" / "intercept_3d_no_graph_source" / "runs" / "no_graph",
    )
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=ROOT / "results" / "intercept_3d_fair_source_checkpoint_inventory.csv",
    )
    parser.add_argument(
        "--summary-md",
        type=Path,
        default=ROOT / "docs" / "intercept_3d_fair_source_checkpoint_inventory.md",
    )
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def root_for(args: argparse.Namespace, graph_encoder: str) -> Path:
    if graph_encoder == "no_graph":
        return args.no_graph_root
    if graph_encoder == "single":
        return args.single_root
    if graph_encoder == "multi_relation":
        return args.multi_root
    raise ValueError(graph_encoder)


def inventory(args: argparse.Namespace) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for graph_encoder in ("no_graph", "single", "multi_relation"):
        root = root_for(args, graph_encoder)
        for seed in args.seeds:
            run_dir = root / f"bc_ppo_seed{seed}"
            best = run_dir / "actor_critic_best.pt"
            latest = run_dir / "actor_critic_latest.pt"
            rows.append(
                {
                    "graph_encoder": graph_encoder,
                    "seed": str(seed),
                    "root": display_path(root),
                    "run_dir": display_path(run_dir),
                    "best_exists": str(best.exists()),
                    "latest_exists": str(latest.exists()),
                    "best_checkpoint": display_path(best),
                    "latest_checkpoint": display_path(latest),
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, str]]) -> None:
    lines = [
        "# 3DOF Fair Source Checkpoint Inventory",
        "",
        "This inventory documents which staged source checkpoints are available before strict-sensing fair baseline experiments.",
        "",
        "| Method | Seed | Best | Latest | Run directory |",
        "|---|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['graph_encoder']} | {row['seed']} | {row['best_exists']} | "
            f"{row['latest_exists']} | `{row['run_dir']}` |"
        )
    missing = [row for row in rows if row["best_exists"] != "True"]
    lines.extend(
        [
            "",
            "## Decision",
            "",
        ]
    )
    if missing:
        lines.append("Missing best checkpoints:")
        lines.append("")
        for row in missing:
            lines.append(f"- `{row['graph_encoder']}` seed `{row['seed']}`: `{row['best_checkpoint']}`")
    else:
        lines.append("All requested best checkpoints exist.")
    lines.extend(
        [
            "",
            "Use this file to justify whether existing `single` / `multi_relation` sources are reused and which `no_graph` sources still need training.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    rows = inventory(args)
    write_csv(args.out_csv, rows)
    write_markdown(args.summary_md, rows)
    print(args.out_csv)
    print(args.summary_md)


if __name__ == "__main__":
    main()
