#!/usr/bin/env python3
"""P20 pre-flight: does motion actually break the open-loop timetable?

G1 is the gate P19 failed (1.057x).  This probe runs ONLY the scripted periodic
schedule (no training, CPU only) under the frozen P20 motion settings and compares
against the same search run under P19's stationary settings.  If the scripted best
collapses under motion while the learned arm stays around 18-19, G1 becomes likely.
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import p19_train_team_coupled_policy as m  # noqa: E402

TRIALS = int(sys.argv[1]) if len(sys.argv) > 1 else 60
GEO = list(range(31000, 31040))


def run(tag: str, cfg_path: str):
    cfg = json.loads((ROOT / cfg_path).read_text(encoding="utf-8"))
    rng = np.random.default_rng(7)
    best = m.search_schedule(GEO, rng, trials=TRIALS, cfg=cfg)
    default = float(np.mean(m.eval_schedule(GEO, 8, 3, (0, 0, 0), cfg=cfg)))
    print(f"{tag:12s} scripted_best={best['mean']:6.2f}  (period={best['period']}, duty={best['duty']}, "
          f"phases={best['phases']})  default(8,3,0,0,0)={default:6.2f}")
    return best["mean"]


p19 = run("P19 static", "configs/p19_team_attitude_coupled_20260910.json")
p20 = run("P20 moving", "configs/p20_moving_team_attitude_coupled_20260910.json")
print(f"\nscripted timetable loses {100.0 * (1.0 - p20 / max(p19, 1e-9)):.1f}% when the geometry moves")
print(f"to pass G1 (1.20x) the learned P20 arm must reach >= {1.20 * p20:.2f}")
