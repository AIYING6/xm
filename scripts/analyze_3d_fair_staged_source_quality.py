from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit source quality for the fair staged 3DOF baseline protocol."
    )
    parser.add_argument(
        "--result-dir",
        type=Path,
        default=ROOT / "results" / "intercept_3d_fair_staged_source_dev_seed0",
    )
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=ROOT / "results" / "intercept_3d_fair_staged_source_quality.csv",
    )
    parser.add_argument(
        "--summary-md",
        type=Path,
        default=ROOT / "docs" / "intercept_3d_fair_staged_source_quality.md",
    )
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def final_train_row(path: Path) -> dict[str, str] | None:
    rows = read_rows(path)
    return rows[-1] if rows else None


def graph_dirs(result_dir: Path) -> list[str]:
    roots = [
        result_dir / "stage2_nominal" / "runs",
        result_dir / "stage3_curriculum" / "runs",
        result_dir / "stage4_strict_smoke" / "runs",
    ]
    names: set[str] = set()
    for root in roots:
        if root.exists():
            names.update(path.name for path in root.iterdir() if path.is_dir())
    return sorted(names)


def stage_train_log(result_dir: Path, stage: str, graph_encoder: str, seed: int) -> Path:
    return result_dir / stage / "runs" / graph_encoder / f"bc_ppo_seed{seed}" / "train_log.csv"


def summarize_train_stage(result_dir: Path, stage: str, graph_encoder: str, seed: int) -> dict[str, str]:
    row = final_train_row(stage_train_log(result_dir, stage, graph_encoder, seed))
    base = {
        "stage": stage,
        "graph_encoder": graph_encoder,
        "seed": str(seed),
        "source": "train_log",
    }
    if row is None:
        return {
            **base,
            "available": "0",
            "update": "",
            "eval_success_rate": "",
            "eval_timeout_rate": "",
            "eval_avg_steps": "",
            "eval_avg_distance": "",
        }
    return {
        **base,
        "available": "1",
        "update": row.get("update", ""),
        "eval_success_rate": row.get("eval_success_rate", ""),
        "eval_timeout_rate": row.get("eval_timeout_rate", ""),
        "eval_avg_steps": row.get("eval_avg_steps", ""),
        "eval_avg_distance": row.get("eval_avg_distance", ""),
    }


def summarize_strict_selection(result_dir: Path, graph_encoder: str, seed: int) -> dict[str, str]:
    rows = read_rows(result_dir / "stage4_strict_smoke" / "checkpoint_sweep" / "validation_selected_checkpoints.csv")
    match = [
        row
        for row in rows
        if row.get("graph_encoder") == graph_encoder and int(row.get("train_seed", -1)) == seed
    ]
    base = {
        "stage": "stage4_strict_validation",
        "graph_encoder": graph_encoder,
        "seed": str(seed),
        "source": "validation_selected_checkpoints",
    }
    if not match:
        return {
            **base,
            "available": "0",
            "update": "",
            "eval_success_rate": "",
            "eval_timeout_rate": "",
            "eval_avg_steps": "",
            "eval_avg_distance": "",
        }
    row = match[0]
    success = row.get("success_mean", "")
    recovery = row.get("post_failure_chain_recovered_mean", "")
    return {
        **base,
        "available": "1",
        "update": row.get("selected_checkpoint_update", ""),
        "eval_success_rate": success,
        "eval_timeout_rate": "" if recovery == "" else str(1.0 - float(recovery)),
        "eval_avg_steps": row.get("post_failure_chain_recovery_steps_mean", ""),
        "eval_avg_distance": "",
    }


def discover_seeds(result_dir: Path, graph_encoder: str) -> list[int]:
    seeds: set[int] = set()
    for stage in ("stage2_nominal", "stage3_curriculum"):
        root = result_dir / stage / "runs" / graph_encoder
        if root.exists():
            for path in root.iterdir():
                if path.is_dir() and path.name.startswith("bc_ppo_seed"):
                    seeds.add(int(path.name.replace("bc_ppo_seed", "")))
    return sorted(seeds)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "stage",
        "graph_encoder",
        "seed",
        "source",
        "available",
        "update",
        "eval_success_rate",
        "eval_timeout_rate",
        "eval_avg_steps",
        "eval_avg_distance",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def pct(value: str) -> str:
    if value == "":
        return ""
    return f"{100.0 * float(value):.1f}%"


def write_markdown(path: Path, rows: list[dict[str, str]], result_dir: Path) -> None:
    lines = [
        "# Fair Staged Source Quality Audit",
        "",
        f"Result directory: `{result_dir.as_posix()}`",
        "",
        "| Stage | Method | Seed | Update | Success/Recovery | Timeout/Unrecovered | Avg steps/recovery steps |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["stage"],
                    row["graph_encoder"],
                    row["seed"],
                    row["update"],
                    pct(row["eval_success_rate"]),
                    pct(row["eval_timeout_rate"]),
                    row["eval_avg_steps"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation Rule",
            "",
            "- If `stage2_nominal` success is zero, do not interpret strict-sensing results; the source policy has not learned the base interception task.",
            "- If `stage2_nominal` succeeds but `stage3_curriculum` fails, tune topology/node-failure curriculum before strict fine-tuning.",
            "- If both source stages are nonzero but strict validation is zero, then tune strict-sensing fine-tuning or scenario difficulty.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    rows: list[dict[str, str]] = []
    for graph_encoder in graph_dirs(args.result_dir):
        for seed in discover_seeds(args.result_dir, graph_encoder):
            rows.append(summarize_train_stage(args.result_dir, "stage2_nominal", graph_encoder, seed))
            rows.append(summarize_train_stage(args.result_dir, "stage3_curriculum", graph_encoder, seed))
            rows.append(summarize_strict_selection(args.result_dir, graph_encoder, seed))
    write_csv(args.out_csv, rows)
    write_markdown(args.summary_md, rows, args.result_dir)
    print(args.out_csv)
    print(args.summary_md)


if __name__ == "__main__":
    main()
