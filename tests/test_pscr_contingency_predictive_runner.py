from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.run_pscr_contingency_predictive import configure
from scripts import run_pscr_predictive_mappo as predictive


def main() -> None:
    root = Path(tempfile.mkdtemp(prefix="pscr_contingency_predictive_smoke_"))
    try:
        configure("robust")
        predictive.train(seed=99501, updates=1, parallel_envs=2, output=root)
        assert (root / "endpoint.pt").is_file()
    finally:
        shutil.rmtree(root)
    print("PSCR_CONTINGENCY_PREDICTIVE_RUNNER_SMOKE_PASS")


if __name__ == "__main__":
    main()
