"""Validate deterministic P41 v2 tape construction without preserving output."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.p41_v2_tapes import FAMILIES, make_tape, scenario_from_dict


def main() -> None:
    first = make_tape(951000, 24)
    second = make_tape(951000, 24)
    assert first == second
    assert len(first["episodes"]) == 24
    assert {row["family"] for row in first["episodes"]} == set(FAMILIES)
    for row in first["episodes"]:
        scenario = scenario_from_dict(row)
        assert scenario.forecast.site != scenario.known.site
    print("P41_V2_TAPE_SMOKE_PASS")


if __name__ == "__main__":
    main()
