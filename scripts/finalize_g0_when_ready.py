"""Detached post-processing watcher for the already-running G0 evaluation."""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "artifacts/g0/g0_episode_results.csv"
LOG = ROOT / "artifacts/g0/g0_postprocess.log"
PYTHON = Path(r"D:/Anaconda/envs/.conda/envs/cac/python.exe")


def main() -> None:
    with LOG.open("a", encoding="utf-8") as log:
        log.write("watcher started\n")
        log.flush()
        while not RAW.exists():
            time.sleep(30)
        commands = [
            [str(PYTHON), "scripts/aggregate_g0_zero_shot.py"],
            [str(PYTHON), "scripts/plot_g0_figures.py"],
            [str(PYTHON), "scripts/write_g0_reports.py"],
        ]
        for command in commands:
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            log.write(f"$ {' '.join(command)}\n{result.stdout}{result.stderr}\n")
            log.flush()
            if result.returncode != 0:
                raise SystemExit(result.returncode)
        log.write("G0 post-processing complete\n")


if __name__ == "__main__":
    main()
