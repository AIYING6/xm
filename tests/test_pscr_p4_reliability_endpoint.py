from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.run_pscr_p4_reliability_endpoint import p4_config


def main() -> None:
    for reliability in (0.25, 0.90):
        env_config = p4_config(7, reliability)
        assert env_config.forecast_reliability_choices == (reliability,)
        assert env_config.primary_forward_distance == 4_500.0
        assert env_config.future_arrival_step == 84
    print("PSCR_P4_RELIABILITY_ENDPOINT_SMOKE_PASS")


if __name__ == "__main__":
    main()
