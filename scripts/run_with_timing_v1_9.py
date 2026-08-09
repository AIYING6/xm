"""Run one command and persist portable, immutable wall/CPU timing metadata."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import resource
except ImportError:  # pragma: no cover - Windows development hosts lack resource.
    resource = None  # type: ignore[assignment]


def usage_delta(before: Any, after: Any) -> dict[str, float | None]:
    if before is None or after is None:
        return {"user_cpu_seconds": None, "system_cpu_seconds": None, "max_rss_kib": None}
    return {
        "user_cpu_seconds": after.ru_utime - before.ru_utime,
        "system_cpu_seconds": after.ru_stime - before.ru_stime,
        "max_rss_kib": float(after.ru_maxrss),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite timing record: {args.output}")
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        raise ValueError("a command must follow --")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    before = resource.getrusage(resource.RUSAGE_CHILDREN) if resource is not None else None
    start = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    execution_error = None
    try:
        completed = subprocess.run(command, check=False)
        return_code = completed.returncode
    except OSError as exc:
        execution_error = f"{type(exc).__name__}: {exc}"
        return_code = 127
    elapsed = time.perf_counter() - start
    after = resource.getrusage(resource.RUSAGE_CHILDREN) if resource is not None else None
    record = {
        "protocol": "V1_9_PORTABLE_TIMING_V1",
        "started_at_utc": started_at,
        "command": command,
        "wall_seconds": elapsed,
        "return_code": return_code,
        "execution_error": execution_error,
        "resource_usage": usage_delta(before, after),
        "pid": os.getpid(),
    }
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
