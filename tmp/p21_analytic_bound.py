#!/usr/bin/env python3
"""Zero-training check: does the achievable frontier have a closed form?

For a single nose with radar half-FOV f and link half-angle l, both duties can be
served at the same heading only when separation <= f + l.  Above that the agent must
time-share.  A cycle is:

    refresh (1 step pointing at the target, resets the cache)
    swing   s steps to reach the link cone
    deliver T - s steps while the cache is still fresh (TTL = T)
    swing   s steps back

    duty cycle = (T - s) / (T + 1 + s),  s = max(1, ceil((sep - (f + l)) / omega))

The max(1, ...) term is the tangency penalty: at sep = f + l the two cones touch at a
single heading, so the agent still has to dither one step instead of parking.
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from p18_train_coupled_policy import oracle_dp  # noqa: E402

cfg = json.loads((ROOT / "configs" / "p18_attitude_coupled_learning_20260910.json").read_text(encoding="utf-8"))
e = cfg["environment"]
T = e["cache_ttl_steps"]
OMEGA = e["turn_limit_deg_per_step"]
SLACK = e["radar_half_fov_deg"] + e["link_half_angle_deg"]
H = e["horizon_steps"]


def swing_steps(sep: float) -> int:
    return max(1, int(math.ceil(max(0.0, sep - SLACK) / OMEGA)))


def closed_form(sep: float) -> float:
    """Two regimes.

    sep < fov + link: the two cones overlap over an interval, so the nose can PARK
    inside the overlap and score every step; the only loss is the travel time to
    reach it from the initial heading.
    sep >= fov + link: the cones only touch (or are disjoint), so parking is
    impossible and the nose must dither: refresh, swing out, deliver, swing back.
    """
    overlap_start = max(0.0, sep - e["link_half_angle_deg"])  # nearest heading serving both
    overlap_width = SLACK - sep
    if overlap_width >= OMEGA:                       # wide enough to park in
        travel = int(math.ceil(overlap_start / OMEGA))
        return float(H - travel)
    s = swing_steps(sep)                             # dithering regime
    if s >= T:
        return 0.0
    return H * (T - s) / (T + 1 + s)


grid = [0, 30, 60, 90, 100, 110, 120, 130, 140, 150, 180]
print(f"TTL={T} turn={OMEGA} deg/step  fov+link={SLACK} deg  horizon={H}")
print(f"{'sep':>5} {'swing':>6} {'closed_form':>12} {'oracle_dp':>10} {'ratio':>7}")
worst = 0.0
for sep in grid:
    cf = closed_form(sep)
    dp = float(oracle_dp(sep, cfg))
    r = cf / dp if dp > 0 else float("nan")
    if dp > 0:
        worst = max(worst, abs(1.0 - r))
    print(f"{sep:>5} {swing_steps(sep):>6} {cf:>12.1f} {dp:>10.0f} {r:>7.2f}")
print(f"\nmax relative deviation from the DP oracle: {100 * worst:.1f}%")
band = [110, 120, 130, 140]
print("band closed-form mean = %.2f   (learned base was 5.12 -> %.1f%% of the analytic frontier)"
      % (sum(closed_form(s) for s in band) / len(band),
         100 * 5.12 / (sum(closed_form(s) for s in band) / len(band))))
