"""Run selected rows from the paper command manifest.

This is a lightweight execution ledger for long paper experiments. It does
not decide which experiments are valid; it only executes already generated
manifest rows and records command provenance, return codes, and log paths.
"""

from __future__ import annotations

import argparse
import csv
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "results" / "paper_command_manifest.csv"
DEFAULT_STATUS_CSV = REPO_ROOT / "results" / "paper_manifest_run_status.csv"
DEFAULT_LOG_DIR = REPO_ROOT / "results" / "paper_manifest_logs"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_csv_list(value: str | None) -> set[str] | None:
    if value is None or value.strip() == "":
        return None
    return {item.strip() for item in value.split(",") if item.strip()}


def load_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def split_command(command: str, python_exe: str) -> list[str]:
    args = shlex.split(command, posix=True)
    if not args:
        raise ValueError("empty command")
    if args[0] == "python":
        args[0] = python_exe
    return args


def row_matches(
    row: dict[str, str],
    *,
    kinds: set[str] | None,
    methods: set[str] | None,
    seeds: set[str] | None,
    statuses: set[str] | None,
) -> bool:
    if kinds is not None and row.get("kind", "") not in kinds:
        return False
    if methods is not None and row.get("method", "") not in methods:
        return False
    if seeds is not None and row.get("seed", "") not in seeds:
        return False
    if statuses is not None and row.get("status", "") not in statuses:
        return False
    return True


def read_completed_keys(status_csv: Path) -> set[tuple[str, str, str, str, str]]:
    if not status_csv.exists():
        return set()
    completed: set[tuple[str, str, str, str, str]] = set()
    with status_csv.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("outcome") == "completed":
                completed.add(
                    (
                        row.get("row_index", ""),
                        row.get("kind", ""),
                        row.get("mode", ""),
                        row.get("method", ""),
                        row.get("seed", ""),
                    )
                )
    return completed


def append_status(status_csv: Path, row: dict[str, str]) -> None:
    status_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "run_id",
        "row_index",
        "kind",
        "mode",
        "method",
        "seed",
        "manifest_status",
        "command",
        "started_utc",
        "finished_utc",
        "duration_sec",
        "return_code",
        "outcome",
        "stdout_log",
        "stderr_log",
    ]
    write_header = not status_csv.exists()
    with status_csv.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def run_row(
    *,
    row_index: int,
    row: dict[str, str],
    python_exe: str,
    log_dir: Path,
    status_csv: Path,
    timeout_sec: int | None,
    dry_run: bool,
) -> int:
    command = row.get("command", "").strip()
    if not command:
        raise ValueError(f"manifest row {row_index} has no command")
    args = split_command(command, python_exe)
    run_id = (
        f"{row.get('mode','unknown')}_{row_index:04d}_"
        f"{row.get('kind','unknown')}_{row.get('method','unknown')}_seed{row.get('seed','na')}"
    )
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout_log = log_dir / f"{run_id}.stdout.txt"
    stderr_log = log_dir / f"{run_id}.stderr.txt"

    print(f"[{utc_now()}] row={row_index} kind={row.get('kind')} method={row.get('method')} seed={row.get('seed')}")
    print(" ".join(args))
    if dry_run:
        return 0

    started = utc_now()
    t0 = time.time()
    with stdout_log.open("w", encoding="utf-8") as out, stderr_log.open("w", encoding="utf-8") as err:
        proc = subprocess.run(args, cwd=REPO_ROOT, stdout=out, stderr=err, timeout=timeout_sec, check=False)
    duration = time.time() - t0
    finished = utc_now()
    outcome = "completed" if proc.returncode == 0 else "failed"
    append_status(
        status_csv,
        {
            "run_id": run_id,
            "row_index": str(row_index),
            "kind": row.get("kind", ""),
            "mode": row.get("mode", ""),
            "method": row.get("method", ""),
            "seed": row.get("seed", ""),
            "manifest_status": row.get("status", ""),
            "command": command,
            "started_utc": started,
            "finished_utc": finished,
            "duration_sec": f"{duration:.3f}",
            "return_code": str(proc.returncode),
            "outcome": outcome,
            "stdout_log": str(stdout_log),
            "stderr_log": str(stderr_log),
        },
    )
    print(f"[{finished}] {outcome} return_code={proc.returncode} duration_sec={duration:.1f}")
    return proc.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--status-csv", type=Path, default=DEFAULT_STATUS_CSV)
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR)
    parser.add_argument("--python-exe", default=sys.executable)
    parser.add_argument("--kind", help="Comma-separated kind filter, e.g. train,validation_sweep")
    parser.add_argument("--method", help="Comma-separated method filter, e.g. mappo,ea_rg_mappo")
    parser.add_argument("--seed", help="Comma-separated seed filter, e.g. 0,1,2")
    parser.add_argument("--status", default="ready", help="Comma-separated manifest status filter")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--timeout-sec", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-completed", action="store_true")
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    kinds = parse_csv_list(args.kind)
    methods = parse_csv_list(args.method)
    seeds = parse_csv_list(args.seed)
    statuses = parse_csv_list(args.status)
    completed = read_completed_keys(args.status_csv) if args.skip_completed else set()

    selected: list[tuple[int, dict[str, str]]] = []
    for row_index, row in enumerate(manifest):
        if row_index < args.start_index:
            continue
        if not row_matches(row, kinds=kinds, methods=methods, seeds=seeds, statuses=statuses):
            continue
        key = (str(row_index), row.get("kind", ""), row.get("mode", ""), row.get("method", ""), row.get("seed", ""))
        if key in completed:
            continue
        selected.append((row_index, row))
        if args.limit is not None and len(selected) >= args.limit:
            break

    print(f"selected rows: {len(selected)}")
    failures = 0
    for row_index, row in selected:
        rc = run_row(
            row_index=row_index,
            row=row,
            python_exe=args.python_exe,
            log_dir=args.log_dir,
            status_csv=args.status_csv,
            timeout_sec=args.timeout_sec,
            dry_run=args.dry_run,
        )
        if rc != 0:
            failures += 1
            break
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
