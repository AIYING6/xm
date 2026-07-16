from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "checkpoint_inventory.md"


@dataclass(frozen=True)
class RunSpec:
    method: str
    seed: int
    run_dir: str


RUNS = [
    RunSpec("MAPPO", 0, "results/mappo_curriculum_slow_150"),
    RunSpec("MAPPO", 1, "results/mappo_curriculum_slow_seed1_150"),
    RunSpec("MAPPO", 2, "results/mappo_curriculum_slow_seed2_150"),
    RunSpec("GAT-MAPPO", 0, "results/gat_mappo_hybrid_slow_60_plus90"),
    RunSpec("GAT-MAPPO", 1, "results/gat_mappo_hybrid_slow_seed1_60_plus90"),
    RunSpec("GAT-MAPPO", 2, "results/gat_mappo_hybrid_slow_seed2_60_plus90"),
    RunSpec("EA-RG-MAPPO-S", 0, "results/ri_gmappo_edge_stage2_rand_seed0_20"),
    RunSpec("EA-RG-MAPPO-S", 1, "results/ri_gmappo_edge_stage2_rand_seed1_20"),
    RunSpec("EA-RG-MAPPO-S", 2, "results/ri_gmappo_edge_stage2_rand_seed2_20"),
]


def load_log(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def last_eval_row(rows: list[dict[str, str]]) -> dict[str, str] | None:
    for row in reversed(rows):
        if row.get("eval_success_rate", "") != "":
            return row
    return None


def fmt_float(value: str, digits: int = 3) -> str:
    if value == "":
        return "-"
    try:
        return f"{float(value):.{digits}f}"
    except ValueError:
        return value


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Checkpoint Inventory",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Map paper methods and seeds to concrete checkpoint directories and training logs.",
        "This report is generated from existing files only; it does not train or evaluate policies.",
        "```",
        "",
        "| Method | Seed | Directory | Checkpoint | Log rows | Last eval success | Last eval collision | Last eval steps |",
        "|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for spec in RUNS:
        run_dir = ROOT / spec.run_dir
        checkpoint = run_dir / "actor_critic_latest.pt"
        log_rows = load_log(run_dir / "train_log.csv")
        eval_row = last_eval_row(log_rows)
        if eval_row is None:
            success = collision = steps = "-"
        else:
            success = fmt_float(eval_row.get("eval_success_rate", ""))
            collision = fmt_float(eval_row.get("eval_collision_rate", ""))
            steps = fmt_float(eval_row.get("eval_avg_steps", ""), digits=1)
        ckpt_status = "yes" if checkpoint.exists() and checkpoint.stat().st_size > 0 else "no"
        lines.append(
            f"| {spec.method} | {spec.seed} | `{spec.run_dir}` | {ckpt_status} | "
            f"{len(log_rows)} | {success} | {collision} | {steps} |"
        )
    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            "```text",
            "The final paper evaluation uses these checkpoints and re-evaluates them with 300 episodes per seed.",
            "Training-log last evaluation rows are provided only as a run sanity check, not as final paper results.",
            "```",
            "",
        ]
    )
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
