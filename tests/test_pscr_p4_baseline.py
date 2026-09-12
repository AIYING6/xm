from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.pscr_contingency_service_env import PSCRContingencyServiceEnv
from scripts.run_pscr_p4_baseline import P4_CONFIG, train


def main() -> None:
    values = {PSCRContingencyServiceEnv(P4_CONFIG(seed=seed)).public_forecast_reliability for seed in range(1, 20)}
    assert values == {0.25, 0.90}
    root = Path(tempfile.mkdtemp(prefix="pscr_p4_baseline_smoke_"))
    try:
        train(seed=99701, updates=1, parallel_envs=2, output=root)
        assert (root / "endpoint.pt").is_file()
    finally:
        shutil.rmtree(root)
    print("PSCR_P4_BASELINE_SMOKE_PASS")


if __name__ == "__main__":
    main()
