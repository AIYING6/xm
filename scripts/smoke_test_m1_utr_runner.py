"""One-update local integration smoke test for the M1 baseline runner."""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.run_m1_utr_pilot import train


def main() -> None:
    root = Path(tempfile.mkdtemp(prefix="m1_utr_runner_"))
    try:
        train(seed=1101, updates=1, parallel_envs=3, out=root)
        assert (root / "endpoint.pt").is_file()
        assert (root / "train_log.csv").is_file()
    finally:
        shutil.rmtree(root)
    print("M1_UTR_RUNNER_SMOKE_PASS")


if __name__ == "__main__":
    main()
