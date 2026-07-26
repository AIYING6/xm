"""Check background jobs launched by start_paper_manifest_job.py."""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JOBS_CSV = ROOT / "results" / "paper_manifest_jobs_v2.csv"
DEFAULT_STATUS_CSV = ROOT / "results" / "paper_manifest_run_status.csv"


def pid_running(pid: str) -> bool:
    if not pid:
        return False
    if sys.platform.startswith("win"):
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            check=False,
        )
        return pid in result.stdout
    try:
        os.kill(int(pid), 0)
    except OSError:
        return False
    return True


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs-csv", type=Path, default=DEFAULT_JOBS_CSV)
    parser.add_argument("--status-csv", type=Path, default=DEFAULT_STATUS_CSV)
    args = parser.parse_args()

    jobs = read_csv(args.jobs_csv)
    statuses = read_csv(args.status_csv)
    completed = {(row.get("mode"), row.get("kind"), row.get("method"), row.get("seed")): row for row in statuses}

    print(f"jobs: {len(jobs)}")
    print(f"status rows: {len(statuses)}")
    for job in jobs:
        running = pid_running(job.get("pid", ""))
        matching_statuses = [
            row
            for row in statuses
            if row.get("mode") == job.get("mode")
            and row.get("row_index") == job.get("row_index")
            if row.get("kind") == job.get("kind")
            and row.get("method") == job.get("method")
            and row.get("seed") == job.get("seed")
        ]
        last_status = matching_statuses[-1] if matching_statuses else {}
        outcome = last_status.get("outcome", "pending")
        duration = last_status.get("duration_sec", "")
        print(
            f"{job.get('job_id')} pid={job.get('pid')} running={running} "
            f"mode={job.get('mode')} row={job.get('row_index')} "
            f"kind={job.get('kind')} method={job.get('method')} seed={job.get('seed')} "
            f"outcome={outcome} duration_sec={duration}"
        )


if __name__ == "__main__":
    main()
