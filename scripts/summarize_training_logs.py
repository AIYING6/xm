"""Summarize and sanity-check paper training logs."""

from __future__ import annotations

import argparse
import csv
import math
from io import StringIO
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN_ROOT = ROOT / "results" / "paper_config_runs"
DEFAULT_METHODS = ("mappo", "single_graph", "ea_rg_mappo", "happo")
ALLOWED_NAN_COLUMNS = {"eval_intent_acc"}


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    text = path.read_bytes().replace(b"\x00", b"").decode("utf-8", errors="replace")
    lines = text.splitlines()
    if text and not text.endswith(("\n", "\r")):
        lines = lines[:-1]
    if len(lines) < 2:
        return []
    return list(csv.DictReader(StringIO("\n".join(lines))))


def as_float(value: str) -> float | None:
    if value in {"", None}:  # type: ignore[comparison-overlap]
        return None
    try:
        return float(value)
    except ValueError:
        return None


def summarize_rows(rows: list[dict[str, str]], *, allowed_nan_columns: set[str]) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    if not rows:
        return {}, ["empty or missing log"]
    last = rows[-1]
    update = int(float(last.get("update", "0") or 0))
    train_rewards = [as_float(row.get("train_avg_reward", "")) for row in rows]
    train_rewards = [value for value in train_rewards if value is not None and math.isfinite(value)]
    eval_rows = [row for row in rows if row.get("eval_success_rate", "") != ""]
    last_eval = eval_rows[-1] if eval_rows else {}

    for row_idx, row in enumerate(rows, start=1):
        for key, value in row.items():
            parsed = as_float(value)
            if value == "" or parsed is None:
                continue
            if not math.isfinite(parsed) and key not in allowed_nan_columns:
                errors.append(f"non-finite value row={row_idx} col={key} value={value}")
                if len(errors) > 20:
                    break
        if len(errors) > 20:
            break

    summary = {
        "update": str(update),
        "rows": str(len(rows)),
        "last_train_avg_reward": last.get("train_avg_reward", ""),
        "mean_train_avg_reward_last_20": (
            f"{sum(train_rewards[-20:]) / len(train_rewards[-20:]):.6g}" if train_rewards[-20:] else ""
        ),
        "last_eval_update": last_eval.get("update", ""),
        "last_eval_success_rate": last_eval.get("eval_success_rate", ""),
        "last_eval_timeout_rate": last_eval.get("eval_timeout_rate", ""),
        "last_eval_avg_distance": last_eval.get("eval_avg_distance", ""),
        "loss": last.get("loss", ""),
        "value_loss": last.get("value_loss", ""),
        "entropy": last.get("entropy", ""),
    }
    return summary, errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True)
    parser.add_argument("--methods", nargs="+", default=DEFAULT_METHODS)
    parser.add_argument("--seeds", nargs="+", type=int, default=(0,))
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--out-csv", type=Path, default=None)
    args = parser.parse_args()

    rows_out: list[dict[str, str]] = []
    all_errors: list[str] = []
    for method in args.methods:
        for seed in args.seeds:
            log_path = args.run_root / args.mode / "runs" / method / f"bc_ppo_seed{seed}" / "train_log.csv"
            summary, errors = summarize_rows(read_rows(log_path), allowed_nan_columns=ALLOWED_NAN_COLUMNS)
            row = {"mode": args.mode, "method": method, "seed": str(seed), **summary}
            rows_out.append(row)
            if errors:
                all_errors.extend([f"{method} seed={seed}: {error}" for error in errors])
            print(row)

    if args.out_csv is not None:
        args.out_csv.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "mode",
            "method",
            "seed",
            "update",
            "rows",
            "last_train_avg_reward",
            "mean_train_avg_reward_last_20",
            "last_eval_update",
            "last_eval_success_rate",
            "last_eval_timeout_rate",
            "last_eval_avg_distance",
            "loss",
            "value_loss",
            "entropy",
        ]
        with args.out_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows_out)
        print(args.out_csv)

    if all_errors:
        for error in all_errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("training log summary passed")


if __name__ == "__main__":
    main()
