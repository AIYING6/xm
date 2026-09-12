"""Run the capacity-matched MAPPO baseline on PSCR's service-intent interface."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms.pscr_service_mappo import PSCRServiceMAPPO
from envs.pscr_service_reconfiguration_env import PSCRServiceReconfigurationEnv
from scripts import run_pscr_plain_baseline as base


PROTOCOL = "PSCR-SERVICE-INTENT-PLAIN-MAPPO-BASELINE-V1"

# Reuse the audited PPO, curriculum and endpoint evaluator.  Only the
# environment and action head differ, which makes this entry point a clean
# control-interface baseline rather than a second optimizer implementation.
base.PSCRPlainMAPPO = PSCRServiceMAPPO
base.PredictiveServiceChainReconfigurationEnv = PSCRServiceReconfigurationEnv
base.PROTOCOL = PROTOCOL

train = base.train
evaluate = base.evaluate


if __name__ == "__main__":
    base.main()
