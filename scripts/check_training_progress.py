"""Report training-log progress for paper runs."""

from __future__ import annotations

import argparse
import csv
import json
import time
from io import StringIO
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs" / "paper"
DEFAULT_RUN_ROOT = ROOT / "results" / "paper_config_runs"
DEFAULT_METHODS = ("mappo", "single_graph", "ea_rg_mappo", "happo")


def expected_updates(mode: str) -> int:
    if mode == "smoke":
        return 1
    if mode == "probe_20":
        return 20
    if mode in {"dev_1m", "formal_bstar"}:
        cfg = json.loads((CONFIG_DIR / "main_gate1.yaml").read_text(encoding="utf-8"))
        return int(cfg["rollout"]["updates_for_1m_steps"])
    raise ValueError(f"unsupported mode: {mode}")


def read_last_row(log_path: Path) -> dict[str, str] | None:
    if not log_path.exists():
        return None
    text = log_path.read_bytes().replace(b"\x00", b"").decode("utf-8", errors="replace")
    lines = text.splitlines()
    if len(lines) < 2:
        return None
    if text and not text.endswith(("\n", "\r")):
        lines = lines[:-1]
    if len(lines) < 2:
        return None
    rows = list(csv.DictReader(StringIO("\n".join(lines))))
    return rows[-1] if rows else None


def parse_update(row: dict[str, str] | None) -> int | None:
    if row is None:
        return None
    value = row.get("update") or row.get("updates")
    return int(float(value)) if value not in {None, ""} else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("smoke", "probe_20", "dev_1m", "formal_bstar"))
    parser.add_argument("--methods", nargs="+", default=DEFAULT_METHODS)
    parser.add_argument("--seeds", nargs="+", type=int, default=(0,))
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--active-window-sec", type=float, default=120.0)
    args = parser.parse_args()

    now = time.time()
    target_updates = expected_updates(args.mode)
    print(f"mode: {args.mode}")
    print(f"target_updates: {target_updates}")
    print(f"checked_utc: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    for method in args.methods:
        for seed in args.seeds:
            run_dir = args.run_root / args.mode / "runs" / method / f"bc_ppo_seed{seed}"
            log_path = run_dir / "train_log.csv"
            last_row = read_last_row(log_path)
            update = parse_update(last_row)
            if not log_path.exists():
                print(f"{method} seed={seed}: missing")
                continue
            stat = log_path.stat()
            age = now - stat.st_mtime
            elapsed = max(stat.st_mtime - stat.st_ctime, 1e-6)
            updates_per_hour = float(update or 0) / elapsed * 3600.0
            remaining = max(target_updates - float(update or 0), 0.0)
            eta_hours = remaining / updates_per_hour if updates_per_hour > 0 else float("inf")
            active = age <= args.active_window_sec and (update or 0) < target_updates
            complete = (update or 0) >= target_updates
            percent = 100.0 * float(update or 0) / float(target_updates)
            print(
                f"{method} seed={seed}: update={update} "
                f"progress={percent:.2f}% active={active} complete={complete} "
                f"log_age_sec={age:.1f} updates_per_hour={updates_per_hour:.1f} "
                f"eta_hours={eta_hours:.2f}"
            )


if __name__ == "__main__":
    main()
