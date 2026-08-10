"""Create a zero-result F2 launch plan from frozen F1 artifacts only."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from f2_r2_common import build_f2_plan, write_new_json


def current_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--f1-root", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--expected-f1-source-commit", required=True)
    parser.add_argument("--expected-evaluator-source-commit", required=True)
    args = parser.parse_args()
    if current_commit() != args.expected_evaluator_source_commit:
        raise SystemExit("F2 evaluator source commit mismatch")
    if args.out_root.exists():
        raise SystemExit(f"refusing to reuse F2 output root: {args.out_root}")
    plan = build_f2_plan(args.f1_root, args.expected_f1_source_commit, args.expected_evaluator_source_commit)
    write_new_json(args.out_root / "F2_R2_LAUNCH_PREFLIGHT_MANIFEST.json", plan)
    print("F2_R2_LAUNCH_PREFLIGHT_PASS: 24 frozen checkpoints; confirmatory episodes not accessed")


if __name__ == "__main__":
    main()
