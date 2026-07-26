"""Run one resumable training chunk from the paper manifest."""

from __future__ import annotations

import argparse
import csv
import re
import shlex
import subprocess
import sys
from io import StringIO
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "results" / "paper_command_manifest.csv"


def load_manifest_row(manifest: Path, method: str, seed: str) -> dict[str, str]:
    with manifest.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    matches = [
        row
        for row in rows
        if row.get("kind") == "train"
        and row.get("method") == method
        and row.get("seed") == seed
        and row.get("status") == "ready"
    ]
    if len(matches) != 1:
        raise SystemExit(f"expected one training row for method={method} seed={seed}, found {len(matches)}")
    return matches[0]


def arg_value(args: list[str], flag: str) -> str | None:
    try:
        return args[args.index(flag) + 1]
    except (ValueError, IndexError):
        return None


def set_arg(args: list[str], flag: str, value: str) -> None:
    try:
        idx = args.index(flag)
    except ValueError:
        args.extend([flag, value])
        return
    args[idx + 1] = value


def ensure_flag(args: list[str], flag: str) -> None:
    if flag not in args:
        args.append(flag)


def snapshot_pattern(method: str) -> tuple[str, str]:
    if method == "happo":
        return "happo_latest.pt", r"happo_update_(\d+)\.pt"
    return "actor_critic_latest.pt", r"actor_critic_update_(\d+)\.pt"


def training_state_name(method: str) -> str:
    if method == "happo":
        return "happo_training_state_latest.pt"
    return "actor_critic_training_state_latest.pt"


def resume_checkpoint_path(run_dir: Path, method: str, latest_name: str) -> Path:
    state_path = run_dir / training_state_name(method)
    if state_path.exists():
        return state_path
    return run_dir / latest_name


def latest_checkpoint_update(run_dir: Path, method: str) -> int:
    _, pattern = snapshot_pattern(method)
    regex = re.compile(pattern)
    updates = []
    for path in run_dir.glob("*.pt"):
        match = regex.fullmatch(path.name)
        if match:
            updates.append(int(match.group(1)))
    return max(updates) if updates else 0


def read_log_rows(log_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not log_path.exists():
        return [], []
    text = log_path.read_bytes().replace(b"\x00", b"").decode("utf-8", errors="replace")
    lines = text.splitlines()
    if text and not text.endswith(("\n", "\r")):
        lines = lines[:-1]
    if not lines:
        return [], []
    reader = csv.DictReader(StringIO("\n".join(lines)))
    return list(reader.fieldnames or []), list(reader)


def trim_log_to_update(log_path: Path, max_update: int) -> None:
    fieldnames, rows = read_log_rows(log_path)
    if not fieldnames:
        return
    kept = [row for row in rows if int(float(row.get("update", "0") or 0)) <= max_update]
    with log_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept)
    print(f"trimmed {log_path} to update <= {max_update}; rows={len(kept)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--chunk-updates", type=int, default=200)
    parser.add_argument("--target-updates", type=int, default=3907)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--python-exe", default=sys.executable)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    row = load_manifest_row(args.manifest, args.method, args.seed)
    command = shlex.split(row["command"], posix=True)
    if command[0] == "python":
        command[0] = args.python_exe
    out_dir_arg = arg_value(command, "--out-dir")
    if out_dir_arg is None:
        raise SystemExit("manifest command missing --out-dir")
    run_dir = Path(out_dir_arg)
    if not run_dir.is_absolute():
        run_dir = ROOT / run_dir
    latest_name, _ = snapshot_pattern(args.method)
    resume_update = latest_checkpoint_update(run_dir, args.method)
    log_path = run_dir / "train_log.csv"
    if resume_update > 0:
        trim_log_to_update(log_path, resume_update)
    remaining = args.target_updates - resume_update
    if remaining <= 0:
        print(f"already complete at update {resume_update}")
        return
    chunk_updates = min(args.chunk_updates, remaining)
    set_arg(command, "--updates", str(chunk_updates))
    set_arg(command, "--update-offset", str(resume_update))
    if resume_update > 0:
        set_arg(command, "--resume", str(resume_checkpoint_path(run_dir, args.method, latest_name)))
        ensure_flag(command, "--append-log")

    print(f"resume_update={resume_update} chunk_updates={chunk_updates} target_updates={args.target_updates}")
    print(" ".join(command))
    if args.dry_run:
        return
    result = subprocess.run(command, cwd=ROOT, check=False)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
