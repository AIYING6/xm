from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.run_pscr_predictive_mappo import train


def main() -> None:
    root = Path(tempfile.mkdtemp(prefix="pscr_predictive_smoke_"))
    try:
        train(seed=99101, updates=1, parallel_envs=2, output=root, curriculum=False)
        assert (root / "endpoint.pt").is_file()
    finally:
        shutil.rmtree(root)
    print("PSCR_PREDICTIVE_RUNNER_SMOKE_PASS")


if __name__ == "__main__":
    main()
