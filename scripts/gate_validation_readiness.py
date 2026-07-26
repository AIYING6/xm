"""Gate whether training outputs are ready for validation sweeps."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_python(args: list[str]) -> int:
    print(" ".join([sys.executable, *args]))
    result = subprocess.run([sys.executable, *args], cwd=ROOT, check=False)
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", default="dev_1m")
    parser.add_argument("--methods", nargs="+", required=True)
    parser.add_argument("--seeds", nargs="+", required=True)
    parser.add_argument("--summary-csv", default="results/dev1m_validation_readiness_training_summary.csv")
    args = parser.parse_args()

    audit_rc = run_python(
        [
            "scripts/audit_training_outputs.py",
            "--mode",
            args.mode,
            "--methods",
            *args.methods,
            "--seeds",
            *args.seeds,
        ]
    )
    summary_rc = run_python(
        [
            "scripts/summarize_training_logs.py",
            "--mode",
            args.mode,
            "--methods",
            *args.methods,
            "--seeds",
            *args.seeds,
            "--out-csv",
            args.summary_csv,
        ]
    )

    if audit_rc != 0 or summary_rc != 0:
        print("validation readiness gate failed")
        raise SystemExit(1)
    print("validation readiness gate passed")


if __name__ == "__main__":
    main()
