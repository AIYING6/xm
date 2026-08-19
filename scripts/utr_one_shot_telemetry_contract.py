"""Pure, import-safe constants for the one-shot UTR diagnostic contract."""
from collections import OrderedDict


PROTOCOL = "UTR-ONE-SHOT-MECHANISM-TELEMETRY-V1"
UTR_SEEDS = (2002, 2101, 2102, 2103, 2104)
EPISODES_PER_CONDITION = 50
EXPECTED_TAPE_HASH = "56adbdc2fda3faf14decd94b45cae9a0b6178760725a6fec391ad671e8a30b65"
SELECTED_CONDITIONS = OrderedDict((
    ("N", "nominal"),
    ("F0", "f0_seen_44_80"),
    ("timing_early", "timing_28_80"),
    ("timing_late", "timing_60_80"),
    ("duration_short", "duration_44_40"),
    ("duration_long", "duration_44_120"),
    ("compound", "compound_28_120"),
))
