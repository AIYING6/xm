from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.run_pscr_plain_baseline import train


def main() -> None:
    root = Path(tempfile.mkdtemp(prefix="pscr_plain_smoke_"))
    try:
        train(seed=98101, updates=1, parallel_envs=2, output=root)
        assert (root / "endpoint.pt").is_file()
        assert (root / "train_log.csv").is_file()
    finally:
        shutil.rmtree(root)
    print("PSCR_PLAIN_BASELINE_SMOKE_PASS")


if __name__ == "__main__": main()
