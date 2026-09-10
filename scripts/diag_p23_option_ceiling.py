#!/usr/bin/env python3
"""P23 DIAGNOSTIC (no training): is the P22 residual a GOAL-POINT defect or a TIMING defect?

P22 result: options band 17.08 vs oracle 26.25 (0.65x) vs primitives 4.25 (4.02x gain).
The residual has two candidate causes:

  (i)  GOAL POINT: the option aims at the duty centre instead of stopping at the edge of
       the feasible cone, so the swing costs more steps than necessary.
  (ii) TIMING: the swing itself is already minimal, but the policy starts it too late (or
       comes back too early), so fresh cache time is wasted.

This script settles it without training:
  1. builds the EXACT semi-MDP induced by the frozen P22 options (the controller is
     deterministic, so every option is a deterministic map (heading, age) -> trajectory);
  2. solves it by DP over remaining steps -> the OPTIONS CEILING, i.e. the best score
     attainable with these options and PERFECT timing;
  3. measures the effective swing length against the analytic minimum s = (sep-110)/turn;
  4. scores every fixed "leave when cache age >= A" cadence to show how sensitive the
     return is to departure timing.

Reading:
  ceiling ~= oracle        -> options themselves are not the limit, timing is  (ii)
  ceiling << oracle        -> the option definition (goal/termination) is the limit (i)
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from p18_train_coupled_policy import oracle_dp  # noqa: E402

CFG = ROOT / "configs" / "p22_swing_option_20260911.json"
FOCUS = [110, 120, 130, 140]


def wrap(a: float) -> float:
    return (a + math.pi) % (2.0 * math.pi) - math.pi


class SemiMDP:
    """Exact semi-MDP of the frozen P22 options for one separation."""

    def __init__(self, sep_deg: float, e: dict, max_option_steps: int):
        self.turn = math.radians(e["turn_limit_deg_per_step"])
        self.n = int(round(2 * math.pi / self.turn))          # 72 headings on the 5 deg grid
        self.ttl = e["cache_ttl_steps"]
        self.horizon = e["horizon_steps"]
        self.maxdur = max_option_steps
        self.fov = math.radians(e["radar_half_fov_deg"])
        self.link = math.radians(e["link_half_angle_deg"])
        self.sep = math.radians(sep_deg)
        self.relay_idx = int(round(sep_deg / e["turn_limit_deg_per_step"])) % self.n
        # (heading, age, option) -> list of (reward, heading', age') per primitive step
        self.traj = {}

    def _ang(self, i: int) -> float:
        return i * self.turn

    def goal_met(self, h: int, option: int) -> bool:
        if option == 0:
            return abs(wrap(0.0 - self._ang(h))) <= self.fov
        return abs(wrap(self.sep - self._ang(h))) <= self.link

    def run_option(self, h: int, age: int, option: int, dwell: bool = False):
        """Deterministic execution; returns per-step list of (reward, h', age').

        dwell=False reproduces the frozen P22 controller exactly: the option always
        executes at least one primitive step toward the goal CENTRE, even when the
        goal is already satisfied, so dwelling at the cone edge is impossible.
        dwell=True is the candidate fix: if the goal is already met, hold for one step.
        """
        key = (h, age, option, dwell)
        if key in self.traj:
            return self.traj[key]
        goal_idx = 0 if option == 0 else self.relay_idx
        hh, aa, steps = h, age, []
        for _ in range(self.maxdur):
            if dwell and not steps and self.goal_met(hh, option):
                delta = 0                      # hold in place, do not drift to the centre
            else:
                err = wrap(self._ang(goal_idx) - self._ang(hh))
                delta = 1 if err > self.turn * 0.5 else (-1 if err < -self.turn * 0.5 else 0)
            hh = (hh + delta) % self.n
            if abs(wrap(0.0 - self._ang(hh))) <= self.fov:       # target visible -> refresh
                aa = 0
            else:
                aa = min(aa + 1, self.ttl + 1)
            link_up = abs(wrap(self.sep - self._ang(hh))) <= self.link
            steps.append((1.0 if (aa <= self.ttl and link_up) else 0.0, hh, aa))
            if self.goal_met(hh, option):
                break
        self.traj[key] = steps
        return steps

    def ceiling(self, dwell: bool = False) -> float:
        """DP over REMAINING PRIMITIVE steps; state = (heading, age).

        Iterating a fixed number of times is wrong (an option may consume up to
        max_option_steps primitive steps per decision), so the value table is indexed
        by the number of primitive steps actually left.
        """
        A, N, H = self.ttl + 2, self.n, self.horizon
        V = [np.zeros((N, A)) for _ in range(H + 1)]
        for k in range(1, H + 1):
            NV = np.zeros((N, A))
            for h in range(N):
                for a in range(A):
                    best = 0.0
                    for o in (0, 1):
                        steps = self.run_option(h, a, o, dwell)
                        take = min(len(steps), k)
                        acc = sum(s[0] for s in steps[:take])
                        dur = len(steps)
                        cont = V[k - dur][steps[-1][1], steps[-1][2]] if dur < k else 0.0
                        best = max(best, acc + cont)
                    NV[h, a] = best
            V[k] = NV
        return float(V[H][0, self.ttl + 1])       # start: heading 0, cache stale

    def swing_steps(self) -> int:
        """Steps of SERVE_RELAY starting from the target-cone edge nearest the relay."""
        edge = None
        for h in range(self.n):
            if abs(wrap(0.0 - self._ang(h))) <= self.fov:
                if edge is None or abs(wrap(self.sep - self._ang(h))) < abs(wrap(self.sep - self._ang(edge))):
                    edge = h
        return len(self.run_option(edge, 0, 1))

    def cadence_score(self, leave_age: int) -> float:
        """Fixed cadence: serve target, swing to relay, deliver until age >= leave_age."""
        h, age, delivered, t = 0, self.ttl + 1, 0, 0
        # initial: get to the target pose
        for r, h, age in self.run_option(h, age, 0):
            delivered += r
            t += 1
        while t < self.horizon:
            for r, h, age in self.run_option(h, age, 1):
                delivered += r
                t += 1
                if t >= self.horizon:
                    return float(delivered)
            # hold in the link cone by re-invoking SERVE_RELAY until it is time to leave
            while age < leave_age and t < self.horizon:
                for r, h, age in self.run_option(h, age, 1):
                    delivered += r
                    t += 1
                    if t >= self.horizon:
                        return float(delivered)
            if t >= self.horizon:
                break
            for r, h, age in self.run_option(h, age, 0):
                delivered += r
                t += 1
                if t >= self.horizon:
                    break
        return float(delivered)


def main() -> None:
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    e = cfg["environment"]
    maxdur = cfg["training"]["max_option_steps"]
    turn = e["turn_limit_deg_per_step"]
    slack = e["radar_half_fov_deg"] + e["link_half_angle_deg"]

    learned_opt = {110: 39.33, 120: 20.0, 130: 6.0, 140: 3.0}
    print("sep | swing | ceiling(frozen) | ceiling(+dwell) | oracle | closed_form | learned | frozen/oracle | dwell/oracle")
    rows = []
    for sep in FOCUS:
        m = SemiMDP(float(sep), e, maxdur)
        c_fix = m.ceiling(dwell=False)
        c_dwl = m.ceiling(dwell=True)
        orc = float(oracle_dp(sep, cfg))
        s_an = max(1, int(math.ceil(max(0.0, sep - slack) / turn)))
        s_eff = m.swing_steps()
        cf = 60 * (e["cache_ttl_steps"] - s_an) / (e["cache_ttl_steps"] + 1 + s_an)
        rows.append((sep, s_eff, s_an, c_fix, c_dwl, orc, cf, learned_opt[sep]))
        print(f"{sep:>3} | {s_eff:>2}/{s_an:<2} | {c_fix:>15.1f} | {c_dwl:>14.1f} | {orc:>6.0f} | "
              f"{cf:>11.1f} | {learned_opt[sep]:>7.1f} | {c_fix / orc:>12.2f} | {c_dwl / orc:>11.2f}")

    print("\n=== departure-timing sensitivity (fixed cadence: leave when cache age >= A) ===")
    print("sep | " + "".join(f"A={a:<4}" for a in range(4, 9)) + " | best A")
    for sep in FOCUS:
        m = SemiMDP(float(sep), e, maxdur)
        scores = {a: m.cadence_score(a) for a in range(4, 9)}
        best = max(scores, key=scores.get)
        print(f"{sep:>3} | " + "".join(f"{scores[a]:<6.0f}" for a in range(4, 9)) + f" | A={best}")

    r_fix = float(np.mean([r[3] / r[5] for r in rows]))
    r_dwl = float(np.mean([r[4] / r[5] for r in rows]))
    print(f"\nmean ceiling/oracle: frozen options = {r_fix:.2f}   with dwell fix = {r_dwl:.2f}")
    if r_fix >= 0.90:
        print("VERDICT: option set is NOT the binding constraint -> residual is TIMING (ii)")
    elif r_dwl >= 0.90 and r_dwl > r_fix + 0.10:
        print("VERDICT: the frozen controller cannot DWELL at the cone edge -> GOAL/TERMINATION defect (i);"
              "\n         adding a dwell-capable option closes most of the gap WITHOUT any new timing mechanism")
    else:
        print("VERDICT: both effects present -> dwell fix (i) plus timing structure (ii)")


if __name__ == "__main__":
    main()
