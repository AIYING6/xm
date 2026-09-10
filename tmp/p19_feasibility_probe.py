#!/usr/bin/env python3
"""Why is P19 scoring 0? Check whether the frozen geometry is even feasible.

An agent can only service two duties in one TTL window if the angular gap between
its two duty bearings can be slewed within cache_ttl_steps * turn_limit.
"""
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from envs.attitude_coupled_team_env import AttitudeCoupledTeamEnv, TeamCoupledConfig  # noqa: E402

TTL = 6
TURN_DEG = 15.0
BUDGET = TTL * TURN_DEG  # max slew inside one freshness window
N = 2000

env = AttitudeCoupledTeamEnv(TeamCoupledConfig(seed=0))
gaps = np.zeros((N, 3))
for k in range(N):
    env.seed(100000 + k)
    env.reset()
    d = env._duty_bearings()
    for i in range(3):
        gaps[k, i] = abs(math.degrees(env._wrap(d[i][1] - d[i][0])))

names = ["S (target vs R)", "R (S vs K)", "K (R vs target)"]
print(f"slew budget inside one TTL = {TTL} steps x {TURN_DEG} deg = {BUDGET} deg\n")
allok = np.ones(N, dtype=bool)
for i, nm in enumerate(names):
    ok = gaps[:, i] <= BUDGET
    allok &= ok
    print(f"{nm:16s} gap: min={gaps[:, i].min():6.1f} mean={gaps[:, i].mean():6.1f} "
          f"max={gaps[:, i].max():6.1f}   feasible={ok.mean() * 100:5.1f}%")
print(f"\nall three agents simultaneously feasible: {allok.mean() * 100:.1f}% of geometries")
