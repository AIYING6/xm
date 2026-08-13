"""Read-only R2B business-grounded geometric operating-window map."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "development" / "phase_r2b_recoverability_map"


def main() -> None:
    target = np.asarray([10_000.0, 0.0], dtype=np.float64)
    scout_radar = 17_500.0
    terminal_range = 5_000.0
    r_sr, r_ra, r_sa = 9_500.0, 12_000.0, 8_500.0
    rows: list[dict] = []
    for scout_y in np.arange(-10_000.0, -1_999.0, 500.0):
        scout = np.asarray([-2_000.0, scout_y])
        for attacker_y in np.arange(2_000.0, 10_001.0, 500.0):
            attacker = np.asarray([-2_000.0, attacker_y])
            relay = 0.5 * (scout + attacker)
            d_sr = float(np.linalg.norm(scout - relay))
            d_ra = float(np.linalg.norm(relay - attacker))
            d_sa = float(np.linalg.norm(scout - attacker))
            d_st = float(np.linalg.norm(scout - target))
            d_at = float(np.linalg.norm(attacker - target))
            closing = (245.0 + 270.0)
            recovery_steps = max(0.0, d_sa - r_sa) / closing
            category = "disconnected"
            if d_sr <= r_sr and d_ra <= r_ra and d_sa > r_sa and d_at > terminal_range and d_st <= scout_radar:
                category = "relay_dependent_recoverable" if recovery_steps < 216 else "recovery_unreachable"
            elif d_sa <= r_sa or d_at <= terminal_range:
                category = "direct_bypass"
            rows.append({
                "scout_y": scout_y, "attacker_y": attacker_y, "relay_y": float(relay[1]),
                "d_sr": d_sr, "d_ra": d_ra, "d_sa": d_sa, "d_st": d_st, "d_at": d_at,
                "recovery_steps_optimistic": recovery_steps, "category": category,
            })
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "operating_window_map.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    counts = {}
    for row in rows: counts[row["category"]] = counts.get(row["category"], 0) + 1
    payload = {
        "protocol": "PHASE-R2B-BGW-V1",
        "artifact_class": "READ_ONLY_RECOVERABILITY_MAP",
        "canonical_data_used": False,
        "training_started": False,
        "grid_points": len(rows),
        "category_counts": counts,
        "map_pass": counts.get("relay_dependent_recoverable", 0) > 0,
    }
    (OUT / "manifest.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if not payload["map_pass"]: raise SystemExit(2)


if __name__ == "__main__": main()
