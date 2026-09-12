"""Capacity-matched MAPPO baseline for frozen reliability-conditioned PSCR P4."""
from __future__ import annotations

import functools
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms.pscr_contingency_mappo import PSCRContingencyMAPPO
from envs.pscr_adversarial_service_env import PSCRConfig
from envs.pscr_contingency_service_env import PSCRContingencyServiceEnv
from scripts import run_pscr_plain_baseline as base


PROTOCOL = "PSCR-P4-RELIABILITY-CONDITIONED-PLAIN-MAPPO-G0"
P4_CONFIG = functools.partial(
    PSCRConfig,
    primary_forward_distance=4_500.0,
    future_forward_distance=12_000.0,
    future_lateral_distance=13_000.0,
    contingency_forward_distance=11_000.0,
    future_arrival_step=84,
    future_deadline_urgent_step=117,
    forecast_reliability_choices=(0.90, 0.25),
)
base.PSCRPlainMAPPO = PSCRContingencyMAPPO
base.PredictiveServiceChainReconfigurationEnv = PSCRContingencyServiceEnv
base.PSCRConfig = P4_CONFIG
base.PROTOCOL = PROTOCOL

train = base.train
evaluate = base.evaluate


def main() -> None:
    """Run a P4 arm with an explicit checkpoint protocol label.

    The default preserves the completed G0 protocol.  Later registered arms
    must pass their frozen protocol on the command line, so a checkpoint never
    inherits a development-stage identifier merely because it reuses this
    capacity-matched runner.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--run-protocol", default=PROTOCOL)
    known, remaining = parser.parse_known_args()
    base.PROTOCOL = known.run_protocol
    sys.argv = [sys.argv[0], *remaining]
    base.main()


if __name__ == "__main__":
    main()
