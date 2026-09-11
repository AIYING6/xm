"""One-update integration smoke for the A0 plain MAPPO pilot."""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.run_a0_plain_mappo_pilot import train


def main() -> None:
    root = Path(tempfile.mkdtemp(prefix="a0_plain_mappo_"))
    try:
        train(seed=301, updates=1, parallel_envs=3, out=root, arm="oc")
        assert (root / "endpoint.pt").is_file()
        assert (root / "train_log.csv").is_file()
    finally:
        shutil.rmtree(root)
    print("A0_PLAIN_MAPPO_RUNNER_SMOKE_PASS")


if __name__ == "__main__":
    main()
