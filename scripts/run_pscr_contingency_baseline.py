"""Run plain MAPPO on the frozen uncertainty-aware PSCR interface."""
from __future__ import annotations

import functools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms.pscr_contingency_mappo import PSCRContingencyMAPPO
from envs.pscr_adversarial_service_env import PSCRConfig
from envs.pscr_contingency_service_env import PSCRContingencyServiceEnv
from scripts import run_pscr_plain_baseline as base


PROTOCOL = "PSCR-CONTINGENCY-PLAIN-MAPPO-BASELINE-V1"
base.PSCRPlainMAPPO = PSCRContingencyMAPPO
base.PredictiveServiceChainReconfigurationEnv = PSCRContingencyServiceEnv
base.PSCRConfig = functools.partial(PSCRConfig, future_deadline_urgent_step=100)
base.PROTOCOL = PROTOCOL

train = base.train
evaluate = base.evaluate


if __name__ == "__main__":
    base.main()
