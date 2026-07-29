from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev


def _float(row: dict[str, str], key: str, default: float = 0.0) -> float:
    value = row.get(key, "")
    if value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _read_episode_rows(summary_csv: Path) -> list[dict[str, str]]:
    root = summary_csv.resolve().parents[5]
    rows: list[dict[str, str]] = []
    with summary_csv.open("r", encoding="utf-8", newline="") as f:
        for summary in csv.DictReader(f):
            episode_csv = root / summary["file"]
            with episode_csv.open("r", encoding="utf-8", newline="") as ef:
                for row in csv.DictReader(ef):
                    row["summary_method"] = summary.get("method", "")
                    row["summary_graph"] = summary.get("graph", "")
                    row["summary_train_seed"] = summary.get("seed", "")
                    row["summary_update"] = summary.get("update", "")
                    rows.append(row)
    return rows


def _delayed_recovery(row: dict[str, str], min_step: int) -> float:
    if _float(row, "post_failure_chain_recovered_after_loss") <= 0.0:
        return 0.0
    first_chain_step = _float(row, "post_failure_first_chain_step", -1.0)
    return float(first_chain_step >= min_step)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary-csv", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--min-recovery-steps", type=int, nargs="+", default=[60, 80, 100])
    args = parser.parse_args()

    rows = _read_episode_rows(args.summary_csv)
    episode_rows: list[dict[str, object]] = []
    for row in rows:
        item: dict[str, object] = {
            "train_seed": int(_float(row, "summary_train_seed")),
            "eval_seed": int(_float(row, "seed")),
            "method": row.get("summary_method", ""),
            "graph_encoder": row.get("summary_graph", ""),
            "checkpoint_update": row.get("summary_update", ""),
            "episode": int(_float(row, "episode")),
            "success": _float(row, "success"),
            "legacy_recovered": _float(row, "post_failure_chain_recovered"),
            "recovered_after_loss": _float(row, "post_failure_chain_recovered_after_loss"),
            "post_failure_first_chain_step": _float(row, "post_failure_first_chain_step", -1.0),
            "steps": _float(row, "steps"),
            "timeout": _float(row, "timeout"),
            "collision": _float(row, "collision"),
        }
        for min_step in args.min_recovery_steps:
            item[f"delayed_recovery_ge_{min_step}"] = _delayed_recovery(row, min_step)
        episode_rows.append(item)

    aggregate_rows: list[dict[str, object]] = []
    by_method_seed: dict[tuple[str, int], list[dict[str, object]]] = defaultdict(list)
    for row in episode_rows:
        by_method_seed[(str(row["method"]), int(row["train_seed"]))].append(row)

    seed_rows: list[dict[str, object]] = []
    for (method, seed), group in sorted(by_method_seed.items()):
        item: dict[str, object] = {
            "method": method,
            "train_seed": seed,
            "episodes": len(group),
            "success": mean(float(r["success"]) for r in group),
            "legacy_recovered": mean(float(r["legacy_recovered"]) for r in group),
            "recovered_after_loss": mean(float(r["recovered_after_loss"]) for r in group),
            "timeout": mean(float(r["timeout"]) for r in group),
            "collision": mean(float(r["collision"]) for r in group),
        }
        for min_step in args.min_recovery_steps:
            key = f"delayed_recovery_ge_{min_step}"
            item[key] = mean(float(r[key]) for r in group)
        seed_rows.append(item)

    by_method: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in seed_rows:
        by_method[str(row["method"])].append(row)

    for method, group in sorted(by_method.items()):
        item = {
            "method": method,
            "seeds": len(group),
            "success_mean": mean(float(r["success"]) for r in group),
            "legacy_recovered_mean": mean(float(r["legacy_recovered"]) for r in group),
            "recovered_after_loss_mean": mean(float(r["recovered_after_loss"]) for r in group),
            "timeout_mean": mean(float(r["timeout"]) for r in group),
            "collision_mean": mean(float(r["collision"]) for r in group),
        }
        if len(group) > 1:
            item["recovered_after_loss_std"] = stdev(float(r["recovered_after_loss"]) for r in group)
        else:
            item["recovered_after_loss_std"] = 0.0
        for min_step in args.min_recovery_steps:
            key = f"delayed_recovery_ge_{min_step}"
            item[f"{key}_mean"] = mean(float(r[key]) for r in group)
        aggregate_rows.append(item)

    _write_csv(args.out_dir / "strict_recovery_episode_metrics.csv", episode_rows)
    _write_csv(args.out_dir / "strict_recovery_seed_summary.csv", seed_rows)
    _write_csv(args.out_dir / "strict_recovery_aggregate_summary.csv", aggregate_rows)

    print(args.out_dir / "strict_recovery_episode_metrics.csv")
    print(args.out_dir / "strict_recovery_seed_summary.csv")
    print(args.out_dir / "strict_recovery_aggregate_summary.csv")


if __name__ == "__main__":
    main()
