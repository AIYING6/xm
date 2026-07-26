"""Start one selected paper-manifest row as a background job."""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JOBS_CSV = ROOT / "results" / "paper_manifest_jobs_v2.csv"
DEFAULT_JOB_LOG_DIR = ROOT / "results" / "paper_manifest_job_logs"
DEFAULT_MANIFEST = ROOT / "results" / "paper_command_manifest.csv"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def append_job(row: dict[str, str], jobs_csv: Path) -> None:
    jobs_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "job_id",
        "pid",
        "row_index",
        "mode",
        "kind",
        "method",
        "seed",
        "status",
        "started_utc",
        "command",
        "stdout_log",
        "stderr_log",
    ]
    write_header = not jobs_csv.exists()
    with jobs_csv.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def find_manifest_row(manifest: Path, kind: str, method: str, seed: str, status: str) -> tuple[int, dict[str, str]]:
    with manifest.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    matches = [
        (idx, row)
        for idx, row in enumerate(rows)
        if row.get("kind") == kind
        and row.get("method") == method
        and row.get("seed") == seed
        and row.get("status") == status
    ]
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one manifest row, found {len(matches)}")
    return matches[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python-exe", default=sys.executable)
    parser.add_argument("--kind", required=True)
    parser.add_argument("--method", required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--status", default="ready")
    parser.add_argument("--jobs-csv", type=Path, default=DEFAULT_JOBS_CSV)
    parser.add_argument("--job-log-dir", type=Path, default=DEFAULT_JOB_LOG_DIR)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--skip-completed", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    row_index, manifest_row = find_manifest_row(args.manifest, args.kind, args.method, args.seed, args.status)
    mode = manifest_row.get("mode", "unknown")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    job_id = f"{stamp}_{mode}_{args.kind}_{args.method}_seed{args.seed}"
    args.job_log_dir.mkdir(parents=True, exist_ok=True)
    stdout_log = args.job_log_dir / f"{job_id}.stdout.txt"
    stderr_log = args.job_log_dir / f"{job_id}.stderr.txt"

    command = [
        args.python_exe,
        "-B",
        "scripts/run_paper_manifest.py",
        "--kind",
        args.kind,
        "--method",
        args.method,
        "--seed",
        args.seed,
        "--status",
        args.status,
        "--limit",
        "1",
        "--python-exe",
        args.python_exe,
    ]
    if args.skip_completed:
        command.append("--skip-completed")

    print(" ".join(command))
    if args.dry_run:
        return

    creationflags = 0
    if sys.platform.startswith("win"):
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    with stdout_log.open("w", encoding="utf-8") as out, stderr_log.open("w", encoding="utf-8") as err:
        proc = subprocess.Popen(
            command,
            cwd=ROOT,
            stdout=out,
            stderr=err,
            stdin=subprocess.DEVNULL,
            close_fds=True,
            creationflags=creationflags,
        )

    append_job(
        {
            "job_id": job_id,
            "pid": str(proc.pid),
            "row_index": str(row_index),
            "mode": mode,
            "kind": args.kind,
            "method": args.method,
            "seed": args.seed,
            "status": args.status,
            "started_utc": utc_now(),
            "command": " ".join(command),
            "stdout_log": str(stdout_log),
            "stderr_log": str(stderr_log),
        },
        args.jobs_csv,
    )
    print(f"started job_id={job_id} pid={proc.pid}")
    print(stdout_log)
    print(stderr_log)


if __name__ == "__main__":
    main()
