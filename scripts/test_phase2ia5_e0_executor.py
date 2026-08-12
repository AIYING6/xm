"""Non-performance unit checks for the Phase 2IA5 E0 executor."""
from __future__ import annotations

import tempfile
from pathlib import Path

from run_phase2ia5_e0_eligibility_validation import ARMS, SEEDS, episode_id, eligibility_trigger_step


def main() -> None:
    assert tuple(ARMS) == ("full_gate", "no_role_gate")
    assert SEEDS == (101, 202, 303)
    assert episode_id(101, 0) == 1_520_000
    assert episode_id(303, 99) == 3_540_099
    assert eligibility_trigger_step([False, True, True, True]) is None
    assert eligibility_trigger_step([True, True, True, True]) == 4
    assert eligibility_trigger_step([False, True, True, True, True]) == 5
    assert eligibility_trigger_step([False] * 216 + [True] * 4) == 220
    try:
        eligibility_trigger_step([True] * 5, hold_steps=3)
    except ValueError:
        pass
    else:
        raise AssertionError("hold length must be fixed at four")
    with tempfile.TemporaryDirectory() as tmp:
        assert not (Path(tmp) / "results").exists()
    print("PHASE2IA5_E0_EXECUTOR_UNIT_TEST=PASS")


if __name__ == "__main__":
    main()
