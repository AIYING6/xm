#!/usr/bin/env python3
"""P25 FEASIBILITY PROBE (zero training).

Before committing GPU time to the moving single-agent experiment, confirm the
task is still *solvable* under motion.  This is the exact lesson P19 round-1
taught us: a moving/closed-loop geometry can silently make the task infeasible
(or trivial) and waste a full training run.

Two reference policies are rolled out (no learning):
  arm C  = recomputed analytic cadence: each step derive the swing cost s from
           the CURRENT separation and leave for the target when cache age reaches
           (ttl - s).  This is the "uses the formula online" baseline.
  arm D  = best FIXED periodic schedule searched over a coarse grid (the P19/P20
           script-table baseline, which is what vanilla RL collapsed against).

Report: for each (agent_speed, target_speed) the mean score and the fraction of
episodes with >0, for both arms.  A good setting is solvable (>0) for both arms
and, crucially, arm C should beat arm D -- otherwise a fixed table is enough and
the motion adds nothing.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from envs.attitude_coupled_relay_env import (  # noqa: E402
    AttitudeCoupledRelayConfig,
    AttitudeCoupledRelayEnv,
    TURN_ACTIONS,
)


def _wrap(a: float) -> float:
    return (a + math.pi) % (2.0 * math.pi) - math.pi


def _turn_toward(heading: float, desired: float, turn: float) -> int:
    err = _wrap(desired - heading)
    if err > turn * 0.5:
        return 2
    if err < -turn * 0.5:
        return 0
    return 1


def _swing_cost_deg(sep_deg: float) -> int:
    # s = ceil((sep - (fov + link)) / turn); 110 is the fov+link slack in P22.
    return max(1, int(math.ceil(max(0.0, sep_deg - 110.0) / 5.0)))


def analytic_policy(env: AttitudeCoupledRelayEnv, phase: str, leave_age: int):
    """Closed-loop cadence that recomputes the schedule from the live geometry."""
    turn = env.turn
    sep_deg = math.degrees(env.separation)
    s = _swing_cost_deg(sep_deg)
    leave_age = max(1, min(env.ttl - 1, env.ttl - s))
    if phase == "target":
        desired = env.target_bearing
        if abs(_wrap(env.target_bearing - env.heading)) <= env.half_fov:
            phase = "relay"
    else:
        desired = env.relay_bearing
        if env.cache_age >= leave_age:
            phase = "target"
    return _turn_toward(env.heading, desired, turn), phase


def fixed_schedule_policy(env: AttitudeCoupledRelayEnv, t: int, P: int, duty: float, phase: int):
    turn = env.turn
    desired = env.relay_bearing if ((t + phase) % P) < int(P * duty) else env.target_bearing
    return _turn_toward(env.heading, desired, turn)


def run_arm(env: AttitudeCoupledRelayEnv, policy, n_ep: int):
    scores, frac = [], 0
    for _ in range(n_ep):
        obs, _, _ = env.reset()
        phase, t = "target", 0
        P = policy.get("P"); duty = policy.get("duty"); ph = policy.get("phase")
        total = 0.0
        while not env.done:
            if P is None:
                a, phase = analytic_policy(env, phase, 0)
            else:
                a = fixed_schedule_policy(env, t, P, duty, ph)
            obs, _, _, r, d, info = env.step(a)
            total += float(r[0])
            t += 1
        scores.append(total)
        frac += 1 if total > 0 else 0
    return float(np.mean(scores)), frac / n_ep


def main() -> None:
    base = AttitudeCoupledRelayConfig(seed=12345)
    sweeps = [
        (0.0, 0.0),
        (0.03, 0.0),
        (0.03, 0.02),
        (0.05, 0.03),
        (0.08, 0.05),
    ]
    n_ep = 200
    # coarse grid for the best-fixed-schedule search (arm D)
    grid = [(P, duty, ph) for P in (16, 20, 24, 30, 36, 40, 48)
            for duty in (0.3, 0.4, 0.5, 0.6, 0.7)
            for ph in range(0, 8)]

    print("ag_spd  tgt_spd | analytic(mean,>0) | best-fixed(mean,>0) | fixed P/duty/ph")
    for ag, tg in sweeps:
        cfg = AttitudeCoupledRelayConfig(
            seed=12345, agent_speed=ag, target_speed=tg, link_range=1.0e9
        )
        env = AttitudeCoupledRelayEnv(cfg)
        c_mean, c_frac = run_arm(env, {"kind": "analytic"}, n_ep)
        best = (0.0, 0.0, None)
        for (P, duty, ph) in grid:
            m, f = run_arm(env, {"P": P, "duty": duty, "phase": ph}, n_ep)
            if m > best[0]:
                best = (m, f, (P, duty, ph))
        b_mean, b_frac, b_params = best
        print(f"{ag:>6} {tg:>7} | {c_mean:>6.1f} {c_frac:>5.0%}  | "
              f"{b_mean:>6.1f} {b_frac:>5.0%}  | {b_params}")


if __name__ == "__main__":
    main()
