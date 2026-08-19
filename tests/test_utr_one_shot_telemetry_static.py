from scripts.utr_one_shot_telemetry_contract import EPISODES_PER_CONDITION, SELECTED_CONDITIONS, UTR_SEEDS


def test_frozen_telemetry_selection_contract() -> None:
    assert tuple(SELECTED_CONDITIONS) == (
        "N", "F0", "timing_early", "timing_late", "duration_short", "duration_long", "compound"
    )
    assert tuple(UTR_SEEDS) == (2002, 2101, 2102, 2103, 2104)
    assert EPISODES_PER_CONDITION == 50
    assert len(UTR_SEEDS) * len(SELECTED_CONDITIONS) * EPISODES_PER_CONDITION == 1750
